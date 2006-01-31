##
## test_storage.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Fri May 20 10:46:58 2005 dax
## $Id: test_component.py,v 1.1 2005/07/11 20:39:31 dax Exp $
## 
## Copyright (C) 2005 adro8400
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##

import os
import unittest
import dummy_server
from jabber.storage import *
from jabber import mailconnection
from jabber.mailconnection import *

class Storage_TestCase(unittest.TestCase):
    def test_init(self):
        spool_dir = "./spool/test"
        self._storage = Storage(spool_dir = spool_dir)
        self.assertTrue(os.access(spool_dir, os.F_OK))
        self.assertEquals(self._storage.spool_dir, spool_dir)
        os.removedirs(spool_dir)
        
# TODO
class SQLiteStorage_TestCase(unittest.TestCase):
    def setUp(self):
        self._storage = SQLiteStorage()

    def tearDown(self):
        pass

class DBMStorage_TestCase(unittest.TestCase):
    def setUp(self):
        spool_dir = "./spool/test"
        self._storage = DBMStorage(nb_pk_fields = 2, spool_dir = spool_dir)
        self._account1 = IMAPConnection(login = "login1",
                                        password = "password1",
                                        host = "host1",
                                        port = 993,
                                        ssl = True,
                                        mailbox = "INBOX.box1")
        self._account1.chat_action = mailconnection.DO_NOTHING
        self._account1.online_action = mailconnection.DO_NOTHING
        self._account1.away_action = mailconnection.DO_NOTHING
        self._account1.xa_action = mailconnection.DO_NOTHING
        self._account1.dnd_action = mailconnection.DO_NOTHING
        self._account1.offline_action = mailconnection.DO_NOTHING
        self._account1.interval = 4
        self._account2 = POP3Connection(login = "login2",
                                        password = "password2",
                                        host = "host2",
                                        port = 1110,
                                        ssl = False)
        self._account2.chat_action = mailconnection.DO_NOTHING
        self._account2.online_action = mailconnection.DO_NOTHING
        self._account2.away_action = mailconnection.DO_NOTHING
        self._account2.xa_action = mailconnection.DO_NOTHING
        self._account2.dnd_action = mailconnection.DO_NOTHING
        self._account2.offline_action = mailconnection.DO_NOTHING
        self._account2.interval = 4
        self._account2.store_password = False
        self._account2.live_email_only = True

    def tearDown(self):
        db_file = self._storage.file
        self._storage = None
        os.remove(db_file)

    def test_set_get(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        self.assertEquals(self._storage[("test@localhost", "account1")],
                          self._account1)
        self.assertEquals(self._storage[("test@localhost", "account2")],
                          self._account2)

    def test_set_sync_get(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        loaded_storage = DBMStorage(nb_pk_fields = 2, spool_dir = "./spool/test")
        self.assertEquals(loaded_storage[("test@localhost", "account1")],
                          self._account1)
        self.assertEquals(loaded_storage[("test@localhost", "account2")],
                          self._account2)

    def test_set_del_get(self):
        self._storage[("test@localhost", "account2")] = self._account2
        del self._storage[("test@localhost", "account2")]
        try:
            self._storage[("test@localhost", "account2")]
        except KeyError:
            return
        self.fail("KeyError was expected")

    def test_haskey(self):
        self._storage[("test@localhost", "account2")] = self._account2
        self.assertTrue(self._storage.has_key((u"test@localhost", u"account2")))

    def test_partial_haskey(self):
        self._storage[("test@localhost", "account2")] = self._account2
        self.assertTrue(self._storage.has_key((u"test@localhost",)))

    def test_get_filtered(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        result = self._storage[("test@localhost",)]
        self.assertEquals(type(result), list)
        self.assertEquals(len(result), 2)
        self.assertEquals(result[1], self._account1)
        self.assertEquals(result[0], self._account2)

    def test_get_filtered2(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        result = self._storage[("account1",)]
        self.assertEquals(type(result), list)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], self._account1)
        
    def test_keys(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        result = self._storage.keys()
        self.assertEquals(type(result), list)
        self.assertEquals(len(result), 2)
        self.assertEquals(type(result[1]), tuple)
        self.assertEquals(len(result[1]), 2)
        self.assertEquals(result[1][0], "test@localhost")
        self.assertEquals(result[1][1], "account1")
        self.assertEquals(type(result[0]), tuple)
        self.assertEquals(len(result[0]), 2)
        self.assertEquals(result[0][0], "test@localhost")
        self.assertEquals(result[0][1], "account2")

    def test_keys_filtered(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        result = self._storage.keys(())
        self.assertEquals(type(result), list)
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], "test@localhost")
        
    def test_keys_filtered2(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        result = self._storage.keys(("test@localhost",))
        self.assertEquals(type(result), list)
        self.assertEquals(len(result), 2)
        self.assertEquals(result[0], "account2")
        self.assertEquals(result[1], "account1")

class SQLiteStorage_TestCase(DBMStorage_TestCase):
    def setUp(self):
        spool_dir = "./spool/test"
        self._storage = SQLiteStorage(nb_pk_fields = 2, spool_dir = spool_dir)
        self._account1 = IMAPConnection(login = "login1",
                                        password = "password1",
                                        host = "host1",
                                        port = 993,
                                        ssl = True,
                                        mailbox = "INBOX.box1")
        self._account1.chat_action = mailconnection.DIGEST
        self._account1.online_action = mailconnection.DIGEST
        self._account1.away_action = mailconnection.DO_NOTHING
        self._account1.xa_action = mailconnection.DO_NOTHING
        self._account1.dnd_action = mailconnection.DO_NOTHING
        self._account1.offline_action = mailconnection.DO_NOTHING
        self._account1.interval = 4
        self._account2 = POP3Connection(login = "login2",
                                        password = "password2",
                                        host = "host2",
                                        port = 1993,
                                        ssl = False)
        self._account2.chat_action = mailconnection.DO_NOTHING
        self._account2.online_action = mailconnection.DO_NOTHING
        self._account2.away_action = mailconnection.DO_NOTHING
        self._account2.xa_action = mailconnection.DO_NOTHING
        self._account2.dnd_action = mailconnection.DO_NOTHING
        self._account2.offline_action = mailconnection.DO_NOTHING
        self._account2.interval = 4
        self._account2.store_password = False
        self._account2.live_email_only = True

#     def tearDown(self):
#         os.remove(self._storage.file)
#         self._storage = None


    def test_set_sync_get(self):
        self._storage[("test@localhost", "account1")] = self._account1
        self._storage[("test@localhost", "account2")] = self._account2
        self._account2.password = None
        loaded_storage = SQLiteStorage(nb_pk_fields = 2, spool_dir = "./spool/test")
        self.assertEquals(loaded_storage[("test@localhost", "account1")],
                          self._account1)
        self.assertEquals(loaded_storage[("test@localhost", "account2")],
                          self._account2)
