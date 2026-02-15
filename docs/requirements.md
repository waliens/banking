# Banking App — Current State Requirements Document

This document captures the complete functional requirements of the banking application as extracted from the codebase. It serves as the foundation for the modernization/refactoring effort.

---

## 1. User Flows

### 1.1 Authentication
- Login with username/password, receive JWT access token (1h) + refresh token (30 days)
- Auto-refresh access token every 60 seconds if older than 30 minutes
- Logout clears tokens from localStorage
- Route guards: some pages require auth only, others require auth + selected profile

### 1.2 Core Workflow
The typical user journey is:

1. **Login**
2. **Select or create a profile** (account group)
3. **Upload transaction files** (Belfius CSV, ING CSV, MasterCard PDF)
4. **Review duplicates** detected during import
5. **Categorize transactions** (manually or accept ML suggestions)
6. **View dashboards** (income/expense charts, per-category breakdowns, tabular summaries)

### 1.3 Supporting Flows
- **Manage categories**: Create/edit/delete hierarchical category tree (name, color, icon, parent)
- **Manage accounts**: View details, edit initial balance, manage aliases, merge duplicate accounts
- **Create manual transactions**: For transactions not from bank imports
- **Manage users**: Create/edit user accounts (admin)
- **Manage ML models**: Trigger retraining, view model states

---

## 2. Data Model

### 2.1 User
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| username | String(255) | Unique |
| password | String(255) | Hashed with werkzeug |

### 2.2 Account
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| number | String(63) | |
| name | String(255) | |
| initial | Numeric(20,2) | Starting balance |
| id_currency | Integer FK → Currency | |

- Unique constraint on (number, name)
- Computed hybrid properties: `balance_pos`, `balance_neg`, `balance` (excludes duplicates)
- Has many aliases, can be source or dest of transactions

### 2.3 AccountAlias
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| number | String(63) | Alternate account number |
| name | String(255) | Alternate account name |
| id_account | Integer FK → Account | CASCADE on delete |

### 2.4 Transaction
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| custom_id | String(255) | Unique, external ID for dedup |
| id_source | Integer FK → Account | Nullable |
| id_dest | Integer FK → Account | Nullable |
| when | Date | Transaction date |
| amount | Numeric(20,2) | Always positive |
| id_currency | Integer FK → Currency | |
| id_category | Integer FK → Category | SET NULL on category delete |
| data_source | String | 'belfius', 'ing', 'mastercard', 'manual' |
| description | String | Extracted from metadata |
| metadata_ | JSON | Raw data from source |
| id_is_duplicate_of | Integer FK → Transaction | Self-ref, soft dedup |

- Amount is always stored positive; sign is determined by source/dest direction
- Negative input amounts cause source/dest swap
- Hybrid properties: `when_month`, `when_year`

### 2.5 Category
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String(255) | |
| id_parent | Integer FK → Category | Self-ref for hierarchy |
| color | String(255) | Hex code |
| icon | String | Icon name |

- Tree structure: root categories have null parent
- Deleting a category re-parents its children to its own parent and nullifies transaction assignments
- Category changes invalidate ML models

### 2.6 Group (Account Group / "Profile")
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| name | String(255) | |
| description | String(1024) | |

- Contains accounts via AccountGroup join table
- Contains transactions via TransactionGroup join table
- Called "Profile" in the UI

### 2.7 AccountGroup (join table)
| Column | Type | Notes |
|--------|------|-------|
| id_group | Integer FK → Group | Composite PK |
| id_account | Integer FK → Account | Composite PK |
| contribution_ratio | Float | 0 < ratio <= 1, default 1.0 |

### 2.8 TransactionGroup (join table)
| Column | Type | Notes |
|--------|------|-------|
| id_group | Integer FK → Group | Composite PK |
| id_transaction | Integer FK → Transaction | Composite PK |
| contribution_ratio | Float | Default 1.0 |

### 2.9 Currency
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| symbol | String(15) | e.g. $ |
| short_name | String(255) | ISO code, e.g. EUR |
| long_name | String(255) | Full name |

- Seeded from currencies.csv on first migration

### 2.10 MLModelFile
| Column | Type | Notes |
|--------|------|-------|
| id | Integer PK | |
| filename | String | UUID-based .pkl path |
| metadata_ | JSON | cv_score, best_params, class_level |
| state | Enum | INVALID, VALID, TRAINING, DELETED |

