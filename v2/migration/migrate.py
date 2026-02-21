"""Data migration script: copies data from v1 database to v2 database.

Usage examples:
    # Direct URLs (simplest)
    python migrate.py --v1-url postgresql://user:pass@host/db --v2-url postgresql://user:pass@host/db

    # Individual params for v1, docker service for v2
    python migrate.py \\
        --v1-host prod.example.com --v1-user banking --v1-password secret --v1-db banking \\
        --v2-docker-service db

    # Disambiguate if multiple compose projects run the same service name
    python migrate.py --v1-url postgresql://... --v2-docker-service db --v2-docker-project myproject

    # Dry run (reads v1, prints counts, does not commit to v2)
    python migrate.py --v1-url postgresql://... --v2-docker-service db --dry-run

The v1 database is never modified. Safe to re-run (truncates v2 tables first).
"""
import argparse
import json
import sys
from urllib.parse import quote_plus


# ---------------------------------------------------------------------------
# Connection parameter helpers
# ---------------------------------------------------------------------------

def _build_url(host: str, port: int, user: str, password: str, db: str) -> str:
    """Build a postgresql:// URL, percent-encoding the password."""
    encoded = quote_plus(password) if password else ""
    auth = f"{user}:{encoded}" if encoded else user
    return f"postgresql://{auth}@{host}:{port}/{db}"


def url_from_docker_service(service_name: str, project_name: str | None = None) -> str:
    """Discover a PostgreSQL connection URL from a running docker compose container.

    Reads POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB from the container
    environment and derives the host/port from the published port bindings.
    """
    try:
        import docker  # type: ignore[import-untyped]
    except ImportError:
        sys.exit(
            "Error: 'docker' package is required for --v2-docker-service. "
            "Install it with:  pip install docker"
        )

    client = docker.from_env()

    labels = [f"com.docker.compose.service={service_name}"]
    if project_name:
        labels.append(f"com.docker.compose.project={project_name}")

    containers = client.containers.list(filters={"label": labels})

    if not containers:
        hint = f" in project '{project_name}'" if project_name else ""
        sys.exit(
            f"Error: No running container found for docker compose service "
            f"'{service_name}'{hint}.\n"
            f"Make sure the service is running: docker compose ps"
        )

    if len(containers) > 1:
        names = [c.name for c in containers]
        sys.exit(
            f"Error: Multiple containers match service '{service_name}': {names}.\n"
            f"Use --v2-docker-project to select the right compose project."
        )

    container = containers[0]

    # Parse environment variables
    env: dict[str, str] = {}
    for entry in container.attrs["Config"]["Env"] or []:
        if "=" in entry:
            k, v = entry.split("=", 1)
            env[k] = v

    user = env.get("POSTGRES_USER", "postgres")
    password = env.get("POSTGRES_PASSWORD", "")
    db = env.get("POSTGRES_DB", user)

    # Determine host port from port bindings
    port_bindings: dict = container.attrs["NetworkSettings"]["Ports"]
    tcp_bindings = port_bindings.get("5432/tcp") or []
    if tcp_bindings:
        host_ip = tcp_bindings[0]["HostIp"] or "localhost"
        if host_ip in ("0.0.0.0", "::"):
            host_ip = "localhost"
        host_port = int(tcp_bindings[0]["HostPort"])
    else:
        host_ip = "localhost"
        host_port = 5432
        print(
            "  Warning: port 5432 is not published to the host. "
            "Falling back to localhost:5432."
        )

    print(f"  Docker container : {container.name}")
    print(f"  Resolved target  : postgresql://{user}:***@{host_ip}:{host_port}/{db}")

    return _build_url(host_ip, host_port, user, password, db)


