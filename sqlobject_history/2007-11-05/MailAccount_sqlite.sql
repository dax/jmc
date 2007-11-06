-- Exported definition from 2007-11-05T19:02:34
-- Class jmc.model.account.MailAccount
-- Database: sqlite
CREATE TABLE mail_account (
    id INTEGER PRIMARY KEY,
    login TEXT,
    password TEXT,
    host TEXT,
    port INT,
    _ssl TINYINT,
    _interval INT,
    store_password TINYINT,
    live_email_only TINYINT,
    lastcheck INT,
    waiting_password_reply TINYINT,
    first_check TINYINT,
    child_name VARCHAR(255)
)
