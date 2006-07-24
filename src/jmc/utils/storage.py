##
## storage.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Wed Jul 20 20:26:53 2005 dax
## $Id: storage.py,v 1.1 2005/09/18 20:24:07 dax Exp $
## 
## Copyright (C) 2005 dax
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
import re
import os.path
import sys
import anydbm
import logging
from UserDict import UserDict

import jmc.email.mailconnection_factory as mailconnection_factory


class Storage(UserDict):
    def __init__(self, nb_pk_fields = 1, spool_dir = ".", db_file = None):
        UserDict.__init__(self)
        self.nb_pk_fields = nb_pk_fields
        if db_file is None:
            self._spool_dir = ""
            self.set_spool_dir(spool_dir)
            self.file = self._spool_dir + "/registered.db"
        else:
            spool_dir = os.path.dirname(db_file) or "."
            self.set_spool_dir(spool_dir)
            self.file = db_file
        self._registered = self.load()
        
    def __setitem__(self, pk_tuple, obj):
#        print "Adding " + "#".join(map(str, pk_tuple)) + " = " + str(obj)
        self._registered[str("#".join(map(str, pk_tuple)))] = obj

    def __getitem__(self, pk_tuple):
#        print "Getting " + "#".join(map(str, pk_tuple))
        if len(pk_tuple) == self.nb_pk_fields:
            return self._registered[str("#".join(map(str, pk_tuple)))]
        else:
            partial_key = str("#".join(map(str, pk_tuple)))
            regexp = re.compile(partial_key)
            return [self._registered[key]
                    for key in self._registered.keys()
                    if regexp.search(key)]

    def __delitem__(self, pk_tuple):
        #print "Deleting " + "#".join(map(str, pk_tuple))
        del self._registered[str("#".join(map(str, pk_tuple)))]

    def get_spool_dir(self):
        return self._spool_dir

    def set_spool_dir(self, spool_dir):
        self._spool_dir = spool_dir
        if not os.path.isdir(self._spool_dir):
            os.makedirs(self._spool_dir)
        
    spool_dir = property(get_spool_dir, set_spool_dir)

    def has_key(self, pk_tuple):
        if len(pk_tuple) == self.nb_pk_fields:
            return self._registered.has_key(str("#".join(map(str, pk_tuple))))
        else:
            partial_key = str("#".join(map(str, pk_tuple)))
            regexp = re.compile("^" + partial_key)
            for key in self._registered.keys():
                if regexp.search(key):
                    return True
            return False

    def keys(self, pk_tuple = None):
        if pk_tuple is None:
            return [tuple(key.split("#")) for key in self._registered.keys()]
        else:
            level = len(pk_tuple)
            partial_key = str("#".join(map(str, pk_tuple)))
            regexp = re.compile("^" + partial_key)
            result = {}
            for key in self._registered.keys():
                if regexp.search(key):
                    result[key.split("#")[level]] = None
            return result.keys()

    def dump(self):
        for pk in self._registered.keys():
            print pk + " = " + str(self._registered[pk])

    def load(self):
        pass

class DBMStorage(Storage):
    _logger = logging.getLogger("jmc.utils.DBMStorage")

    def __init__(self, nb_pk_fields = 1, spool_dir = ".", db_file = None):
#        print "DBM INIT"
        Storage.__init__(self, nb_pk_fields, spool_dir, db_file)
        
    def __del__(self):
        #        print "DBM STOP"
        self.sync()
        
    def load(self):
        str_registered = anydbm.open(self.file, \
                                     'c')
        result = {}
	try:
	    for pk in str_registered.keys():
                result[pk] = mailconnection_factory.str_to_mail_connection(str_registered[pk])
	except Exception, e:
	    print >>sys.stderr, "Cannot load registered.db : "
	    print >>sys.stderr, e
        str_registered.close()
        return result

    def sync(self):
        #print "DBM SYNC"
        self.store()
        
    def __store(self, nb_pk_fields, registered, pk):
        if nb_pk_fields > 0:
            for key in registered.keys():
                if pk:
                    self.__store(nb_pk_fields - 1, \
                                registered[key], pk + "#" + key)
                else:
                    self.__store(nb_pk_fields - 1, \
                                registered[key], key)
        else:
            self.__str_registered[pk] = str(registered)
#            print "STORING : " + pk + " = " + str(registered)
            
    def store(self):