---

## 3. Business Rules

### 3.1 Duplicate Detection
- **Automatic (on import)**: Matches on exact (id_source, id_dest, when, amount) tuple
- **Two-phase**: checks existing DB first, then checks within the import batch (binary search)
- Duplicates are marked with `id_is_duplicate_of` pointing to the original — never deleted
- Duplicates are excluded from all balance calculations and statistics
- **Manual override**: User can mark/unmark duplicates via UI
- **Candidate search**: Finds potential duplicates within configurable day range (default 7 days)

### 3.2 Data Import

#### Belfius CSV
- 13-row header, semicolon delimiter, latin1 encoding
- Amount: comma decimal separator, sign determines direction
- Reference extracted from description via regex: `REF. : ([0-9A-Za-z]+)`
- Custom ID: `{when}/{valued}/{from}/{to}/{amount:.2f}/{ref}`

#### ING CSV
- 1-row header, semicolon delimiter, UTF-8 BOM
- Amount: dot as thousands separator, comma as decimal
- Zero amounts skipped (informational entries)
- Description priority: details > communication > empty
- Custom ID: `{when}/{valued}/{from}/{to}/{amount}/{stmt_nb}-{transac_nb}`

#### MasterCard PDF
- PDF → HTML via pdfminer → parsed with BeautifulSoup
- Rows extracted by Y-coordinate matching, columns by X-coordinate
- Handles foreign currency conversion data
- Custom ID includes: amount, account, closing/debit dates, index

#### Common Rules
- Amount always stored as absolute value
- Positive input = income (swap source/dest if needed)
- New accounts created automatically during import (default EUR currency)
- Imported transactions auto-linked to matching profiles

### 3.3 Account Management
- Account identification: (number, name) tuple
- Account deduplication uses UnionFind for transitive equivalence
- IBAN / non-IBAN Belgian format matching supported
- Merge operation: moves all aliases, transactions, and group memberships to representative; invalidates ML models
- Cannot merge accounts that have direct transactions between them

### 3.4 Category Hierarchy
- Tree structure with arbitrary depth
- Operations: `get_tags_descendants(id)` returns full subtree; `get_tags_at_level(level)` returns tags at specific depth
- Statistics can aggregate at any hierarchy level (transactions roll up to ancestor)
- Category changes invalidate ML models

### 3.5 ML Categorization
- **Algorithm**: ExtraTreesClassifier (500 estimators, single-threaded)
- **Minimum**: 50 labeled transactions required for training
- **Features**: TF-IDF on cleaned description + date components (year/month/day/weekday) + value date + one-hot encoded accounts + hour/minute from description + amount
- **Description cleaning**: removes bank references, IBANs, dates, times, card numbers, structured communications
- **Hyperparameter tuning**: GridSearchCV with 5-fold CV over min_samples_leaf and max_features
- **Category levels**: coarse (first-level ancestors) or fine (second-level ancestors)
- **Inference**: runs in separate process for memory cleanup; returns category + confidence probability
- **Invalidation**: models invalidated on category change or account merge; triggers async retraining

### 3.6 Statistics
- **Income vs Expense**: determined by contribution_ratio difference between source and dest accounts in a group
- **Per-category**: aggregated by category hierarchy level, filterable by date range, income/expense, specific category
- **Monthly breakdown**: same as per-category but bucketed by month
- All stats exclude duplicate transactions
- Stats scoped to a specific profile (account group)

### 3.7 Profile (Account Group) Logic
- Groups accounts with individual contribution ratios (for shared expense tracking)
- Transactions auto-attributed to groups when source OR dest account is in the group
- Manual link/unlink of transactions to groups
- "External only" filter: transactions crossing group boundary (one side in, one side out)

---

## 4. API Surface (42 endpoints)

### Authentication (3)
| Method | Path | Description |
|--------|------|-------------|
| POST | /login | Authenticate, returns JWT tokens |
| POST | /refresh | Refresh access token |
| GET | /user/current | Get authenticated user |

### Users (3)
| Method | Path | Description |
|--------|------|-------------|
| GET | /users | List all users |
| POST | /user | Create user |
| PUT | /user/:id | Update user |

