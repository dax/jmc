# -*- coding: utf-8 -*-
##
## account.py
## Login : <dax@happycoders.org>
## Started on  Fri Jan 19 18:21:44 2007 David Rousselie
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
import sys
import logging
import email
from email.Header import Header
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
import traceback
import types

import poplib
import imaplib
import socket
import smtplib

from sqlobject.inheritance import InheritableSQLObject
from sqlobject.col import StringCol, IntCol, BoolCol
from sqlobject.sqlbuilder import AND

from jcl.error import FieldError
from jcl.model import account
from jcl.model.account import Account, PresenceAccount
from jmc.lang import Lang

class NoAccountError(Exception):
    """Error raised when no corresponding account is found."""
    pass

def _get_default_status_msg(self, lang_class):
    return str(self.get_type()) + "://" + str(self.login) + "@" + str(self.host) + ":" + \
        unicode(self.port)

def validate_password(password, default_func, bare_from_jid):
    if password is None or password == "":
        return None
    return password

def validate_login(login, default_func, bare_from_jid):
    return account.no_whitespace_field("login", account.mandatory_field("login", login))

def validate_host(host, default_func, bare_from_jid):
    return account.no_whitespace_field("host", account.mandatory_field("host", host))

class MailAccount(PresenceAccount):
    """ Wrapper to mail connection and action.
    Abstract class, do not represent real mail connection type.
    """

    # Define constants
    DIGEST = 1
    RETRIEVE = 2
    default_encoding = "utf-8"
    possibles_actions = [PresenceAccount.DO_NOTHING,
                         DIGEST,
                         RETRIEVE]

    login = StringCol(default="")
    password = StringCol(default=None)
    host = StringCol(default="localhost")
    port = IntCol(default=110)
    # explicitly set dbName to avoid MySQL reserved words
    ssl = BoolCol(default=False, dbName="_ssl")
    interval = IntCol(default=5, dbName="_interval")
    store_password = BoolCol(default=True)
    live_email_only = BoolCol(default=False)

    lastcheck = IntCol(default=0)
    waiting_password_reply = BoolCol(default=False)
    first_check = BoolCol(default=True)

    def _init(self, *args, **kw):
        """MailAccount init
        Initialize class attributes"""
        PresenceAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.MailAccount")
        self.connection = None
        self.connected = False
        self.default_lang_class = Lang.en

    def _get_register_fields(cls, real_class=None):
        """
        See Account._get_register_fields
        """
        if real_class is None:
            real_class = cls
        return PresenceAccount.get_register_fields(real_class) + \
            [("login", "text-single", None,
              validate_login, lambda bare_from_jid: ""),
             ("password", "text-private", None, validate_password,
              lambda bare_from_jid: ""),
             ("host", "text-single", None, validate_host,
              lambda bare_from_jid: ""),
             ("port", "text-single", None,
              account.int_post_func,
              lambda bare_from_jid: real_class.get_default_port()),
             ("ssl", "boolean", None,
              account.boolean_post_func,
              lambda bare_from_jid: False),
             ("store_password", "boolean", None,
              account.boolean_post_func,
              lambda bare_from_jid: True),
             ("live_email_only", "boolean", None,
              account.boolean_post_func,
              lambda bare_from_jid: False),
             ("interval", "text-single", None,
              account.int_post_func,
              lambda bare_from_jid: 5)]

    get_register_fields = classmethod(_get_register_fields)

    def _get_default_port(cls):
        return 42
    get_default_port = classmethod(_get_default_port)

    def _get_presence_actions_fields(cls):
        """See PresenceAccount._get_presence_actions_fields
        """
        return {'chat_action': (cls.possibles_actions,
                                MailAccount.RETRIEVE),
                'online_action': (cls.possibles_actions,
                                  MailAccount.RETRIEVE),
                'away_action': (cls.possibles_actions,
                                MailAccount.DIGEST),
                'xa_action': (cls.possibles_actions,
                              MailAccount.DIGEST),
                'dnd_action': (cls.possibles_actions,
                               MailAccount.DIGEST),
                'offline_action': (cls.possibles_actions,
                                   PresenceAccount.DO_NOTHING)}

    get_presence_actions_fields = classmethod(_get_presence_actions_fields)

    get_default_status_msg = _get_default_status_msg

    def set_status(self, status):
        """Set current Jabber status"""
        if status != account.OFFLINE and self._status == account.OFFLINE:
            PresenceAccount.set_status(self, status)
            self.first_check = True
        self._status = status

    def get_decoded_header(self, header, charset_hint=None):
        decoded_header = email.Header.decode_header(header)
        decoded_header_str = u""
        for i in range(len(decoded_header)):
            try:
                if decoded_header[i][1]:
                    charset_hint = decoded_header[i][1]
                    decoded_header_str += unicode(decoded_header[i][0].decode(\
                            decoded_header[i][1]))
                else:
                    decoded_header_str += unicode(decoded_header[i][0].decode(\
                            MailAccount.default_encoding))
            except Exception,e:
                try:
                    decoded_header_str += unicode(decoded_header[i][0])
                except Exception, e:
                    try:
                        decoded_header_str += unicode(decoded_header[i][0].decode(\
                                "iso-8859-1"))
                    except Exception, e:
                        type, value, stack = sys.exc_info()
                        print >>sys.stderr, \
                            "".join(traceback.format_exception
                                    (type, value, stack, 5))
        return (decoded_header_str, charset_hint)

    def get_decoded_part(self, part, charset_hint):
        content_charset = part.get_content_charset()
        result = u""
        payload = part.get_payload(decode=True)
        try:
            if content_charset:
                result = unicode(payload.decode(content_charset))
            else:
                result = unicode(payload.decode(MailAccount.default_encoding))
        except Exception, e:
            try:
                result = unicode(payload)
            except Exception, e:
                try:
                    result = unicode(payload.decode("iso-8859-1"))
                except Exception, e:
                    if charset_hint is not None:
                        try:
                            result = unicode(payload.decode(charset_hint))
                        except Exception, e:
                            type, value, stack = sys.exc_info()
                            print >>sys.stderr, \
                                "".join(traceback.format_exception
                                        (type, value, stack, 5))

        return result

    def format_message(self, email_msg, include_body=True):
        (email_from, charset_hint) = self.get_decoded_header(email_msg["From"])
        result = u"From : " + email_from + "\n"
        (email_subject, charset_hint) = self.get_decoded_header(email_msg["Subject"],
                                                                charset_hint)
        result += u"Subject : " + email_subject + "\n\n"

        if include_body:
            action = {
                "text/plain" : lambda part: \
                    self.get_decoded_part(part, charset_hint),
                "text/html" : lambda part: "\n<<<HTML part skipped>>>\n"
                }
            for part in email_msg.walk():
                content_type = part.get_content_type()
                if action.has_key(content_type):
                    result += action[content_type](part) + u'\n'
        return (result, email_from)

    def format_message_summary(self, email_msg):
        return self.format_message(email_msg, False)

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def get_mail_list_summary(self, start_index=1, end_index=20):
        raise NotImplementedError

    def get_new_mail_list(self):
        raise NotImplementedError

    def get_mail(self, index):
        raise NotImplementedError

    def get_mail_summary(self, index):
        raise NotImplementedError

    def get_next_mail_index(self, mail_list):
        raise NotImplementedError

    def is_mail_list_valid(self, mail_list):
        return (mail_list and mail_list != [] and mail_list[0] != '')

    def get_type(self):
        raise NotImplementedError

    # Does not modify server state but just internal JMC state
    def mark_all_as_read(self):
        raise NotImplementedError

