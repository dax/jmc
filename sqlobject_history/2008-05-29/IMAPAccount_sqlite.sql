-- Exported definition from 2008-05-29T19:26:03
-- Class jmc.model.account.IMAPAccount
-- Database: sqlite
CREATE TABLE imap_account (
    id INTEGER PRIMARY KEY,
    mailbox TEXT,
    delimiter TEXT,
    child_name VARCHAR(255)
)