### Transactions — Query (4)
| Method | Path | Description |
|--------|------|-------------|
| GET | /transactions | Paginated list with 15+ filter params |
| GET | /transactions/count | Count matching filters |
| GET | /transaction/:id | Get single transaction |
| GET | /account/:id/transactions | Transactions for specific account |

### Transactions — Modify (7)
| Method | Path | Description |
|--------|------|-------------|
| POST | /transaction | Create manual transaction |
| PUT | /transaction/:id | Edit manual transaction (only manual allowed) |
| DELETE | /transaction/:id | Delete manual transaction (only if not grouped) |
| PUT | /transactions/tag | Bulk set categories |
| PUT | /transaction/:id/category/:id | Set single category |
| GET | /transaction/:id/category/infer | ML category prediction |
| GET | /transaction/:id/account_groups | Get linked groups |

### Transactions — Duplicates (3)
| Method | Path | Description |
|--------|------|-------------|
| GET | /transaction/:id/duplicate_of/candidates | Find potential duplicates |
| PUT | /transaction/:id_dup/duplicate_of/:id_parent | Mark as duplicate |
| PUT/DELETE | /transaction/:id/duplicate_of | Unmark duplicate |

### Accounts (5)
| Method | Path | Description |
|--------|------|-------------|
| GET | /accounts | List all accounts |
| GET | /account/:id | Get single account |
| PUT | /account/:id | Update (initial balance, swap representative) |
| PUT | /account/merge | Merge two accounts |
| POST | /account/:id/alias | Add alias |

### Account Groups / Profiles (6)
| Method | Path | Description |
|--------|------|-------------|
| GET | /account/groups | List all groups |
| GET | /account_group/:id | Get single group |
| POST | /account_group | Create group |
| PUT | /account_group/:id | Update group |
| PUT | /account_group/:id/transactions | Link transactions |
| DELETE | /account_group/:id/transactions | Unlink transactions |

### Statistics (3)
| Method | Path | Description |
|--------|------|-------------|
| GET | /account_group/:id/stats/incomeexpense | Income vs expense by year/month |
| GET | /account_group/:id/stats/percategory | Category breakdown |
| GET | /account_group/:id/stats/percategorymonthly | Monthly category trends |

### Categories (4)
| Method | Path | Description |
|--------|------|-------------|
| GET | /categories | List all categories |
| POST | /category | Create category |
| PUT | /category/:id | Update category |
| DELETE | /category/:id | Delete (re-parents children, nullifies transactions) |

### Other (4)
| Method | Path | Description |
|--------|------|-------------|
| GET | /currencies | List currencies |
| GET | /models | List ML models |
| POST | /model/refresh | Trigger retraining |
| POST | /upload_files | Import bank files (format param) |

---

## 5. Frontend Pages & Features

### 5.1 Login Page (`/login`)
- Username/password form
- Redirects to `?next` param or dashboard after login

### 5.2 Profile Selection (`/group/select`)
- Dropdown of existing profiles
- Shows accounts in selected profile
- Create / Edit / Select actions
- Stores selection in localStorage

### 5.3 Create/Edit Profile (`/group/create`, `/group/edit/:id`)
- Name, description fields
- Account list with contribution ratios (0-1)
- Autocomplete account selector

### 5.4 Dashboard (`/dashboard`)
- Requires selected profile
- Shows profile name, account count, total balance (color-coded)
- 5 tabs:
  - Accounts table
  - Tabular summary (per-category table)
  - Income/Expense chart (monthly column chart, year selector)
  - Per-category chart (pie chart, month/year selector)
  - Per-category monthly chart (trend lines)
- Charts use Google Charts, lazy-rendered per tab

### 5.5 Upload Data (`/upload`)
- Format selector: Belfius CSV, ING CSV, MasterCard PDF
- File drag-drop or browse
- MasterCard: requires account selection + preview before import
- Preview shows predicted matches, duplicates (warning icon), new accounts
- Redirects to dashboard after success

### 5.6 Tag Transactions (`/transaction/tagging`)
- Requires selected profile
- Paginated transaction table with backend sorting
- Collapsible advanced filters: date range, accounts, category, amount range (log slider), text search, group link status
- Per-row actions: edit (manual only), link/unlink from profile, mark duplicate (modal), set category
- ML integration: shows predicted category with confidence %, button to accept
- Bulk actions: link all, unlink all, set all categories, validate page (batch save)
- Pagination: 5/10/25/50/100 items per page

