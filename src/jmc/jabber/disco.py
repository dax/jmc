##
## disco.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Sun Jul  8 20:55:46 2007 David Rousselie
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

from pyxmpp.jid import JID
from pyxmpp.jabber.disco import DiscoItems, DiscoItem

from jcl import jabber
from jcl.model import account
from jcl.jabber.command import CommandRootDiscoGetInfoHandler
from jcl.jabber.disco import AccountTypeDiscoGetInfoHandler, \
     AccountDiscoGetInfoHandler, DiscoHandler
import jcl.jabber.command as command

from jmc.model.account import IMAPAccount

class MailRootDiscoGetInfoHandler(CommandRootDiscoGetInfoHandler):
    def handle(self, stanza, lang_class, node, disco_obj, data):
        """Add jabber:iq:gateway support"""
        disco_infos = CommandRootDiscoGetInfoHandler.handle(self, stanza, lang_class,
                                                            node, disco_obj, data)
        disco_infos[0].add_feature("jabber:iq:gateway")
        disco_infos[0].add_identity(self.component.name, "headline", "newmail")
        return disco_infos

class MailAccountTypeDiscoGetInfoHandler(AccountTypeDiscoGetInfoHandler):
    def handle(self, stanza, lang_class, node, disco_obj, data):
        disco_infos = AccountTypeDiscoGetInfoHandler.handle(self, stanza,
                                                            lang_class,
                                                            node, disco_obj,
                                                            data)
        if node == "IMAP" and account.get_accounts(stanza.get_from().bare(),
                                                   IMAPAccount).count() > 0:
            disco_infos[0].add_feature("http://jabber.org/protocol/disco#info")
            disco_infos[0].add_feature("http://jabber.org/protocol/disco#items")
        return disco_infos

class IMAPAccountDiscoGetInfoHandler(AccountDiscoGetInfoHandler):
    def handle(self, stanza, lang_class, node, disco_obj, data):
        disco_infos = AccountDiscoGetInfoHandler.handle(self, stanza,
                                                        lang_class,
                                                        node, disco_obj,
                                                        data)
        disco_infos[0].add_feature(command.COMMAND_NS)
        splitted_node = node.split("/")
        splitted_node_len = len(splitted_node)
        if splitted_node_len > 1 and \
            splitted_node[0] == "IMAP":
            _account = account.get_account(stanza.get_from().bare(),
                                           splitted_node[1],
                                           IMAPAccount)
            if _account is not None:
                disco_infos[0].add_feature("http://jabber.org/protocol/disco#info")
                if splitted_node_len > 2:
                    imap_dir = "/".join(splitted_node[2:])
                    if len(_account.ls_dir(imap_dir)) > 0:
                        disco_infos[0].add_feature("http://jabber.org/protocol/disco#items")
                else:
                    disco_infos[0].add_feature("http://jabber.org/protocol/disco#items")
        return disco_infos

class IMAPAccountDiscoGetItemsHandler(DiscoHandler):
    def __init__(self, component):
        DiscoHandler.__init__(self, component)
        self.__logger = logging.getLogger("jcl.jabber.IMAPAccountDiscoGetItemsHandler")

    def filter(self, stanza, lang_class, node=None):
        if node is None:
            return None
        splitted_node = node.split("/")
        splitted_node_len = len(splitted_node)
        if splitted_node_len < 2:
            return None
        account_type = splitted_node[0]
        if account_type != "IMAP":
            return None
        account_name = splitted_node[1]
        if splitted_node_len == 2:
            imap_dir = None
        else:
            imap_dir = "/".join(splitted_node[2:])
        return (account_type, account_name, imap_dir)

    def handle(self, stanza, lang_class, node, disco_obj, data):
        """Discovery get_items on an IMAP account"""
        account_type, account_name, imap_dir = data
        bare_from_jid = stanza.get_from().bare()
        self.__logger.debug("Listing " + str(imap_dir) + " IMAP directory")
        account_class = self.component.account_manager.get_account_class(account_type)
        _account = account.get_account(bare_from_jid, account_name,
                                       account_class=account_class)
        if account_class is not None and _account is not None:
            disco_items = DiscoItems()
            if imap_dir is None:
                imap_dir = ""
            subdirs = _account.ls_dir(imap_dir)
            if imap_dir != "":
                imap_dir += "/"
            for subdir in subdirs:
                DiscoItem(disco_items,
                          JID(unicode(_account.jid) + "/" + account_type + \
                              "/" + imap_dir + subdir),
                          account_type + "/" + account_name + "/" + imap_dir
                          + subdir,
                          subdir)
            return [disco_items]
        return []

