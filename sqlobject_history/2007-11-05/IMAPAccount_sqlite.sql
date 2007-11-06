-- Exported definition from 2007-11-05T19:02:34
-- Class jmc.model.account.IMAPAccount
-- Database: sqlite
CREATE TABLE imap_account (
    id INTEGER PRIMARY KEY,
    mailbox TEXT,
    delimiter TEXT,
    child_name VARCHAR(255)
)
