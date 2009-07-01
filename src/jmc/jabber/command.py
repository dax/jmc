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
import re
import time

from pyxmpp.jabber.dataforms import Form

import jcl.model.account as account
import jcl.jabber.command as command
from jcl.jabber.command import JCLCommandManager, CommandError

from jmc.model.account import MailAccount
from jmc.jabber.feeder import MailSender

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
        self.commands["jmc#force-check"] = (False, re.compile(".*"))
        self.commands["jmc#get-email"] = (False, command.account_node_re)

    # Delayed to JMC 0.3.1
    def execute_retrieve_attachment_1(self, info_query, session_context,
                                      command_node, lang_class):
        self.__logger.debug("Executing command 'retrieve-attachment' step 1")
        self.add_actions(command_node, [command.ACTION_NEXT])
        bare_from_jid = info_query.get_from().bare()
        account_name = info_query.get_to().node
        _account = account.get_account(bare_from_jid, account_name,
                                       MailAccount)
        if _account is not None:
            result_form = Form(xmlnode_or_type="form",
                               title="TITLE",
                               instructions="INS")
            field = result_form.add_field(name="attachments",
                                          field_type="list-multi",
                                          label="select attachments")
            field.add_option(label="Next",
                             value="-1")
            for (mail_id, mail_title) in _account.get_mail_with_attachment_list():
                field.add_option(label=mail_title,
                                 value=mail_id)
            result_form.as_xml(command_node)
            return (result_form, [])
        else:
            # ERROR
            return (None, [])

    # retrieve step2: Delayed to JMC 0.3.1

    def execute_force_check_root_node(self, info_query, session_context,
                                      command_node, lang_class):
        self.__logger.debug("Executing command 'force-check' step 1 on root node")
        self.add_actions(command_node, [command.ACTION_COMPLETE])
        session_context["user_jids"] = [unicode(info_query.get_from().bare())]
        return (self.add_form_select_accounts(\
                session_context, command_node, lang_class,
                lang_class.command_force_check,
                lang_class.command_force_check_1_description,
                format_as_xml=True, show_user_jid=False), [])

    def execute_force_check_1(self, info_query, session_context,
                              command_node, lang_class):
        self.__logger.debug("Executing command 'force-check' step 1")
        bare_from_jid = info_query.get_from().bare()
        account_name = info_query.get_to().node
        accounts = []
        if account_name is None:
            if session_context.has_key("account_names"):
                for account_name in session_context["account_names"]:
                    name, user_jid = self.get_name_and_jid(account_name)
                    _account = account.get_account(user_jid, name)
                    _account.lastcheck = int(time.time()) \
                        - (_account.interval * self.component.time_unit)
                    accounts.append(_account)
            else:
                return self.execute_force_check_root_node(info_query,
                                                          session_context,
                                                          command_node,
                                                          lang_class)
        else:
            _account = account.get_account(bare_from_jid, account_name)
            if _account is not None:
                _account.lastcheck = int(time.time()) \
                        - (_account.interval * self.component.time_unit)
                accounts.append(_account)
        command_node.setProp("status", command.STATUS_COMPLETED)
        self.component.check_email_accounts(accounts, lang_class)
        return (None, [])

    execute_force_check_2 = execute_force_check_1

    def execute_get_email(self, info_query, session_context,
                          command_node, lang_class):
        self.__logger.debug("Executing command 'get-email' step 1")
        if "fetch_more" in session_context \
                and session_context["fetch_more"][-1] == "0":
            return self.execute_get_email_last(info_query, session_context,
                                               command_node, lang_class)
        else:
            self.add_actions(command_node, [command.ACTION_COMPLETE])
            bare_from_jid = info_query.get_from().bare()
            account_name = info_query.get_to().node
            _account = account.get_account(bare_from_jid, account_name)
            if _account is not None:
                result_form = Form(\
                    xmlnode_or_type="form",
                    title=lang_class.command_get_email,
                    instructions=lang_class.command_get_email_1_description)
                if not "start_index" in session_context:
                    session_context["start_index"] = 1
                self.__logger.debug("Checking email list summary from index "
                                    + str(session_context["start_index"]) + " to "
                                    + str(session_context["start_index"] + 10))
                _account.connect()
                email_list = _account.get_mail_list_summary(\
                    start_index=session_context["start_index"],
                    end_index=session_context["start_index"] + 9)
                _account.disconnect()
                session_context["start_index"] += 10
                field = result_form.add_field(name="emails",
                                              field_type="list-multi",
                                              label=lang_class.field_email_subject)
                for (email_index, email_subject) in email_list:
                    field.add_option(label=email_subject, value=email_index)
                if len(email_list) == 10:
                    result_form.add_field(name="fetch_more",
                                          field_type="boolean",
                                          label=lang_class.field_select_more_emails)
                else:
                    session_context["fetch_more"] = ["0"]
                result_form.as_xml(command_node)
                return (result_form, [])
            else:
                raise CommandError("item-not-found")

    def execute_get_email_last(self, info_query, session_context,
                               command_node, lang_class):
        self.__logger.debug("Executing command 'get-email' last step")
        result = []
        mail_sender = MailSender(self.component)
        bare_from_jid = info_query.get_from().bare()
        account_name = info_query.get_to().node
        _account = account.get_account(bare_from_jid, account_name)
        if _account is not None:
            _account.connect()
            for email_index in session_context["emails"]:
                (email_body, email_from) = _account.get_mail(email_index)
                result.append(\
                    mail_sender.create_full_email_message(\
                        email_from,
                        lang_class.mail_subject % (email_from),
                        email_body,
                        _account))
            _account.disconnect()
            result_form = Form(\
                xmlnode_or_type="form",
                title=lang_class.command_get_email,
                instructions=lang_class.command_get_email_2_description \
                    % (len(session_context["emails"])))
            result_form.as_xml(command_node)
        command_node.setProp("status", command.STATUS_COMPLETED)
        return (None, result)
