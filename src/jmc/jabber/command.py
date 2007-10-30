##
## command.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Tue Oct 23 18:45:19 2007 David Rousselie
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

from pyxmpp.jabber.dataforms import Form
import jcl.model.account as account

from jmc.model.account import MailAccount
from jcl.jabber.command import JCLCommandManager
import jcl.jabber.command as command

class MailCommandManager(JCLCommandManager):
    """
    Implement ad-hoc commands specific to JMC:
    - retrieve email attachments
    - force email checking
    """

    def __init__(self, component=None, account_manager=None):
        """
        JMCCommandManager constructor.
        Register JMC ad-hoc commands
        """
        JCLCommandManager.__init__(self, component, account_manager)
        self.__logger = logging.getLogger("jmc.jabber.command.JMCCommandManager")
        #self.commands["jmc#retrieve-attachment"] = (False, command.account_node_re)
        self.commands["jmc#force-check"] = (False, command.account_node_re)

    # Delayed for JMC 0.3.1
    def execute_retrieve_attachment_1(self, info_query, session_context,
                                      command_node, lang_class):
        # TODO : translate
        self.__logger.debug("Executing command 'retrieve-attachment' step 1")
        self.add_actions(command_node, [command.ACTION_NEXT])
        bare_from_jid = info_query.get_from().bare()
        account_name = info_query.get_to().node
        print str(bare_from_jid)
        print str(account_name)
        _account = account.get_account(bare_from_jid, account_name,
                                       MailAccount)
        if _account is not None:
            result_form = Form(xmlnode_or_type="form",
                               title="TODO:TITLE",
                               instructions="TODO:INS")
            field = result_form.add_field(name="attachments",
                                          field_type="list-multi",
                                          label="select attachments")
            field.add_option(label="Next",
                             values=["-1"])
            for (mail_id, mail_title) in _account.get_mail_with_attachment_list():
                field.add_option(label=mail_title,
                                 values=[mail_id])
            result_form.as_xml(command_node)
            return (result_form, [])
        else:
            # TODO Error
            return (None, [])

    # TODO: retrieve step2: Delayed to JMC 0.3.1

    def execute_force_check_1(self, info_query, session_context,
                              command_node, lang_class):
        self.__logger.debug("Executing command 'force-check' step 1")
        self.add_actions(command_node, [command.ACTION_COMPLETE])
        session_context["user_jids"] = [unicode(info_query.get_from().bare())]
        return (self.add_form_select_accounts(session_context, command_node,
                                              lang_class, "TODO:TITLE",
                                              "TODO:DESC", format_as_xml=True,
                                              show_user_jid=False), [])

    def execute_force_check_2(self, info_query, session_context,
                              command_node, lang_class):
        self.__logger.debug("Executing command 'force-check' step 2")
        command_node.setProp("status", command.STATUS_COMPLETED)
        accounts = []
        for account_name in session_context["account_names"]:
            name, user_jid = self.get_name_and_jid(account_name)
            _account = account.get_account(user_jid, name)
            _account.lastcheck = _account.interval - 1
            accounts.append(_account)
        self.component.check_email_accounts(accounts, lang_class)
        return (None, [])