class IMAPAccount(MailAccount):
    mailbox = StringCol(default="INBOX")
    delimiter = StringCol(default=".")

    def _get_register_fields(cls, real_class=None):
        """See Account._get_register_fields"""
        if real_class is None:
            real_class = cls
        return MailAccount.get_register_fields(real_class) + \
            [("mailbox", "text-single", None,
              account.default_post_func,
              lambda bare_from_jid: "INBOX")]

    get_register_fields = classmethod(_get_register_fields)

    def _get_default_port(cls):
        """Return default IMAP server port"""
        return 143

    get_default_port = classmethod(_get_default_port)

    def _init(self, *args, **kw):
        MailAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.IMAPConnection")
        self._regexp_list = re.compile("\((.*)\) \"(.)\" \"?([^\"]*)\"?$")
        self.__cached_folders = {}

    def get_type(self):
        if self.ssl:
            return "imaps"
        return "imap"

    def _get_real_mailbox(self):
        """
        mailbox attribute is stored with "/" to delimit folders.
        real mailbox is the folder with the delimiter used by the IMAP server
        """
        return self.mailbox.replace("/", self.delimiter)

    def get_status(self):
        return MailAccount.get_status(self) + "/" + self.mailbox

    def connect(self):
        self.__logger.debug("Connecting to IMAP server "
                            + str(self.login) + "@" + str(self.host) + ":" + str(self.port)
                            + " (" + str(self.mailbox) + "). SSL="
                            + str(self.ssl))
        if self.ssl:
            self.connection = imaplib.IMAP4_SSL(self.host, int(self.port))
        else:
            self.connection = imaplib.IMAP4(self.host, int(self.port))
        self.connection.login(self.login, self.password)
        self.connected = True

    def disconnect(self):
        self.__logger.debug("Disconnecting from IMAP server "
                            + self.host)
        self.connection.logout()
        self.connected = False

    def get_mail_list_summary(self, start_index=1, end_index=20):
        """
        Get a list of emails starting from start_index and ending at end_index
        of tuple (email_index, email_subject)
        """
        self.__logger.debug("Getting mail list summary")
        typ, data = self.connection.select(self._get_real_mailbox(), True)
        if typ == "OK":
            typ, data = self.connection.fetch(str(start_index) + ":" +
                                              str(end_index),
                                              "RFC822.header")
            if typ == 'OK':
                result = []
                index = start_index
                for _email in data:
                    if isinstance(_email, types.TupleType) and len(_email) == 2:
                        subject_header = self.get_decoded_header(email.message_from_string(_email[1])["Subject"])[0]
                        result.append((str(index), subject_header))
                        index += 1
                return result
        raise Exception(data[0])

    def get_new_mail_list(self):
        """
        Get a list of new emails indexes
        """
        self.__logger.debug("Getting mail list")
        typ, data = self.connection.select(self._get_real_mailbox())
        if typ == 'OK':
            typ, data = self.connection.search(None, 'RECENT')
            if typ == 'OK':
                return data[0].split(' ')
        raise Exception(data[0])

    def get_mail(self, index):
        self.__logger.debug("Getting mail " + str(index))
        typ, data = self.connection.select(self._get_real_mailbox(), True)
        if typ == 'OK':
            typ, data = self.connection.fetch(index, '(RFC822)')
            if typ == 'OK':
                return self.format_message(\
                    email.message_from_string(data[0][1]))
        raise Exception(str(data[0]) + " (email " + str(index) + ")")

    def get_mail_summary(self, index):
        self.__logger.debug("Getting mail summary " + str(index))
        typ, data = self.connection.select(self._get_real_mailbox(), True)
        if typ == 'OK':
            typ, data = self.connection.fetch(index, '(RFC822.header)')
            if typ == 'OK':
                return self.format_message_summary(\
                    email.message_from_string(data[0][1]))
        raise Exception(str(data[0]) + " (email " + str(index) + ")")

    def get_next_mail_index(self, mail_list):
        """
        Mail indexes generator. Return mail_list elements and destroy them
        when returned.
        """
        while self.is_mail_list_valid(mail_list):
            yield mail_list.pop(0)
        return

    def mark_all_as_read(self):
        self.get_new_mail_list()

    type = property(get_type)

    def _add_full_path_to_cache(self, folder_array):
        current_dir = self.__cached_folders
        for folder in folder_array:
            if not current_dir.has_key(folder):
                current_dir[folder] = {}
            current_dir = current_dir[folder]

    def _build_folder_cache(self):
        if self.connected:
            typ, data = self.connection.list()
            if typ == 'OK':
                for line in data:
                    match = self._regexp_list.match(line)
                    if match is not None:
                        delimiter = match.group(2)
                        subdir = match.group(3).split(delimiter)
                        self._add_full_path_to_cache(subdir)
        return self.__cached_folders

    def ls_dir(self, imap_dir):
        """
        imap_dir: IMAP directory to list. subdirs must be delimited by '/'
        """
        self.__logger.debug("Listing IMAP dir '" + str(imap_dir) + "'")
        if self.__cached_folders == {}:
            if not self.connected:
                self.connect()
            self._build_folder_cache()
            self.disconnect()
        if imap_dir == "":
            folder_array = []
        else:
            folder_array = imap_dir.split('/')
        current_folder = self.__cached_folders
        for folder in folder_array:
            if not current_folder.has_key(folder):
                return []
            else:
                current_folder = current_folder[folder]
        return current_folder.keys()

    def populate_handler(self, try_other_delimiter=True, testing_delimiter="/"):
        """
        Handler called when populating account
        """
        # Get delimiter
        if not self.connected:
            self.connect()
        typ, data = self.connection.list(self.mailbox)
        if typ == 'OK':
            line = data[0]
            if line is None:
                if try_other_delimiter:
                    self.mailbox = self.mailbox.replace(testing_delimiter,
                                                        ".")
                    self.populate_handler(False, ".")
                    return
                else:
                    self.disconnect()
                    raise Exception("Cannot find mailbox " + str(self.mailbox))
            else:
                match = self._regexp_list.match(line)
                if match is not None:
                    self.delimiter = match.group(2)
                else:
                    self.disconnect()
                    raise Exception("Cannot find delimiter for mailbox "
                                    + str(self.mailbox))
        else:
            self.disconnect()
            raise Exception("Cannot find mailbox " + str(self.mailbox))
        self.disconnect()
        # replace any previous delimiter in self.mailbox by "/"
        if self.delimiter != testing_delimiter:
            self.mailbox = self.mailbox.replace(testing_delimiter,
                                                self.delimiter)


