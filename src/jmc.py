##
## jmc.py
## Login : <dax@happycoders.org>
## Started on  Fri Jan 19 18:14:41 2007 David Rousselie
## $Id$
## 
## Copyright (C) 2007 David Rousselie
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

import logging
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

from sqlobject import *
from pyxmpp.message import Message

from jmc.jabber.component import MailComponent
from jmc.model.account import MailPresenceAccount

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)
component = MailComponent("jmc.localhost", \
                          "secret", \
                          "127.0.0.1", \
                          5349, \
                          "sqlite:///tmp/jmc_test.db")
component.account_class = MailPresenceAccount
component.run()
logger.debug("JMC is exiting")
