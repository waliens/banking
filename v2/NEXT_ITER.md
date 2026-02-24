Help me with this next iteration of my app:

# Icons for categories

In v1, all tags have an icon associated, this makes the use of the application more fun and also allow to display the icon to give a hint. It means also that user must be able to set an icon of a new transaction. You can create a custom script to extract the icons from the v1 database. Generally look how I use icons in the V1.

What could be great in addition to what is in v1 is a proper icon form when setting the icon of an existing category or creating a category

--v2-docker-service db --v2-docker-project v2 --v1-host 192.168.1.3 --v1-port 5433 --v1-user admin --v1-password 'cTk6KS58cU6X&8L62bhL!GtACjtbu' --v1-db banking

# Account alias management

In the v1, App, there was an account alias management page. The idea is to add this feature back to the v2 (in the admin panel). The accounts being used in several places in the App it is important to be able to group aliases of an account together and make sure all these aliases to be considered as a unique account. This means that the user must have the ability to merge accounts which are aliases of each other. Auto merging should be already implemented in the backend (based on IBAN or old belgian account naming), but double check. The goal of the UX is to make it as seamless and easy as possible to merge accounts together, to remove an account from an alias and to define or redefine the name of the representative account of the alias so that the user has a readable name. Most of this is already in v1 but UI/UX should be improved simplified. If you have ideas on how to make it simpler to find alias, propose and idea (there was a search based on levenstein distance but it might not be user friendly enough)

# Import tracking

To help post processing an import (e.g. managing duplicates, merging accounts), it would be nice to have a way to
display characteristics of all data associated with an import & other information:
- transactions (including filter to show only transactions that were auto-tagged via the rule system)
- auto-detected duplicates of this import, duplicates can be
   * either ignored at upload, it would be interesting to know how many were ignored this way but it is not necessary to record them
   * or registered in the database but auto-marked as a duplicate of another transaction, it would be nice to have the list of such transactions
- list new accounts
- statistics: how many transactions added, how many accounts, how many duplicates, how many transactions auto-tagged (via the rules)
- date and time when import happened, date and time of earliest and latest transaction of the import
- list of uploaded files by name

The import list can be accessed via the import page where it should be possible to dive further into an individual import. You can decide how to structure the UX on this page but import feature being a core functionality should remain at the front !

# Duplicate management in Admin panel

In the v1, there was a duplicate transaction management page where it was possible to list all transactions marked as duplicate (un-mark them, show comparatibe tables between both transactions of a duplicate). Please add such a feature back in v2. Important elements:
- a list of duplicate transactions with key information displayed on the list items (not too much info) and more info accessible in some ways e.g. a diff like view for the two transactions allowing to see what differs and what is the same
- some filters must be present to be able to find specific transaction quickly (start & end, amount, by import id & show date time of import as key to select a specific import)
- it must be possible to unmark a pair of duplicate transactions to make them not duplicate

# Transaction page bug

Bug in transaction page the transition to the transaction page from the transaction list does not work as expected. Issue is that scroll of the list is linked to the transaction page and when the list is scrolled down the transition goes to a scrolled down transaction page which is blank because content is at the top.

# Review page

A tooltip should be added on the transaction description to show the full description if user want. It should be possible to display all the transaction information from the review page because sometimes it is useful to have a little more context to properly classify a transaction. The goal here is not to disrupt too much the review flow when requesting this information.
In v1, this is happening when clicking on the transaction row which extends the row in the table with the addition information. This is nice but the issue is that it extends the list height which can disrupt the review.

the additional information must include:
- source account info
- dest account info
- any other info you see relevant and that's not already displayed in the list item

The duplicate management can still happen in this context but priority is transaction information.

The fitler form is nice but is missing some fields, for instance source and dest account (look at v1)

Also there is a bug in the current filter form: overlapping fields.




- Add link to import page on transaction detail page
- Don't create a second migration script from V1 to V2, include icon migration in the original script and create a harcoded mapping in the migration script (decide yourself the mapping based on icons)
About the alembic migrations, you can consider that the app is still in development so all changes can be integrated in a single migration that creates everything