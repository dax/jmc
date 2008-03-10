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

from jcl.model import account
from jcl.model.account import Account, PresenceAccount
from jmc.lang import Lang

IMAP4_TIMEOUT = 10
POP3_TIMEOUT = 10

class NoAccountError(Exception):
    """Error raised when no corresponding account is found."""
    pass

## All MY* classes are implemented to add a timeout (settimeout)
## while connecting
class MYIMAP4(imaplib.IMAP4):
    def open(self, host='', port=imaplib.IMAP4_PORT):
        """Setup connection to remote server on "host:port"
            (default: localhost:standard IMAP4 port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self.sock.settimeout(IMAP4_TIMEOUT)
        self.sock.connect((host, port))
	self.sock.settimeout(None)
        self.file = self.sock.makefile('rb')

class MYIMAP4_SSL(imaplib.IMAP4_SSL):
    def open(self, host='', port=imaplib.IMAP4_SSL_PORT):
        """Setup connection to remote server on "host:port".
            (default: localhost:standard IMAP4 SSL port).
        This connection will be used by the routines:
            read, readline, send, shutdown.
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	self.sock.settimeout(IMAP4_TIMEOUT)
        self.sock.connect((host, port))
	self.sock.settimeout(None)
        self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)

class MYPOP3(poplib.POP3):
    def __init__(self, host, port=poplib.POP3_PORT):
        self.host = host
        self.port = port
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host,
                                      self.port,
                                      0,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
		self.sock.settimeout(POP3_TIMEOUT)
                self.sock.connect(sa)
		self.sock.settimeout(None)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
        self.file = self.sock.makefile('rb')
        self._debugging = 0
        self.welcome = self._getresp()

class MYPOP3_SSL(poplib.POP3_SSL):
    def __init__(self, host, port=poplib.POP3_SSL_PORT, keyfile=None,
                 certfile=None):
        self.host = host
        self.port = port
        self.keyfile = keyfile
        self.certfile = certfile
        self.buffer = ""
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, 0,
                                      socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            try:
                self.sock = socket.socket(af, socktype, proto)
		self.sock.settimeout(POP3_TIMEOUT)
                self.sock.connect(sa)
		self.sock.settimeout(None)
            except socket.error, msg:
                if self.sock:
                    self.sock.close()
                self.sock = None
                continue
            break
        if not self.sock:
            raise socket.error, msg
        self.file = self.sock.makefile('rb')
        self.sslobj = socket.ssl(self.sock, self.keyfile, self.certfile)
        self._debugging = 0
        self.welcome = self._getresp()

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
        """See Account._get_register_fields
        """
        def password_post_func(password, default_func, bare_from_jid):
            if password is None or password == "":
                return None
            return password

        if real_class is None:
            real_class = cls
        return PresenceAccount.get_register_fields(real_class) + \
            [("login", "text-single", None,
              lambda field_value, default_func, bare_from_jid: \
                  account.mandatory_field("login", field_value),
              lambda bare_from_jid: ""),
             ("password", "text-private", None, password_post_func,
              lambda bare_from_jid: ""),
             ("host", "text-single", None,
              lambda field_value, default_func, bare_from_jid: \
                  account.mandatory_field("host", field_value),
              lambda bare_from_jid: ""),
             ("port", "text-single", None,
              account.int_post_func,
              lambda bare_from_jid: real_class.get_default_port()),
             ("ssl", "boolean", None,
              account.default_post_func,
              lambda bare_from_jid: False),
             ("store_password", "boolean", None,
              account.default_post_func,
              lambda bare_from_jid: True),
             ("live_email_only", "boolean", None,
              account.default_post_func,
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

    def get_default_status_msg(self, lang_class):
        return self.get_type() + "://" + self.login + "@" + self.host + ":" + \
	    unicode(self.port)

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
        """See Account._get_register_fields
        """
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
                            + self.login + "@" + self.host + ":" + str(self.port)
                            + " (" + self.mailbox + "). SSL="
                            + str(self.ssl))
        if self.ssl:
            self.connection = MYIMAP4_SSL(self.host, self.port)
        else:
            self.connection = MYIMAP4(self.host, self.port)
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
        typ, count = self.connection.select(self._get_real_mailbox(), True)
        result = []
        if typ == "OK":
            typ, data = self.connection.fetch(str(start_index) + ":" +
                                              str(end_index),
                                              "RFC822.header")
            if typ == 'OK':
                index = start_index
                for _email in data:
                    if isinstance(_email, types.TupleType) and len(_email) == 2:
                        subject_header = self.get_decoded_header(email.message_from_string(_email[1])["Subject"])[0]
                        result.append((str(index), subject_header))
                        index += 1
        return result

    def get_new_mail_list(self):
        """
        Get a list of new emails indexes
        """
        self.__logger.debug("Getting mail list")
        typ, data = self.connection.select(self._get_real_mailbox())
        typ, data = self.connection.search(None, 'RECENT')
        if typ == 'OK':
            return data[0].split(' ')
        return None

    def get_mail(self, index):
        self.__logger.debug("Getting mail " + str(index))
        typ, data = self.connection.select(self._get_real_mailbox(), True)
        typ, data = self.connection.fetch(index, '(RFC822)')
        if typ == 'OK':
            return self.format_message(\
                email.message_from_string(data[0][1]))
        return u"Error while fetching mail " + str(index)

    def get_mail_summary(self, index):
        self.__logger.debug("Getting mail summary " + str(index))
        typ, data = self.connection.select(self._get_real_mailbox(), True)
        typ, data = self.connection.fetch(index, '(RFC822.header)')
        if typ == 'OK':
            return self.format_message_summary(\
                email.message_from_string(data[0][1]))
        return u"Error while fetching mail " + str(index)

    def get_next_mail_index(self, mail_list):
        if self.is_mail_list_valid(mail_list):
            return mail_list.pop(0)
        else:
            return None

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

    def populate_handler(self):
        """
        Handler called when populating account
        """
        # Get delimiter
        if not self.connected:
            self.connect()
        typ, data = self.connection.list(self.mailbox)
        if typ == 'OK':
            line = data[0]
            match = self._regexp_list.match(line)
            if match is not None:
                self.delimiter = match.group(2)
            else:
                self.disconnect()
                raise Exception("Cannot find delimiter for mailbox "
                                + self.mailbox)
        else:
            self.disconnect()
            raise Exception("Cannot find mailbox " + self.mailbox)
        self.disconnect()
        # replace any previous delimiter in self.mailbox by "/"
        if self.delimiter != "/":
            self.mailbox = self.mailbox.replace(self.delimiter, "/")
            

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
                            + self.login + "@" + self.host + ":" +
                            str(self.port) + ". SSL=" + str(self.ssl))
        if self.ssl:
            self.connection = MYPOP3_SSL(self.host, self.port)
        else:
            self.connection = MYPOP3(self.host, self.port)
        try:
            self.connection.apop(self.login, self.password)
        except:
            self.connection.user(self.login)
            self.connection.pass_(self.password)
        self.connected = True


    def disconnect(self):
        self.__logger.debug("Disconnecting from POP3 server " + self.host)
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
        if self.is_mail_list_valid(mail_list):
            if self.nb_mail == self.lastmail:
                return None
            if self.nb_mail < self.lastmail:
                self.lastmail = 0
            result = int(mail_list[self.lastmail])
            self.lastmail += 1
            return result
        else:
            return None

    def mark_all_as_read(self):
        self.get_new_mail_list()
        self.lastmail = self.nb_mail


