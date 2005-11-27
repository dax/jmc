##
## storage.py
## Login : <dax@happycoders.org>
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
import mailconnection_factory
from UserDict import UserDict

class Storage(UserDict):
    def __init__(self, nb_pk_fields = 1, spool_dir = "."):
        UserDict.__init__(self)
        self._spool_dir = ""
        self.set_spool_dir(spool_dir)
        self.nb_pk_fields = nb_pk_fields
        self.file = self._spool_dir + "/registered.db"
        
    # return hash of hash (jid and name)
    def load(self):
        pass

    def sync(self):
        pass
    
    def store(self, nb_pk_fields, registered, pk):
        pass
    
    def add(self, key_list, obj):
        pass

    def remove(self, key_list):
        pass
    
    def get_spool_dir(self):
        return self._spool_dir

    def set_spool_dir(self, spool_dir):
        self._spool_dir = spool_dir
        if not os.path.isdir(self._spool_dir):
            os.makedirs(self._spool_dir)
        
    spool_dir = property(get_spool_dir, set_spool_dir)
    
class DBMStorage(Storage):
    def __init__(self, nb_pk_fields = 1, spool_dir = "."):
#        print "DBM INIT"
        Storage.__init__(self, nb_pk_fields, spool_dir)
        self.__str_registered = anydbm.open(self.file, \
                                            'c')
        
    def __del__(self):
#        print "DBM STOP"
        self.__str_registered.close()

    def load(self):
#        print "DBM LOAD"
        result = {}
	try:
	    for pk in self.__str_registered.keys():
                pk_list = pk.split('#')
                obj = result
                key = None
                while pk_list:
                    key = pk_list.pop(0)
                    if pk_list:
                        if not obj.has_key(key):
                            obj[key] = {}
                        obj = obj[key]
                obj[key] = mailconnection_factory.str_to_mail_connection(self.__str_registered[pk])
	except Exception, e:
	    print >>sys.stderr, "Cannot load registered.db : "
	    print >>sys.stderr, e
        return result

    def sync(self):
#        print "DBM SYNC"
        self.__str_registered.close()
        self.__str_registered = anydbm.open(self.file, \
                                            'c')
        
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
            print "STORING : " + pk + " = " + str(registered)
            
    def store(self, registered):
#        print "DBM STORE"
        try:
            self.__store(self.nb_pk_fields, registered, "")
            # Force file synchronisation
            self.sync()
	except Exception, e:
	    print >>sys.stderr, "Cannot save to registered.db : "
	    print >>sys.stderr, e

    def __setitem__(self, pk_tuple, obj):
#        print "Adding " + "#".join(pk_tuple) + " = " + str(obj)
        self.__str_registered["#".join(pk_tuple)] = str(obj)
        self.sync()

    def __getitem__(self, pk_tuple):
#        print "Getting " + "#".join(pk_tuple)
        if len(pk_tuple) == self.nb_pk_fields:
            return  mailconnection_factory.str_to_mail_connection(self.__str_registered["#".join(pk_tuple)])
        else:
            partial_key = "#".join(pk_tuple)
            regexp = re.compile(partial_key)
            return [mailconnection_factory.str_to_mail_connection(self.__str_registered[key])
                    for key in self.__str_registered.keys()
                    if regexp.search(key)]

    def __delitem__(self, pk_tuple):
#        print "Deleting " + "#".join(pk_tuple)
        del self.__str_registered["#".join(pk_tuple)]
        self.sync()

    def has_key(self, pk_tuple):
        return self.__str_registered.has_key("#".join(pk_tuple))

    def keys(self, pk_tuple = None):
        if pk_tuple is None:
            return [tuple(key.split("#")) for key in self.__str_registered.keys()]
        else:
            level = len(pk_tuple)
            partial_key = "#".join(pk_tuple)
            regexp = re.compile("^" + partial_key)
            result = {}
            for key in self.__str_registered.keys():
                if regexp.search(key):
                    result[key.split("#")[level]] = None
            return result.keys()
        
class SQLiteStorage(Storage):
    def __init__(self, nb_pk_fields = 1, spool_dir = "."):
        pass

    def load(self):
        pass

    def sync(self):
        pass
    
    def store(self, nb_pk_fields, registered, pk):
        pass
    
    def add(self, key_list, obj):
        pass

    def remove(self, key_list):
        pass
    