### 5.7 View Account (`/account/:id`)
- Account header: number, name, balance, initial amount
- Aliases displayed as tags
- Transaction history (load more pattern, 50 at a time)

### 5.8 Edit Account (`/account/:id/edit`)
- Edit initial balance
- Manage aliases: add new, swap representative with alias
- Dual-table layout for representative vs aliases

### 5.9 Create/Edit Manual Transaction (`/transaction`, `/transaction/:id`)
- Fields: amount, currency, source account, dest account, date, category, description
- Optional: link to current profile on creation
- Only manual transactions can be edited/deleted

### 5.10 Duplicate Management (`/duplicates`)
- Table of transactions marked as duplicates
- Expandable detail rows with side-by-side comparison
- "Unduplicate" action

### 5.11 Merge Accounts (`/account/merge`)
- Select representative + alias accounts
- String matching strategies (longest common substring, etc.)
- Prev/Next navigation through match candidates with score
- Confirmation dialog (irreversible operation)

### 5.12 Edit Category Tree (`/category/tree`)
- Two-column: scrollable tree sidebar + detail form
- Tree with nested categories, inline "+" to add subcategory
- Edit: name, icon, parent (dropdown with breadcrumb), color (picker)
- Delete with confirmation (warns about children re-parenting)

### 5.13 ML Models (`/models`)
- Table of model files with state badges (valid/invalid/training/deleted)
- "Re-train" button triggers async training

### 5.14 Manage Users (`/users/manage`)
- Two-column: user list sidebar + edit form
- Create/edit username and password
- Password confirmation field

### 5.15 Help Page (`/help`)
- Static documentation covering all features

---

## 6. Frontend Architecture

### State Management (Vuex)
- `currentGroupId` / `currentGroup`: selected profile (persisted in localStorage)
- `currentUser`: authenticated user
- `initialized`: store hydration flag
- Actions: login, logout, token refresh, group selection

### API Client Layer
- Base `Model` class with CRUD operations (axios)
- Subclasses: User, Account, Group, Transaction, Category, Currency, MLModelFile
- Field mappers for type conversion (string → Date, string → currency)
- Auth header set automatically from localStorage token

### i18n
- English + French (detected from browser)
- CSV-based translation source, compiled to JSON
- Belgian banking terminology ("Profile" for account group)

---

## 7. User Feedback & Pain Points

### 7.1 Complexity & Simplification Needed
- **Overall UX is too complex** — flows need to be streamlined
- **AccountGroup ("Profile") concept is unintuitive** — needs rethinking. Users shouldn't have to select a profile every time they log in; the app should remember and default to their last/primary profile
- **Transaction model is too complex** — needs simplification
- **Multi-user**: still desired, but currently adds complexity without proportional value
- **UI feels outdated** — needs a modern look and feel

### 7.2 Broken / Unreliable Features
- **Login & token refresh is clunky** — hardcoded timeouts, not activity-based, silent failures
- **Account balances are sometimes incorrect** — bug in balance computation from transactions + initial balance
- **Duplicate detection is imperfect**:
  - Fails on cross-bank duplicates (same transaction reported in imports from two different banks, e.g. a transfer visible in both Belfius and ING exports)
  - Other edge cases cause false negatives
  - Duplicates are hard to find when you need to tag them

### 7.3 Missing Features

#### Reimbursement / Expense Splitting (HIGH PRIORITY)
When paying on behalf of someone (e.g. dinner with friends), the other person reimburses you later. Currently both transactions (the payment and the reimbursement) appear independently in reports, distorting actual spending. What should appear in stats is **only your share** of the expense.

This is very common with apps like **Tricount** and **Splitwise**. The app should:
- Allow linking a reimbursement to the original expense
- Compute and display only the user's actual share in statistics
- Support importing from Splitwise/Tricount (automated or manual) to help reconcile these

#### Mobile Experience
- **The app is not mobile-ready at all** — no responsive design
- **Transaction tagging is the most mobile-critical flow** — users want to tag from their phone
- A **swipe-inspired mobile tagger** (like Tinder-style card swiping for category assignment) could make tagging fast and enjoyable on mobile

