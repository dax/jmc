##
## presence.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Wed Jun 27 22:05:08 2007 David Rousselie
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

import re

from jcl.jabber.presence import DefaultPresenceHandler, \
     DefaultSubscribeHandler, DefaultUnsubscribeHandler
from jcl.model.account import LegacyJID

from jcl.jabber import Handler
from jmc.jabber import MailHandler

class MailPresenceHandler(DefaultPresenceHandler):
    """Define filter for legacy JIDs presence handling"""
    def __init__(self):
        Handler.__init__(self)
        self.dest_jid_regexp = re.compile(".*%.*")

    def filter(self, stanza, lang_class):
        """Return empty array if JID match '.*%.*@componentJID'"""
        node = stanza.get_to().node
        if node is not None and self.dest_jid_regexp.match(node):
            bare_from_jid = unicode(stanza.get_from().bare())
            return [] # Not None
        return None

class MailSubscribeHandler(DefaultSubscribeHandler, MailHandler):
    """Use DefaultSubscribeHandler handle method and MailHandler filter.
    Filter email address in JID. Accept and add to LegacyJID table.
    """

    def __init__(self):
        DefaultSubscribeHandler.__init__(self)
        MailHandler.__init__(self)

    def filter(self, stanza, lang_class):
        return MailHandler.filter(self, stanza, lang_class)

    def handle(self, stanza, lang_class, accounts):
        result = DefaultSubscribeHandler.handle(self, stanza, lang_class, accounts)
        to_node = stanza.get_to().node
        to_email = to_node.replace('%', '@', 1)
        LegacyJID(legacy_address=to_email,
                  jid=unicode(stanza.get_to()),
                  account=accounts[0])
        return result

class MailUnsubscribeHandler(DefaultUnsubscribeHandler, MailHandler):
    """Use DefaultUnsubscribeHandler handle method and MailHandler filter.
    """

    def __init__(self):
        DefaultUnsubscribeHandler.__init__(self)
        MailHandler.__init__(self)

    def filter(self, stanza, lang_class):
        return MailHandler.filter(self, stanza, lang_class)

    def handle(self, stanza, lang_class, accounts):
        result = DefaultUnsubscribeHandler.handle(self, stanza, lang_class, accounts)
        legacy_jid = LegacyJID.select(\
           LegacyJID.q.jid == unicode(stanza.get_to()))
        if legacy_jid.count() == 1:
            legacy_jid[0].destroySelf()
        return result
