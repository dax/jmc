# -*- coding: utf-8 -*-
##
## component.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Fri Jan  7 11:06:42 2005
## $Id: component.py,v 1.12 2005/09/18 20:24:07 dax Exp $
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

from sqlobject.sqlbuilder import AND

import jcl.jabber as jabber
import jcl.model as model
from jcl.model import account
from jcl.model.account import Account, User
from jcl.jabber.disco import  \
     AccountTypeDiscoGetInfoHandler, AccountDiscoGetInfoHandler
from jcl.jabber.feeder import FeederComponent
from jcl.jabber.command import CommandRootDiscoGetInfoHandler
from jcl.jabber.component import AccountManager
from jmc.model.account import IMAPAccount, POP3Account, \
    AbstractSMTPAccount, GlobalSMTPAccount, SMTPAccount

from jmc.jabber.disco import MailRootDiscoGetInfoHandler, \
     IMAPAccountDiscoGetItemsHandler, MailAccountTypeDiscoGetInfoHandler, \
     IMAPAccountDiscoGetInfoHandler
from jmc.jabber.message import SendMailMessageHandler, \
     RootSendMailMessageHandler
from jmc.jabber.presence import MailSubscribeHandler, \
     MailUnsubscribeHandler, MailPresenceHandler
from jmc.lang import Lang
from jmc.jabber.command import MailCommandManager
from jmc.jabber.feeder import MailFeederHandler, MailFeeder, MailSender

class MailAccountManager(AccountManager):
    def account_get_register(self, info_query,
                             name,
                             from_jid,
                             account_type,
                             lang_class):
        """
        Handle get_register on an IMAP account.
        Return a preinitialized form.
        account_type contains 'account_type + imap_dir'
        """
        splitted_node = account_type.split("/")
        splitted_node_len = len(splitted_node)
        if splitted_node_len == 1 or \
            splitted_node[0] != "IMAP":
            return AccountManager.account_get_register(self,
                                                       info_query,
                                                       name, from_jid,
                                                       account_type,
                                                       lang_class)
        else:
            info_query = info_query.make_result_response()
            model.db_connect()
            imap_dir = "/".join(splitted_node[1:])
            bare_from_jid = from_jid.bare()
            _account = account.get_account_filter(\
                AND(AND(User.q.jid == unicode(bare_from_jid),
                        Account.q.userID == User.q.id),
                    IMAPAccount.q.mailbox == imap_dir),
                account_class=IMAPAccount)
            query = info_query.new_query("jabber:iq:register")
            if _account is not None:
                # update account
                result = self.generate_registration_form_init(lang_class,
                                                              _account)
            else:
                _account = account.get_account(bare_from_jid, name,
                                               IMAPAccount)
                if _account is not None:
                    # create new account based on current one
                    result = self.generate_registration_form_init(lang_class,
                                                                  _account)
                    result["name"].value = None
                    result["name"].type = "text-single"
                    result["mailbox"].value = imap_dir.replace("/", _account.delimiter)
                else:
                    # create new account from scratch
                    result = self.generate_registration_form(\
                        lang_class,
                        IMAPAccount,
                        bare_from_jid)
                    result["mailbox"].value = imap_dir
            result.as_xml(query)
            return [info_query]

class MailComponent(FeederComponent):
    """Jabber Mail Component main implementation"""

    def __init__(self,
                 jid,
                 secret,
                 server,
                 port,
                 config,
                 config_file,
                 lang=Lang(),
                 account_manager_class=MailAccountManager,
                 command_manager_class=MailCommandManager):
        """Use FeederComponent behavior and setup feeder and sender
        attributes.
        """
        FeederComponent.__init__(self,
                                 jid,
                                 secret,
                                 server,
                                 port,
                                 config,
                                 config_file,
                                 lang=lang,
                                 account_manager_class=account_manager_class,
                                 command_manager_class=command_manager_class)
        self.handler = MailFeederHandler(MailFeeder(self), MailSender(self))
        self.account_manager.account_classes = (IMAPAccount,
                                                POP3Account,
                                                SMTPAccount)
        self.msg_handlers[0] += [SendMailMessageHandler(self),
                                 RootSendMailMessageHandler(self)]
        self.presence_subscribe_handlers += [[MailSubscribeHandler(self)]]
        self.presence_unsubscribe_handlers += [[MailUnsubscribeHandler(self)]]
        self.presence_available_handlers += [[MailPresenceHandler(self)]]
        self.presence_unavailable_handlers += [[MailPresenceHandler(self)]]
        self.disco_get_items_handlers[0] += [IMAPAccountDiscoGetItemsHandler(self)]
        jabber.replace_handlers(self.disco_get_info_handlers,
                                CommandRootDiscoGetInfoHandler,
                                MailRootDiscoGetInfoHandler(self))
        jabber.replace_handlers(self.disco_get_info_handlers,
                                AccountTypeDiscoGetInfoHandler,
                                MailAccountTypeDiscoGetInfoHandler(self))
        jabber.replace_handlers(self.disco_get_info_handlers,
                                AccountDiscoGetInfoHandler,
                                IMAPAccountDiscoGetInfoHandler(self))

    def check_email_accounts(self, accounts, lang_class=None):
        if lang_class is None:
            lang_class = self.lang.get_default_lang_class()
        self.handler.handle(None, lang_class, accounts)