### 7.4 Code-Level Issues (from codebase analysis)
1. **Missing error handling**: Several API calls have empty/missing `.catch()` handlers
2. **No confirmation for bulk actions**: "Link All", "Unlink All", "Validate Page" affect many rows without confirmation
3. **Missing loading states**: Login form stays clickable during submission, no spinners on save/delete
4. **Inconsistent feedback patterns**: Mix of toasts, dialog alerts, and silent operations
5. **No input validation**: Contribution ratio allows 0, no source != dest check
6. **No optimistic updates**: Actions refresh entire page instead of updating locally
7. **Incomplete currency handling**: Dashboard hides balance for mixed-currency profiles
8. **No client-side caching**: Categories, currencies, accounts fetched fresh every time
9. **No automated frontend tests**

---

## 8. Target Feature Set (Modernized App)

### Constraints
- Must run on low-resource hardware (small Synology NAS) as well as bigger machines
- Open Banking API not viable (banks refuse API access to individuals)
- Should remain self-hosted, Dockerized

### HIGH PRIORITY — Core Refactoring

#### Simplified Flows & Concepts
- **Rethink AccountGroup/Profile**: make it more intuitive; auto-select last used profile on login; streamline the concept for households (e.g. "50/50 split" rather than raw contribution_ratio)
- **Simplify transaction model**: reduce data model complexity inherited from Belfius format
- **Onboarding wizard**: guide new users through first setup (create profile → upload → categorize)
- **"Review inbox"**: surface uncategorized transactions as a to-do with badge count ("23 to review") instead of requiring users to navigate to tag page with filters

#### Smarter Duplicate Detection
- **Fuzzy matching**: configurable date tolerance, cross-bank awareness (transfer visible in both sender and receiver imports), description similarity
- **Fix balance computation bug**

#### Expense Splitting / Reimbursements
- **Expense groups**: link related transactions (original payment + reimbursement); stats show only net share
- **Auto-match reimbursements**: suggest links when incoming transfer roughly matches a recent outgoing payment
- **Splitwise/Tricount import**: manual or automated, to reconcile shared expenses

#### Modern Mobile-First UI
- **Responsive design throughout** — mobile-ready from the ground up
- **Swipe-based mobile tagger**: card UI showing one transaction at a time; swipe right to accept ML suggestion, left for category picker, up to skip
- **Quick-add expense**: floating action button for cash expenses with minimal fields
- **Modern look and feel**: replace outdated Buefy/Bulma

#### Auth Improvements
- **Fix login/token refresh**: proper session management, activity-based refresh, no silent failures
- **Remember profile selection** across sessions

### HIGH PRIORITY — New Features

#### Recurring Transaction Detection
- Auto-identify subscriptions and recurring payments from patterns (amount, frequency, merchant)
- Dedicated view to see all recurring expenses
- Alert when a recurring expense changes amount or stops appearing

#### Quick-Tag Rules
- User-defined rules: "All transactions containing DELHAIZE → Groceries"
- Apply retroactively to existing transactions and automatically to future imports
- Reduces ML dependency for obvious, rule-based categorization

#### Transaction Splitting
- Split a single transaction across multiple categories with sub-amounts (e.g. supermarket receipt = groceries + household)

#### Import Reconciliation View
- After each import, show summary: X new, Y duplicates skipped, Z needing review
- Instead of silently importing and redirecting

#### Analytics Improvements
- **Period comparison**: month-over-month, year-over-year side by side
- **Anomaly detection**: flag transactions with unusually high amounts for their category
- **Net worth tracking**: aggregate all account balances over time into a chart
- **"Where did my money go?" summary**: top categories, biggest expense, income vs spending delta, recurring costs total — as a dashboard card or monthly view

#### Batch Operations
- Select multiple transactions and apply category, mark as reviewed, or link to expense group in one action

### LOW PRIORITY — Nice to Have
- Budget targets per category (monthly/yearly limits with progress bars)
- Budget alerts (approaching/exceeding limits)
- Forecasting (project end-of-month balance from patterns)
- Receipt/note attachments on transactions
- Pending reimbursement ledger (who owes what)
- Dashboard widget customization
- Keyboard shortcuts (if non-intrusive)
- Push notifications
