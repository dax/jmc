-- Exported definition from 2007-12-04T17:57:39
-- Class jmc.model.account.IMAPAccount
-- Database: sqlite
CREATE TABLE imap_account (
    id INTEGER PRIMARY KEY,
    mailbox TEXT,
    delimiter TEXT,
    child_name VARCHAR(255)
)