def resolve_url(label: str, args, prefix: str, parser: argparse.ArgumentParser) -> str:
    """Return a connection URL for the given side (v1 or v2).

    Priority: explicit URL > docker service > individual host params.
    """
    url      = getattr(args, f"{prefix}_url", None)
    host     = getattr(args, f"{prefix}_host", None)
    port     = getattr(args, f"{prefix}_port", None) or 5432
    user     = getattr(args, f"{prefix}_user", None) or "postgres"
    password = getattr(args, f"{prefix}_password", None) or ""
    db       = getattr(args, f"{prefix}_db", None) or user
    service  = getattr(args, f"{prefix}_docker_service", None)
    project  = getattr(args, f"{prefix}_docker_project", None)

    if url:
        return url

    if service:
        print(f"\nDiscovering {label} connection via docker service '{service}'...")
        return url_from_docker_service(service, project)

    if host:
        return _build_url(host, port, user, password, db)

    parser.error(
        f"Specify {label} connection with --{prefix}-url, "
        f"--{prefix}-docker-service, or --{prefix}-host"
    )


# ---------------------------------------------------------------------------
# Core migration logic
# ---------------------------------------------------------------------------

def migrate(v1_url: str, v2_url: str, dry_run: bool = False) -> None:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    v1_engine = create_engine(v1_url)
    v2_engine = create_engine(v2_url)

    with Session(v1_engine) as v1, Session(v2_engine) as v2:

        def commit_or_dry(session: Session) -> None:
            if dry_run:
                session.rollback()
            else:
                session.commit()

        # ── 1. Clean v2 tables (in dependency order) ──────────────────────
        print("Cleaning v2 tables...")
        if not dry_run:
            for table in [
                "expense_split_reimbursement", "expense_split",
                "tag_rule", "recurring_pattern", "ml_model",
                "wallet_account", "wallet",
                "transaction", "account_alias", "account",
                "category", "currency", '"user"',
            ]:
                v2.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            v2.commit()
        else:
            print("  (dry-run: skipping truncate)")

        # ── 2. Currencies ──────────────────────────────────────────────────
        print("Migrating currencies...")
        currencies = v1.execute(
            text("SELECT id, symbol, short_name, long_name FROM currency")
        ).fetchall()
        for c in currencies:
            v2.execute(text(
                "INSERT INTO currency (id, symbol, short_name, long_name) "
                "VALUES (:id, :symbol, :short_name, :long_name)"
            ), {"id": c.id, "symbol": c.symbol, "short_name": c.short_name, "long_name": c.long_name})
        commit_or_dry(v2)
        print(f"  {len(currencies)} currencies")

        # ── 3. Users ───────────────────────────────────────────────────────
        print("Migrating users...")
        users = v1.execute(text('SELECT id, username, password FROM "user"')).fetchall()
        for u in users:
            v2.execute(text(
                'INSERT INTO "user" (id, username, password_hash) '
                "VALUES (:id, :username, :password_hash)"
            ), {"id": u.id, "username": u.username, "password_hash": u.password})
        commit_or_dry(v2)
        print(f"  {len(users)} users")

        # ── 4. Categories ──────────────────────────────────────────────────
        print("Migrating categories...")
        categories = v1.execute(
            text("SELECT id, name, id_parent, color, icon FROM category")
        ).fetchall()
        for c in categories:
            v2.execute(text(
                "INSERT INTO category (id, name, id_parent, color, icon, sort_order, is_income) "
                "VALUES (:id, :name, :id_parent, :color, :icon, 0, false)"
            ), {"id": c.id, "name": c.name, "id_parent": c.id_parent, "color": c.color, "icon": c.icon})
        commit_or_dry(v2)
        print(f"  {len(categories)} categories")

        # ── 5. Accounts ────────────────────────────────────────────────────
        print("Migrating accounts...")
        accounts = v1.execute(
            text("SELECT id, number, name, initial, id_currency FROM account")
        ).fetchall()

        # Infer institution name from transactions data_source column
        institutions: dict[int, str] = {}
        inst_rows = v1.execute(text(
            "SELECT DISTINCT COALESCE(id_source, id_dest) AS acc_id, data_source "
            "FROM transaction WHERE data_source IS NOT NULL"
        )).fetchall()
        for row in inst_rows:
            if row.acc_id is not None:
                institutions[row.acc_id] = row.data_source

        for a in accounts:
            v2.execute(text(
                "INSERT INTO account (id, number, name, initial_balance, id_currency, institution, is_active) "
                "VALUES (:id, :number, :name, :initial_balance, :id_currency, :institution, true)"
            ), {
                "id": a.id, "number": a.number, "name": a.name,
                "initial_balance": a.initial or 0, "id_currency": a.id_currency,
                "institution": institutions.get(a.id),
            })
        commit_or_dry(v2)
        print(f"  {len(accounts)} accounts")

        # ── 6. Account aliases ─────────────────────────────────────────────
        print("Migrating account aliases...")
        aliases = v1.execute(
            text("SELECT id, number, name, id_account FROM account_alias WHERE id_account IS NOT NULL")
        ).fetchall()
        skipped_aliases = v1.execute(
            text("SELECT COUNT(*) FROM account_alias WHERE id_account IS NULL")
        ).scalar()
        if skipped_aliases:
            print(f"  Skipping {skipped_aliases} orphaned aliases (id_account IS NULL)")
        for a in aliases:
            v2.execute(text(
                "INSERT INTO account_alias (id, number, name, id_account) "
                "VALUES (:id, :number, :name, :id_account)"
            ), {"id": a.id, "number": a.number, "name": a.name, "id_account": a.id_account})
        commit_or_dry(v2)
        print(f"  {len(aliases)} aliases")

        # ── 7. Transactions ────────────────────────────────────────────────
        # Two-pass insert: id_duplicate_of is a self-referential FK, so we
        # insert all rows first (with NULL), then patch the duplicate links.
        print("Migrating transactions...")
        transactions = v1.execute(text(
            'SELECT id, custom_id, id_source, id_dest, "when", metadata, amount, id_currency, '
            "id_category, data_source, id_is_duplicate_of, description FROM transaction"
        )).fetchall()

        # Pass 1: insert without id_duplicate_of
        for t in transactions:
            v2.execute(text(
                "INSERT INTO transaction "
                "  (id, external_id, id_source, id_dest, date, raw_metadata, amount, "
                "   id_currency, id_category, data_source, description, is_reviewed) "
                "VALUES "
                "  (:id, :external_id, :id_source, :id_dest, :date, :raw_metadata, :amount, "
                "   :id_currency, :id_category, :data_source, :description, :is_reviewed)"
            ), {
                "id": t.id,
                "external_id": t.custom_id,
                "id_source": t.id_source,
                "id_dest": t.id_dest,
                "date": t[4],          # 'when' column — positional to avoid keyword clash
                "raw_metadata": json.dumps(t.metadata) if t.metadata else None,
                "amount": t.amount,
                "id_currency": t.id_currency,
                "id_category": t.id_category,
                "data_source": t.data_source,
                "description": t.description or "",
                "is_reviewed": t.id_category is not None,
            })
        commit_or_dry(v2)

        # Pass 2: set id_duplicate_of now that all rows exist
        duplicates = [(t.id, t.id_is_duplicate_of) for t in transactions if t.id_is_duplicate_of is not None]
        for tid, dup_id in duplicates:
            v2.execute(text(
                "UPDATE transaction SET id_duplicate_of = :dup_id WHERE id = :id"
            ), {"id": tid, "dup_id": dup_id})
        commit_or_dry(v2)
        print(f"  {len(transactions)} transactions ({len(duplicates)} duplicate links)")

        # ── 8. Groups → Wallets ────────────────────────────────────────────
        print("Migrating groups to wallets...")
        groups = v1.execute(text('SELECT id, name, description FROM "group"')).fetchall()
        for g in groups:
            v2.execute(text(
                "INSERT INTO wallet (id, name, description) VALUES (:id, :name, :description)"
            ), {"id": g.id, "name": g.name, "description": g.description})

        account_groups = v1.execute(
            text("SELECT id_group, id_account, contribution_ratio FROM account_group")
        ).fetchall()
        for ag in account_groups:
            v2.execute(text(
                "INSERT INTO wallet_account (id_wallet, id_account, contribution_ratio) "
                "VALUES (:id_wallet, :id_account, :ratio)"
            ), {"id_wallet": ag.id_group, "id_account": ag.id_account, "ratio": ag.contribution_ratio})
        commit_or_dry(v2)
        print(f"  {len(groups)} wallets, {len(account_groups)} wallet-account links")

        # ── 9. ML models ───────────────────────────────────────────────────
        print("Migrating ML models...")
        models = v1.execute(
            text("SELECT id, filename, metadata, state FROM ml_model_file")
        ).fetchall()
        for m in models:
            # v1 state is an enum value like 'valid' / 'invalid'; v2 stores as varchar
            state_val = m.state.value if hasattr(m.state, "value") else str(m.state)
            v2.execute(text(
                "INSERT INTO ml_model (id, filename, metadata, state) "
                "VALUES (:id, :filename, :metadata, :state)"
            ), {
                "id": m.id,
                "filename": m.filename,
                "metadata": json.dumps(m.metadata) if m.metadata else None,
                "state": state_val,
            })
        commit_or_dry(v2)
        print(f"  {len(models)} ML models")

        # ── 10. Reset sequences ────────────────────────────────────────────
        if not dry_run:
            print("Resetting sequences...")
            for table in [
                "currency", '"user"', "category",
                "account", "account_alias",
                "transaction", "wallet", "ml_model",
            ]:
                v2.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}"
                ))
            v2.commit()

        # ── 11. Verification ───────────────────────────────────────────────
        print("\nVerification:")
        table_pairs = [
            ("currency",       "currency"),
            ('"user"',         '"user"'),
            ("category",       "category"),
            ("account",        "account"),
            ("account_alias",  "account_alias"),
            ("transaction",    "transaction"),
            ('"group"',        "wallet"),
            ("account_group",  "wallet_account"),
            ("ml_model_file",  "ml_model"),
        ]
        all_ok = True
        for v1_table, v2_table in table_pairs:
            c1 = v1.execute(text(f"SELECT COUNT(*) FROM {v1_table}")).scalar()
            c2 = v2.execute(text(f"SELECT COUNT(*) FROM {v2_table}")).scalar()
            status = "OK" if c1 == c2 else "MISMATCH"
            if status != "OK":
                all_ok = False
            print(f"  {v1_table:20s} -> {v2_table:20s}: {c1:>6} -> {c2:>6}  [{status}]")

        if dry_run:
            print("\nDry-run complete — no data was written.")
        elif all_ok:
            print("\nMigration complete!")
        else:
            print("\nMigration complete with MISMATCHES — review output above.")
            sys.exit(1)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_conn_args(parser: argparse.ArgumentParser, prefix: str, label: str) -> None:
    """Add a mutually-described connection argument group for one side."""
    g = parser.add_argument_group(
        f"{label} connection",
        f"Provide exactly one of: --{prefix}-url | --{prefix}-docker-service | --{prefix}-host",
    )
    g.add_argument(f"--{prefix}-url",      metavar="URL",      help="Full postgresql:// connection URL")
    g.add_argument(f"--{prefix}-host",     metavar="HOST",     help="Hostname / IP")
    g.add_argument(f"--{prefix}-port",     metavar="PORT",     type=int, default=5432, help="Port (default: 5432)")
    g.add_argument(f"--{prefix}-user",     metavar="USER",     help="Database user (default: postgres)")
    g.add_argument(f"--{prefix}-password", metavar="PASSWORD", help="Database password")
    g.add_argument(f"--{prefix}-db",       metavar="DBNAME",   help="Database name (default: USER)")
    if prefix != "v1":  # docker discovery only makes sense for the local v2 target
        g.add_argument(
            f"--{prefix}-docker-service",
            metavar="SERVICE",
            help="Docker compose service name (e.g. 'db'). Reads connection params from the container.",
        )
        g.add_argument(
            f"--{prefix}-docker-project",
            metavar="PROJECT",
            help="Docker compose project name — used to disambiguate when multiple projects share the service name.",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migrate v1 banking data to v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    _add_conn_args(parser, "v1", "Source (v1)")
    _add_conn_args(parser, "v2", "Target (v2)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read from v1 and verify counts, but do not commit any changes to v2.",
    )
    args = parser.parse_args()

    v1_url = resolve_url("v1", args, "v1", parser)
    v2_url = resolve_url("v2", args, "v2", parser)

    migrate(v1_url, v2_url, dry_run=args.dry_run)