class POP3Account(MailAccount):
    nb_mail = IntCol(default=0)
    lastmail = IntCol(default=0)

    def _init(self, *args, **kw):
        MailAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.POP3Account")
        self.connected = False

    def _get_default_port(cls):
        """Return default POP3 server port"""
        return 110

    get_default_port = classmethod(_get_default_port)

    def get_type(self):
        if self.ssl:
            return "pop3s"
        return "pop3"

    type = property(get_type)

    def connect(self):
        self.__logger.debug("Connecting to POP3 server "
                            + str(self.login) + "@" + str(self.host) + ":" +
                            str(self.port) + ". SSL=" + str(self.ssl))
        if self.ssl:
            self.connection = poplib.POP3_SSL(self.host, int(self.port))
        else:
            self.connection = poplib.POP3(self.host, int(self.port))
        try:
            self.connection.apop(self.login, self.password)
        except:
            self.connection.user(self.login)
            self.connection.pass_(self.password)
        self.connected = True


    def disconnect(self):
        self.__logger.debug("Disconnecting from POP3 server " + str(self.host))
        self.connection.quit()
        self.connected = False

    def get_mail_list_summary(self, start_index=1, end_index=20):
        self.__logger.debug("Getting mail list")
        count, size = self.connection.stat()
        result = []
        if count < end_index:
            end_index = count
        for index in xrange(start_index, end_index + 1):
            (ret, data, octets) = self.connection.top(index, 0)
            if ret[0:3] == '+OK':
                subject_header = self.get_decoded_header(email.message_from_string('\n'.join(data))["Subject"])[0]
                result.append((str(index), subject_header))
        try:
            self.connection.rset()
        except:
            pass
        return result

    def get_new_mail_list(self):
        self.__logger.debug("Getting new mail list")
        count, size = self.connection.stat()
        self.nb_mail = count
        return [str(i) for i in range(1, count + 1)]

    def get_mail(self, index):
        self.__logger.debug("Getting mail " + str(index))
        ret, data, size = self.connection.retr(index)
        try:
            self.connection.rset()
        except:
            pass
        if ret[0:3] == '+OK':
            return self.format_message(email.message_from_string(\
                    '\n'.join(data)))
        return u"Error while fetching mail " + str(index)

    def get_mail_summary(self, index):
        self.__logger.debug("Getting mail summary " + str(index))
        ret, data, size = self.connection.retr(index)
        try:
            self.connection.rset()
        except:
            pass
        if ret[0:3] == '+OK':
            return self.format_message_summary(email.message_from_string(\
                    '\n'.join(data)))
        return u"Error while fetching mail " + str(index)

    def get_next_mail_index(self, mail_list):
        """
        Return next mail index to be read. mail_list is a generated list of
        mail indexes in the mailbox. If the mailbox has been check by another
        client, self.nb_mail should be < to self.lastmail (last mail_list
        index that has been returned), so self.lastmail is set to 0 to return
        indexes from the begining of the mail_list array. If the mailbox has
        not been checked by another client since last check from JMC, then
        only new email indexes of mail_list should be returned. self.lastmail
        sill contains old nb_mail value (it has stop at this value in the last
        check) and self.nb_mail contains the new count of new emails:
        ex:
        - First check
        [1, 2, 3, 4, 5, 6, 7]
         ^                 ^
         |                 |
         self.lastmail     self.nb_mail
        - end of first check
        [1, 2, 3, 4, 5, 6, 7]
                           ^
                           |
                           self.nb_mail == self.lastmail
        - second check (no check by another client)
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
                           ^                     ^
                           |                     |
                           self.lastmail         self.nb_mail
        Only emails indexes form 8 to 13 are returned
        - a checking done by another client is dectected only if self.nb_mail
        become < to self.lastmail. If the number of new emails is superior to
        self.lastmail after another client has check the mailbox, emails
        indexes from 0 to self.lastmail are not sent through JMC.
        """
        while self.nb_mail != self.lastmail:
            if self.nb_mail < self.lastmail:
                self.lastmail = 0
            result = int(mail_list[self.lastmail])
            self.lastmail += 1
            yield result
        return

    def mark_all_as_read(self):
        self.get_new_mail_list()
        self.lastmail = self.nb_mail

