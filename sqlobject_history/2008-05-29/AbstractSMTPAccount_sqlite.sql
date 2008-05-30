-- Exported definition from 2008-05-29T19:26:03
-- Class jmc.model.account.AbstractSMTPAccount
-- Database: sqlite
CREATE TABLE abstract_smtp_account (
    id INTEGER PRIMARY KEY,
    default_from TEXT,
    default_account TINYINT,
    child_name VARCHAR(255)
)
