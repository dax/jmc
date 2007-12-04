-- Exported definition from 2007-12-04T17:57:39
-- Class jmc.model.account.SMTPAccount
-- Database: sqlite
CREATE TABLE smtp_account (
    id INTEGER PRIMARY KEY,
    login TEXT,
    password TEXT,
    host TEXT,
    port INT,
    tls TINYINT,
    store_password TINYINT,
    waiting_password_reply TINYINT,
    default_from TEXT,
    default_account TINYINT,
    child_name VARCHAR(255)
)