class AbstractSMTPAccount(Account):
    """Common SMTP attribut"""
    default_from = StringCol(default="nobody@localhost")
    default_account = BoolCol(default=False)

    def _init(self, *args, **kw):
        """SMTPAccount init
        Initialize class attributes"""
        Account._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.AbstractSMTPAccount")

    def get_type(self):
        if self.tls:
            return "smtps"
        return "smtp"

    type = property(get_type)

    def create_email(self, from_email, to_email, subject, body, other_headers=None):
        """Create new email"""
        _email = MIMEText(body)
        if subject is None:
            subject = ""
        _email['Subject'] = Header(str(subject))
        _email['From'] = Header(str(from_email))
        _email['To'] = Header(str(to_email))
        if other_headers is not None:
            for header_name in other_headers.keys():
                _email[header_name] = Header(other_headers[header_name])
        return _email

    def _get_register_fields (cls, real_class=None):
        """ """
        def default_account_default_func(bare_from_jid):
            accounts = account.get_accounts(bare_from_jid, AbstractSMTPAccount,
                                            (AbstractSMTPAccount.q.default_account == True))
            if accounts.count() == 0:
                return True
            else:
                return False

        def default_account_post_func(value, default_func, bare_from_jid):
            accounts = account.get_accounts(bare_from_jid, AbstractSMTPAccount,
                                            (AbstractSMTPAccount.q.default_account == True))
            already_default_account = (accounts.count() != 0)
            if isinstance(value, str) or isinstance(value, unicode):
                value = value.lower()
                bool_value = (value == "true" or value == "1")
            else:
                bool_value = value
            if bool_value:
                if already_default_account:
                    for _account in accounts:
                        _account.default_account = False
                return True
            else:
                if not already_default_account:
                    return True
                else:
                    return False

        if real_class is None:
            real_class = cls
        return Account.get_register_fields(real_class) + \
            [("default_account", "boolean", None,
              default_account_post_func,
              default_account_default_func),
             ("default_from", "text-single", None,
              lambda field_value, default_func, bare_from_jid: \
                  account.mandatory_field("default_from", field_value),
              lambda bare_from_jid: "")]

    get_register_fields = classmethod(_get_register_fields)

