##
## mailconnection.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Fri Jan  7 11:06:42 2005 
## $Id: mailconnection.py,v 1.11 2005/09/18 20:24:07 dax Exp $
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


import sys
import email
import email.Header

import poplib
import imaplib
import socket

IMAP4_TIMEOUT = 10
POP3_TIMEOUT = 10

DO_NOTHING = 0
DIGEST = 1
RETRIEVE = 2
## All MY* classes are implemented to add a timeout (settimeout)
## while connecting
class MYIMAP4(imaplib.IMAP4):
    def open(self, host = '', port = imaplib.IMAP4_PORT):
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
    def open(self, host = '', port = imaplib.IMAP4_SSL_PORT):
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
    def __init__(self, host, port = poplib.POP3_PORT):
        self.host = host
        self.port = port
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
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
    def __init__(self, host, port = poplib.POP3_SSL_PORT, keyfile = None, certfile = None):
        self.host = host
        self.port = port
        self.keyfile = keyfile
        self.certfile = certfile
        self.buffer = ""
        msg = "getaddrinfo returns an empty list"
        self.sock = None
        for res in socket.getaddrinfo(self.host, self.port, 0, socket.SOCK_STREAM):
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

class MailConnection(object):
    """ Wrapper to mail connection and action.
    Abstract class, do not represent real mail connection type"""

    def __init__(self, login = "", password = "", host = "", \
		 port = 110, ssl = False):
	""" Initialize MailConnection object for common parameters of all
	connections types

	:Parameters:
	- 'login': login used to connect mail server
	- 'password': password associated with 'login' to connect mail server
	- 'host': mail server hostname
	- 'port': mail server port
	- 'ssl': activate ssl to connect server

	:Types:
	- 'login': string
	- 'password': string
	- 'host': string
	- 'port': int
	- 'ssl': boolean"""
	self.login = login
	self.password = password
	self.host = host
	self.port = port
	self.ssl = ssl
	self.lastcheck = 0
        self.status = "offline"
	self.connection = None
        self.chat_action = RETRIEVE
        self.online_action = RETRIEVE
        self.away_action = RETRIEVE
        self.xa_action = RETRIEVE
        self.dnd_action = RETRIEVE
        self.offline_action = DO_NOTHING
        self.interval = 5
        
    def __eq__(self, other):
        return self.get_type() == other.get_type() \
               and self.login == other.login \
               and self.password == other.password \
               and self.host == other.host \
               and self.port == other.port \
               and self.ssl == other.ssl \
               and self.chat_action == other.chat_action \
               and self.online_action == other.online_action \
               and self.away_action == other.away_action \
               and self.xa_action == other.xa_action \
               and self.dnd_action == other.dnd_action \
               and self.offline_action == other.offline_action \
               and self.interval == other.interval
    
    def __str__(self):
	return self.get_type() + "#" + self.login + "#" + self.password + "#" \
	    + self.host + "#" + str(self.port) + "#" + str(self.chat_action) + "#" \
            + str(self.online_action) + "#" + str(self.away_action) + "#" + \
            str(self.xa_action) + "#" + str(self.dnd_action) + "#" + str(self.offline_action)
 
    def get_decoded_part(self, part):
        content_charset = part.get_content_charset()
        if content_charset:
            return part.get_payload(decode=True).decode(content_charset)
        else:
            return part.get_payload(decode=True)
            
    def format_message(self, email_msg, include_body = True):
        from_decoded = email.Header.decode_header(email_msg["From"])
        result = u"From : "
        for i in range(len(from_decoded)):
            if from_decoded[i][1]:
                result += from_decoded[i][0].decode(from_decoded[i][1])
            else:
                result += from_decoded[i][0]
        result += "\n"

        subject_decoded = email.Header.decode_header(email_msg["Subject"])
        result += u"Subject : "
        for i in range(len(subject_decoded)):
            if subject_decoded[i][1]:
                result += subject_decoded[i][0].decode(subject_decoded[i][1])
            else:
                result += subject_decoded[i][0]
        result += "\n\n"

        if include_body:
            action = {
                "text/plain" : lambda part: self.get_decoded_part(part),
                "text/html" : lambda part: "\n<<<HTML part skipped>>>\n"
                }
            for part in email_msg.walk():
                content_type = part.get_content_type()
                if action.has_key(content_type):
                    result += action[content_type](part) + '\n'
        return result

    def format_message_summary(self, email_msg):
        return self.format_message(email_msg, False)
        
    def get_type(self):
	return "UNKNOWN"

    def get_status_msg(self):
	return self.get_type() + "://" + self.login + "@" + self.host + ":" + \
	    str(self.port)

    def connect(self):
	pass

    def disconnect(self):
	pass

    def get_mail_list(self):
	return 0

    def get_mail(self, index):
	return None

    def get_mail_summary(self, index):
	return None

    def get_action(self):
        mapping = {"online": self.online_action,
                   "chat": self.chat_action,
                   "away": self.away_action,
                   "xa": self.xa_action,
                   "dnd": self.dnd_action,
                   "offline": self.offline_action}
        if mapping.has_key(self.status):
            return mapping[self.status]
        return NOTHING
        
    action = property(get_action)
    
