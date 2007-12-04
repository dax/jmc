-- Exported definition from 2007-11-05T19:02:34
-- Class jcl.model.account.Account
-- Database: sqlite
CREATE TABLE account (
    id INTEGER PRIMARY KEY,
    name TEXT,
    jid TEXT,
    status TEXT,
    in_error TINYINT,
    enabled TINYINT,
    lastlogin TIMESTAMP,
    user_id INT CONSTRAINT user_id_exists REFERENCES user(id) ,
    child_name VARCHAR(255)
)
