-- Class jmc.model.account.AbstractSMTPAccount
-- Database: sqlite
CREATE TABLE abstract_smtp_account (
    id INTEGER PRIMARY KEY,
    default_from TEXT,
    default_account TINYINT,
    child_name VARCHAR(255)
);

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
);

INSERT INTO abstract_smtp_account
       SELECT
              id,
              default_from,
              default_account,
              "GlobalSMTPAccount"
       FROM
              smtp_account;

INSERT INTO global_smtp_account
       SELECT
              id,
              login,
              password,
              host,
              port,
              tls,
              store_password,
              waiting_password_reply,
              "SMTPAccount"
       FROM
              smtp_account;

DROP TABLE smtp_account;

-- Class jmc.model.account.SMTPAccount
-- Database: sqlite
CREATE TABLE smtp_account (
    id INTEGER PRIMARY KEY,
    child_name VARCHAR(255)
);

INSERT INTO smtp_account
       SELECT
              id,
              NULL
       FROM
              global_smtp_account;

UPDATE account SET
       child_name="AbstractSMTPAccount"
WHERE
       child_name="SMTPAccount";