class IMAPConnection(MailConnection):
    def __init__(self, login = "", password = "", host = "", \
		 port = None, ssl = False, mailbox = "INBOX"):
	if not port:
	    if ssl:
		port = 993
	    else:
		port = 143
	MailConnection.__init__(self, login, password, host, port, ssl)
	self.mailbox = mailbox

    def __eq__(self, other):
        return MailConnection.__eq__(self, other) \
               and self.mailbox == other.mailbox
    
    def __str__(self):
	return MailConnection.__str__(self) + "#" + self.mailbox

    def get_type(self):
	if self.ssl:
	    return "imaps"
	return "imap"
	    
    def get_status(self):
	return MailConnection.get_status(self) + "/" + self.mailbox

    def connect(self):
	print >>sys.stderr, "Connecting to IMAP server " \
	    + self.login + "@" + self.host + ":" + str(self.port) \
	    + " (" + self.mailbox + "). SSL=" \
	    + str(self.ssl)
	if self.ssl:
	    self.connection = MYIMAP4_SSL(self.host, self.port)
	else:
	    self.connection = MYIMAP4(self.host, self.port)
	self.connection.login(self.login, self.password)

    def disconnect(self):
	print >>sys.stderr, "Disconnecting from IMAP server " \
	    + self.host
	self.connection.logout()

    def get_mail_list(self):
	print >>sys.stderr, "Getting mail list"
	typ, data = self.connection.select(self.mailbox)
	typ, data = self.connection.search(None, 'UNSEEN')
	if typ == 'OK':
	    return data[0].split(' ')
	return None

    def get_mail(self, index):
	print >>sys.stderr, "Getting mail " + str(index)
	typ, data = self.connection.select(self.mailbox)
	typ, data = self.connection.fetch(index, '(RFC822)')
	self.connection.store(index, "FLAGS", "UNSEEN")
	if typ == 'OK':
            return self.format_message(email.message_from_string(data[0][1]))
	return u"Error while fetching mail " + str(index)
	
    def get_mail_summary(self, index):
	print >>sys.stderr, "Getting mail summary " + str(index)
	typ, data = self.connection.select(self.mailbox)
	typ, data = self.connection.fetch(index, '(RFC822)')
	self.connection.store(index, "FLAGS", "UNSEEN")
	if typ == 'OK':
            return self.format_message_summary(email.message_from_string(data[0][1]))
	return u"Error while fetching mail " + str(index)

class POP3Connection(MailConnection):
    def __init__(self, login = "", password = "", host = "", \
		 port = None, ssl = False):
	if not port:
	    if ssl:
		port = 995
	    else:
		port = 110
	MailConnection.__init__(self, login, password, host, port, ssl)

    def get_type(self):
	if self.ssl:
	    return "pop3s"
	return "pop3"

    def connect(self):
	print >>sys.stderr, "Connecting to POP3 server " \
	    + self.login + "@" + self.host + ":" + str(self.port)\
	    + ". SSL=" + str(self.ssl)
	if self.ssl:
	    self.connection = MYPOP3_SSL(self.host, self.port)
	else:
	    self.connection = MYPOP3(self.host, self.port)
	try:
	  self.connection.apop(self.login, self.password)
	except:
	  self.connection.user(self.login)
	  self.connection.pass_(self.password)
	

    def disconnect(self):
	print >>sys.stderr, "Disconnecting from POP3 server " \
	    + self.host
	self.connection.quit()

    def get_mail_list(self):
	print >>sys.stderr, "Getting mail list"
	count, size = self.connection.stat()
	return [str(i) for i in range(1, count + 1)]

    def get_mail(self, index):
	print >>sys.stderr, "Getting mail " + str(index)
	ret, data, size = self.connection.retr(index)
	if ret[0:3] == '+OK':
            return self.format_message(email.message_from_string('\n'.join(data)))
	return u"Error while fetching mail " + str(index)

    def get_mail_summary(self, index):
	print >>sys.stderr, "Getting mail summary " + str(index)
	ret, data, size = self.connection.retr(index)
	if ret[0:3] == '+OK':
            return self.format_message_summary(email.message_from_string('\n'.join(data)))
	return u"Error while fetching mail " + str(index)
