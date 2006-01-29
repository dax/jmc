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
        print "setting spool dir to " + spool_dir
        self._spool_dir = spool_dir
        if not os.path.isdir(self._spool_dir):
            os.makedirs(self._spool_dir)
        
    spool_dir = property(get_spool_dir, set_spool_dir)
    
class DBMStorage(Storage):
    def __init__(self, nb_pk_fields = 1, spool_dir = "."):
#        print "DBM INIT"
        Storage.__init__(self, nb_pk_fields, spool_dir)
        self.__registered = self.load()
        
    def __del__(self):
        #        print "DBM STOP"
        self.sync()
        
    def load(self):
        #        print "DBM LOAD"
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
        #        print "DBM SYNC"
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
                                         'c')
            for pk in self.__registered.keys():
                str_registered[pk] = str(self.__registered[pk])
	except Exception, e:
	    print >>sys.stderr, "Cannot save to registered.db : "
	    print >>sys.stderr, e
        str_registered.close()
        
    def __setitem__(self, pk_tuple, obj):
#        print "Adding " + "#".join(pk_tuple) + " = " + str(obj)
        self.__registered[str("#".join(pk_tuple))] = obj
        self.sync()

    def __getitem__(self, pk_tuple):
#        print "Getting " + "#".join(pk_tuple)
        if len(pk_tuple) == self.nb_pk_fields:
            return self.__registered[str("#".join(pk_tuple))]
        else:
            partial_key = str("#".join(pk_tuple))
            regexp = re.compile(partial_key)
            return [self.__registered[key]
                    for key in self.__registered.keys()
                    if regexp.search(key)]

    def __delitem__(self, pk_tuple):
#        print "Deleting " + "#".join(pk_tuple)
        del self.__registered[str("#".join(pk_tuple))]
        self.sync()

    def has_key(self, pk_tuple):
        if len(pk_tuple) == self.nb_pk_fields:
            return self.__registered.has_key(str("#".join(pk_tuple)))
        else:
            partial_key = str("#".join(pk_tuple))
            regexp = re.compile("^" + partial_key)
            for key in self.__registered.keys():
                if regexp.search(key):
                    return True
            return False

    def keys(self, pk_tuple = None):
        if pk_tuple is None:
            return [tuple(key.split("#")) for key in self.__registered.keys()]
        else:
            level = len(pk_tuple)
            partial_key = str("#".join(pk_tuple))
            regexp = re.compile("^" + partial_key)
            result = {}
            for key in self.__registered.keys():
                if regexp.search(key):
                    result[key.split("#")[level]] = None
            return result.keys()

    def dump(self):
#        print "dumping"
        for pk in self.__registered.keys():
            print pk + " = " + str(self.__registered[pk])
            
        
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
    
