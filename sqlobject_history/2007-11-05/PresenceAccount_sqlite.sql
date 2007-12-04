-- Exported definition from 2007-11-05T19:02:34
-- Class jcl.model.account.PresenceAccount
-- Database: sqlite
CREATE TABLE presence_account (
    id INTEGER PRIMARY KEY,
    chat_action INT,
    online_action INT,
    away_action INT,
    xa_action INT,
    dnd_action INT,
    offline_action INT,
    child_name VARCHAR(255)
)
