##
## config.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Fri Jan  7 11:06:42 2005 
## $Id: config.py,v 1.2 2005/03/13 11:39:36 dax Exp $
## 
## Copyright (C) 2005 
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

import libxml2
import os

from pyxmpp.jid import JID
from jmc.jabber.component import ComponentFatalError

class Config:
    def __init__(self, config_file):
        self.doc = None
        self.config_file = config_file
#        libxml2.initializeCatalog()
#         libxml2.loadCatalog(os.path.join(data_dir, "catalog.xml"))
        parser = libxml2.createFileParserCtxt(config_file)
#        parser.validate(1)
        parser.parseDocument()
        if not parser.isValid():
            raise ComponentFatalError, "Invalid configuration"
        self.doc = parser.doc()

    def get_content(self, xpath):
	return self.doc.xpathEval(xpath)[0].getContent()

    def __del__(self):
        if self.doc:
            self.doc.freeDoc()
