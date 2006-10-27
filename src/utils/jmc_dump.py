##
## dump.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Mon Jan 30 21:43:38 2006 David Rousselie
## $Id$
## 
## Copyright (C) 2006 
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
import jmc.utils.storage
import os.path
import re


if len(sys.argv) != 3:
    print >>sys.stderr, "Usage: " + sys.argv[0] + " db_type db_file"
    print >>sys.stderr, "Supported DB type are :"
    for var in [aclass
                for aclass in dir(jmc.utils.storage)
                if type(getattr(jmc.utils.storage, aclass)) == types.ClassType \
                and re.compile(".+Storage$").match(aclass) is not None]:
        print >>sys.stderr, "\t" + var
    sys.exit(1)

from_storage_class = sys.argv[1]
from_file = sys.argv[2]

if not os.path.exists(from_file):
    print >>sys.stderr, from_file + " does not exist."
    sys.exit(1)

from jmc.utils.storage import *

try:
    from_storage = globals()[from_storage_class + "Storage"](2, db_file = from_file)
except Exception,e:
    print >>sys.stderr, e
    print >>sys.stderr, "Cannot find " + from_storage_class + "Storage class"
    sys.exit(1)

for jid, name in from_storage.keys():
    print jid + "/" + name + " from " + from_storage_class + " = " + str(from_storage[(jid, name)])
