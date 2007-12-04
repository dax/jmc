-- Exported definition from 2007-12-04T17:57:39
-- Class jcl.model.account.Account
-- Database: sqlite
CREATE TABLE account (
    id INTEGER PRIMARY KEY,
    name TEXT,
    jid TEXT,
    status TEXT,
    error TEXT,
    enabled TINYINT,
    lastlogin TIMESTAMP,
    user_id INT CONSTRAINT user_id_exists REFERENCES user(id) ,
    child_name VARCHAR(255)
)