#        print "DBM STORE"
        try:
            str_registered = anydbm.open(self.file, \
                                         'n')
            for pk in self._registered.keys():
                str_registered[pk] = str(self._registered[pk])
	except Exception, e:
	    print >>sys.stderr, "Cannot save to registered.db : "
	    print >>sys.stderr, e
        str_registered.close()

    def __setitem__(self, pk_tuple, obj):
        Storage.__setitem__(self, pk_tuple, obj)
        self.sync()

    def __delitem__(self, pk_tuple):
        Storage.__delitem__(self, pk_tuple)
        self.sync()

# Do not fail if pysqlite is not installed
try:
    from pysqlite2 import dbapi2 as sqlite

    class SQLiteStorage(Storage):
        _logger = logging.getLogger("jmc.utils.SQLiteStorage")
    
        def __init__(self, nb_pk_fields = 1, spool_dir = ".", db_file = None):
            self.__connection = None
            Storage.__init__(self, nb_pk_fields, spool_dir, db_file)

        def create(self):
            SQLiteStorage._logger.debug("creating new Table")
            cursor = self.__connection.cursor()
            cursor.execute("""
            create table account(
            jid STRING,
            name STRING,
            type STRING,
            login STRING,
            password STRING,
            host STRING,
            port INTEGER,
            chat_action INTEGER,
            online_action INTEGER,
            away_action INTEGER,
            xa_action INTEGER,
            dnd_action INTEGER,
            offline_action INTEGER,
            interval INTEGER,
            live_email_only BOOLEAN,
            mailbox STRING,
            PRIMARY KEY(jid, name)
            )
            """)
            self.__connection.commit()
            cursor.close()
            
        def __del__(self):
            self.__connection.close()

        def sync(self):
            pass

        def load(self):
            if not os.path.exists(self.file):
                self.__connection = sqlite.connect(self.file)
                self.create()
            else:
                self.__connection = sqlite.connect(self.file)
            cursor = self.__connection.cursor()
            cursor.execute("""select * from account""")
            result = {}
            for row in cursor.fetchall():
                #             print "Creating new " + row[self.nb_pk_fields] + " connection."
                account_type = row[self.nb_pk_fields]
                account = result["#".join(row[0:self.nb_pk_fields])] = mailconnection_factory.get_new_mail_connection(account_type)
                account.login = row[self.nb_pk_fields + 1]
                account.password = row[self.nb_pk_fields + 2]
                if account.password is None:
                    account.store_password = False
                else:
                    account.store_password = True
                account.host = row[self.nb_pk_fields + 3]
                account.port = int(row[self.nb_pk_fields + 4])
                account.chat_action = int(row[self.nb_pk_fields + 5])
                account.online_action = int(row[self.nb_pk_fields + 6])
                account.away_action = int(row[self.nb_pk_fields + 7])
                account.xa_action = int(row[self.nb_pk_fields + 8])
                account.dnd_action = int(row[self.nb_pk_fields + 9])
                account.offline_action = int(row[self.nb_pk_fields + 10])
                account.interval = int(row[self.nb_pk_fields + 11])
                account.live_email_only = (row[self.nb_pk_fields + 12] == 1)
                if account_type[0:4] == "imap":
                    account.mailbox = row[self.nb_pk_fields + 13]
                    #            for field_index in range(self.nb_pk_fields + 1, len(row)):
                    #                 print "\tSetting " + str(cursor.description[field_index][0]) + \
                    #                       " to " + str(row[field_index])
                    #                setattr(account,
                    #                        cursor.description[field_index][0],
                    #                        row[field_index])
            cursor.close()
            return result
    
        def __setitem__(self, pk_tuple, obj):
            Storage.__setitem__(self, pk_tuple, obj)
            cursor = self.__connection.cursor()
            mailbox = None
            password = None
            if obj.type[0:4] == "imap":
                mailbox = obj.mailbox
            if obj.store_password == True:
                password = obj.password
            cursor.execute("""
            insert or replace into account values
            (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                           (pk_tuple[0],
                            pk_tuple[1],
                            obj.type,
                            obj.login,
                            password,
                            obj.host,
                            obj.port,
                            obj.chat_action,
                            obj.online_action,
                            obj.away_action,
                            obj.xa_action,
                            obj.dnd_action,
                            obj.offline_action,
                            obj.interval,
                            obj.live_email_only,
                            mailbox))
            self.__connection.commit()
            cursor.close()
        
        def __delitem__(self, pk_tuple):
            Storage.__delitem__(self, pk_tuple)
            cursor = self.__connection.cursor()
            cursor.execute("""
            delete from account where jid = ? and name = ?
            """,
                           (pk_tuple[0],
                            pk_tuple[1]))
            self.__connection.commit()
            cursor.close()
except ImportError:
    pass

