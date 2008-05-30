-- Exported definition from 2008-05-29T19:26:03
-- Class jmc.model.account.GlobalSMTPAccount
-- Database: sqlite
CREATE TABLE global_smtp_account (
    id INTEGER PRIMARY KEY,
    login TEXT,
    password TEXT,
    host TEXT,
    port INT,
    tls TINYINT,
    store_password TINYINT,
    waiting_password_reply TINYINT,
    child_name VARCHAR(255)
)