class SMTPAccount(Account):
    """Send email account"""

    login = StringCol(default="")
    password = StringCol(default=None)
    host = StringCol(default="localhost")
    port = IntCol(default=110)
    tls = BoolCol(default=False)
    store_password = BoolCol(default=True)
    waiting_password_reply = BoolCol(default=False)
    default_from = StringCol(default="nobody@localhost")
    default_account = BoolCol(default=False)

    def _init(self, *args, **kw):
        """SMTPAccount init
        Initialize class attributes"""
        Account._init(self, *args, **kw)
        self.__logger = logging.getLogger("jmc.model.account.SMTPAccount")

    def _get_default_port(cls):
        """Return default SMTP server port"""
        return 25

    get_default_port = classmethod(_get_default_port)

    def _get_register_fields(cls, real_class=None):
        """See Account._get_register_fields
        """
        def password_post_func(password, default_func, bare_from_jid):
            if password is None or password == "":
                return None
            return password

        def default_account_default_func(bare_from_jid):
            accounts = account.get_accounts(bare_from_jid, SMTPAccount,
                                            (SMTPAccount.q.default_account == True))
            if accounts.count() == 0:
                return True
            else:
                return False

        def default_account_post_func(value, default_func, bare_from_jid):
            accounts = account.get_accounts(bare_from_jid, SMTPAccount,
                                            (SMTPAccount.q.default_account == True))
            already_default_account = (accounts.count() != 0)
            if isinstance(value, str):
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
            [("login", "text-single", None,
              account.default_post_func,
              lambda bare_from_jid: ""),
             ("password", "text-private", None, password_post_func,
              lambda bare_from_jid: ""),
             ("host", "text-single", None,
              lambda field_value, default_func, bare_from_jid: \
                  account.mandatory_field("host", field_value),
              lambda bare_from_jid: ""),
             ("port", "text-single", None,
              account.int_post_func,
              lambda bare_from_jid: real_class.get_default_port()),
             ("tls", "boolean", None,
              account.default_post_func,
              lambda bare_from_jid: False),
             ("default_from", "text-single", None,
              lambda field_value, default_func, bare_from_jid: \
                  account.mandatory_field("default_from", field_value),
              lambda bare_from_jid: ""),
             ("store_password", "boolean", None,
              account.default_post_func,
              lambda bare_from_jid: True),
             ("default_account", "boolean", None,
              default_account_post_func,
              default_account_default_func)]

    get_register_fields = classmethod(_get_register_fields)

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

    def __say_hello(self, connection):
        if not (200 <= connection.ehlo()[0] <= 299):
            (code, resp) = connection.helo()
            if not (200 <= code <= 299):
                raise SMTPHeloError(code, resp)

    def send_email(self, _email):
        """Send email according to current account parameters"""
        self.__logger.debug("Sending email:\n"
                            + str(_email))
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

        smtp_connection.connect(self.host, self.port)
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
                                    + auth_method + " method")
                smtp_connection.esmtp_features["auth"] = auth_method
                try:
                    smtp_connection.login(self.login, self.password)
                    current_error = None
                    self.__logger.debug("Successfuly to authenticate using "
                                        + auth_method + " method")
                    break
                except smtplib.SMTPAuthenticationError, error:
                    self.__logger.debug("Failed to authenticate using "
                                        + auth_method + " method")
                    current_error = error
            if current_error is not None:
                raise current_error
        smtp_connection.sendmail(str(_email['From']), str(_email['To']),
                                 _email.as_string())
        smtp_connection.quit()