smtp_default_login = None
smtp_default_password = None
smtp_default_host = "localhost"
smtp_default_port = 25
smtp_default_tls = False
smtp_default_ssl = False

class GlobalSMTPAccount(AbstractSMTPAccount):
    """SMTP Account to send email with global settings"""
    login = StringCol(default=lambda: smtp_default_login)
    password = StringCol(default=lambda: smtp_default_password)
    host = StringCol(default=lambda: smtp_default_host)
    port = IntCol(default=lambda: smtp_default_port)
    tls = BoolCol(default=lambda: smtp_default_tls)
    ssl = BoolCol(default=lambda: smtp_default_ssl, dbName="_ssl")
    store_password = BoolCol(default=True)
    waiting_password_reply = BoolCol(default=False)

    def _init(self, *args, **kw):
        """SMTPAccount init
        Initialize class attributes"""
        AbstractSMTPAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.GlobalSMTPAccount")

    def _get_register_fields(cls, real_class=None):
        """See Account._get_register_fields
        """
        if real_class is None:
            real_class = cls
        return AbstractSMTPAccount.get_register_fields(real_class)

    get_register_fields = classmethod(_get_register_fields)

    get_default_status_msg = _get_default_status_msg

    def __say_hello(self, connection):
        if not (200 <= connection.ehlo()[0] <= 299):
            (code, resp) = connection.helo()
            if not (200 <= code <= 299):
                raise SMTPHeloError(code, resp)

    def send_email(self, _email):
        """Send email according to current account parameters"""
        self.__logger.debug("Sending email:\n"
                            + str(_email))
        if self.ssl:
            smtp_connection = smtplib.SMTP_SSL()
        else:
            smtp_connection = smtplib.SMTP()
        if self.__logger.getEffectiveLevel() == logging.DEBUG:
            smtp_connection.set_debuglevel(1)
	# It seems there is a bug that set self.port to something that is
	# not an integer. How ? Here is a temporary workaround.
        from types import IntType
        if type(self.port) != IntType:
            self.__logger.debug("BUG: SMTPAccount.port is not an integer: "
                                + str(type(self.port)) + ", value: "
                                + str(self.port))
            self.port = int(self.port)
        smtp_connection.connect(self.host, int(self.port))
        self.__say_hello(smtp_connection)
        if self.tls:
            smtp_connection.starttls()
            self.__say_hello(smtp_connection)
        if self.login is not None and len(self.login) > 0:
            auth_methods = smtp_connection.esmtp_features["auth"].split()
            auth_methods.reverse()
            current_error = None
            for auth_method in auth_methods:
                self.__logger.debug("Trying to authenticate using "
                                    + str(auth_method) + " method")
                smtp_connection.esmtp_features["auth"] = auth_method
                try:
                    smtp_connection.login(self.login, self.password)
                    current_error = None
                    self.__logger.debug("Successfuly to authenticate using "
                                        + str(auth_method) + " method")
                    break
                except (smtplib.SMTPAuthenticationError, smtplib.SMTPException), error:
                    self.__logger.debug("Failed to authenticate using "
                                        + str(auth_method) + " method")
                    current_error = error
            if current_error is not None:
                raise current_error
        smtp_connection.sendmail(str(_email['From']), str(_email['To']),
                                 _email.as_string())
        smtp_connection.quit()

