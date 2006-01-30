##
## jmc_backend_converter.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Sun Jan 29 18:46:29 2006 David Rousselie
## $Id$
## 
## Copyright (C) 2006 David Rousselie
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

import sys
sys.path.insert(0, "..")
import types
import jabber.storage
import os.path
import re

if len(sys.argv) != 5:
    print >>sys.stderr, "Usage: " + sys.argv[0] + " from_type from_db_file to_type to_db_file"
    print >>sys.stderr, "Supported DB type are :"
    for var in [aclass
                for aclass in dir(jabber.storage)
                if type(getattr(jabber.storage, aclass)) == types.ClassType \
                and re.compile(".+Storage$").match(aclass) is not None]:
        print >>sys.stderr, "\t" + var
    sys.exit(1)

from_storage_class = sys.argv[1]
from_file = sys.argv[2]
to_storage_class = sys.argv[3]
to_file = sys.argv[4]

if not os.path.exists(from_file):
    print >>sys.stderr, from_file + " does not exist."
    sys.exit(1)

from jabber.storage import *

from_storage = None
to_storage = None
try:
    from_storage = globals()[from_storage_class + "Storage"](2, db_file = from_file)
except Exception,e:
    print >>sys.stderr, e
    print >>sys.stderr, "Cannot find " + from_storage_class + "Storage class"
    sys.exit(1)
try:
    to_storage = globals()[to_storage_class + "Storage"](2, db_file = to_file)
except Exception,e:
    print >>sys.stderr, e
    print >>sys.stderr, "Cannot find " + to_storage_class + "Storage class"
    sys.exit(1)


for jid, name in from_storage.keys():
    print "Converting " + jid + "/" + name + " from " + from_storage_class + \
          " to " + to_storage_class + "."
    to_storage[(jid, name)] = from_storage[(jid, name)]

to_storage.sync()