class SMTPAccount(GlobalSMTPAccount):
    """Send email account"""

    def _init(self, *args, **kw):
        """SMTPAccount init
        Initialize class attributes"""
        GlobalSMTPAccount._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.SMTPAccount")

    def _get_register_fields(cls, real_class=None):
        """See Account._get_register_fields
        """
        def password_post_func(password, default_func, bare_from_jid):
            if password is None or password == "":
                return None
            return password

        if real_class is None:
            real_class = cls
        return GlobalSMTPAccount.get_register_fields(real_class) + \
            [("login", "text-single", None,
              account.default_post_func,
              lambda bare_from_jid: smtp_default_login),
             ("password", "text-private", None, password_post_func,
              lambda bare_from_jid: smtp_default_password),
             ("host", "text-single", None,
              lambda field_value, default_func, bare_from_jid: \
                  account.mandatory_field("host", field_value),
              lambda bare_from_jid: smtp_default_host),
             ("port", "text-single", None,
              account.int_post_func,
              lambda bare_from_jid: smtp_default_port),
             ("tls", "boolean", None,
              account.boolean_post_func,
              lambda bare_from_jid: smtp_default_tls),
             ("ssl", "boolean", None,
              account.boolean_post_func,
              lambda bare_from_jid: smtp_default_ssl),
             ("store_password", "boolean", None,
              account.boolean_post_func,
              lambda bare_from_jid: True)]

    get_register_fields = classmethod(_get_register_fields)
