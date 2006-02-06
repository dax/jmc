# -*- coding: UTF-8 -*-
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

import re
import signal
import threading
import thread
import logging
import sys
import anydbm
import os
import time
import traceback

import mailconnection
from mailconnection import *
from x import *
from storage import *
import mailconnection_factory
import pyxmpp.jabberd
from pyxmpp.presence import Presence
from pyxmpp.message import Message
from pyxmpp.streambase import StreamError, FatalStreamError
from pyxmpp.jid import JID
from pyxmpp.jabber.disco import DiscoItems, DiscoItem, DiscoInfo, DiscoIdentity
from pyxmpp.jabberd.component import Component

from jabber.lang import Lang

class ComponentFatalError(RuntimeError):
    pass

class MailComponent(Component):
    def __init__(self,
                 jid,
                 secret,
                 server,
                 port,
                 default_lang,
                 check_interval,
                 spool_dir,
                 storage,
                 name):
	Component.__init__(self, \
                           JID(jid), \
                           secret, \
                           server, \
                           port, \
                           disco_category = "gateway", \
                           disco_type = "headline")
 	self.__logger = logging.getLogger("jabber.Component")
	self.__shutdown = 0
        self.__lang = Lang(default_lang)
        self.__name = name
        
	signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
	
	self.__interval = check_interval
        spool_dir += "/" + jid
        try:
            self.__storage = globals()[storage \
                                       + "Storage"](2, spool_dir = spool_dir)
        except:
            print >>sys.stderr, "Cannot find " \
                  + storage + "Storage class"
            sys.exit(1)
	# dump registered accounts (save) every hour
	self.__count = 60
        self.running = False

    def __del__(self):
        logging.shutdown()

    """ Register Form creator """
    def get_reg_form(self, lang_class):
        reg_form = X()
        reg_form.xmlns = "jabber:x:data"
        reg_form.title = lang_class.register_title
        reg_form.instructions = lang_class.register_instructions
        reg_form.type = "form"
        
        reg_form.add_field(type = "text-single", \
                           label = lang_class.account_name, \
                           var = "name")
        
        reg_form.add_field(type = "text-single", \
                           label = lang_class.account_login, \
                           var = "login")
        
        reg_form.add_field(type = "text-private", \
                           label = lang_class.account_password, \
                           var = "password")

        reg_form.add_field(type = "boolean", \
                           label = lang_class.account_password_store, \
                           var = "store_password",
                           value = "1")

        reg_form.add_field(type = "text-single", \
                           label = lang_class.account_host, \
                           var = "host")
        
        reg_form.add_field(type = "text-single", \
                           label = lang_class.account_port, \
                           var = "port")
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_type, \
                                   var = "type")
        field.add_option(label = "POP3", \
                         value = "pop3")
        field.add_option(label = "POP3S", \
                         value = "pop3s")
        field.add_option(label = "IMAP", \
                         value = "imap")
        field.add_option(label = "IMAPS", \
                         value = "imaps")
        
        reg_form.add_field(type = "text-single", \
                           label = lang_class.account_mailbox, \
                           var = "mailbox", \
                           value = "INBOX")
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_ffc_action, \
                                   var = "chat_action", \
                                   value = str(mailconnection.RETRIEVE))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_online_action, \
                                   var = "online_action", \
                                   value = str(mailconnection.RETRIEVE))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_away_action, \
                                   var = "away_action", \
                                   value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_xa_action, \
                                   var = "xa_action", \
                                   value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_dnd_action, \
                                   var = "dnd_action", \
                                   value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form.add_field(type = "list-single", \
                                   label = lang_class.account_offline_action, \
                                   var = "offline_action", \
                                   value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        # default interval in config file
        reg_form.add_field(type = "text-single", \
                           label = lang_class.account_check_interval, \
                           var = "interval", \
                           value = unicode(self.__interval))

        reg_form.add_field(type = "boolean", \
                           label = lang_class.account_live_email_only, \
                           var = "live_email_only")
        
	return reg_form

    """ Register Form modifier for existing accounts """
    def get_reg_form_init(self, lang_class, jid, name):
	if not self.__storage.has_key((jid, name)):
	    return None
	account = self.__storage[(jid, name)]
        reg_form_init = X()
        reg_form_init.xmlns = "jabber:x:data"
        reg_form_init.title = lang_class.update_title
        reg_form_init.instructions = lang_class.update_instructions % \
                                     (name,)
        reg_form_init.type = "form"
        
        reg_form_init.add_field(type = "hidden", \
                                label = lang_class.account_name, \
                                var = "name", \
                                value = name)
        
        reg_form_init.add_field(type = "text-single", \
                                label = lang_class.account_login, \
                                var = "login", \
                                value = account.login)
        
        reg_form_init.add_field(type = "text-private", \
                                label = lang_class.account_password, \
                                var = "password", \
                                value = account.password)
        
        reg_form_init.add_field(type = "boolean", \
                                label = lang_class.account_password_store, \
                                var = "store_password", \
                                value = str(account.store_password).lower())

        reg_form_init.add_field(type = "text-single", \
                                label = lang_class.account_host, \
                                var = "host", \
                                value = account.host)
        
        reg_form_init.add_field(type = "text-single", \
                                label = lang_class.account_port, \
                                var = "port", \
                                value = unicode(account.port))
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_type, \
                                        var = "type", \
                                        value = account.get_type())
        if account.get_type()[0:4] == "imap":
            field.add_option(label = "IMAP", \
                             value = "imap")
            field.add_option(label = "IMAPS", \
                             value = "imaps")
            field = reg_form_init.add_field(type = "text-single", \
                                            label = lang_class.account_mailbox, \
                                            var = "mailbox")
	    field.value = account.mailbox
        else:
            field.add_option(label = "POP3", \
                             value = "pop3")
            field.add_option(label = "POP3S", \
                             value = "pop3s")
            
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_ffc_action, \
                                        var = "chat_action", \
                                        value = str(account.chat_action))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_online_action, \
                                        var = "online_action", \
                                        value = str(account.online_action))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_away_action, \
                                        var = "away_action", \
                                        value = str(account.away_action))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_xa_action, \
                                        var = "xa_action", \
                                        value = str(account.xa_action))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_dnd_action, \
                                        var = "dnd_action", \
                                        value = str(account.dnd_action))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        field = reg_form_init.add_field(type = "list-single", \
                                        label = lang_class.account_offline_action, \
                                        var = "offline_action", \
                                        value = str(account.offline_action))
        field.add_option(label = lang_class.action_nothing, \
                         value = str(mailconnection.DO_NOTHING))
        field.add_option(label = lang_class.action_digest, \
                         value = str(mailconnection.DIGEST))
        field.add_option(label = lang_class.action_retrieve, \
                         value = str(mailconnection.RETRIEVE))
        
        reg_form_init.add_field(type = "text-single", \
                                label = lang_class.account_check_interval, \
                                var = "interval", \
                                value = str(account.interval))

        reg_form_init.add_field(type = "boolean", \
                                label = lang_class.account_live_email_only, \
                                var = "live_email_only", \
                                value = str(account.live_email_only).lower())

	return reg_form_init

    """ Looping method """
    def run(self, timeout):
        self.connect()
        self.running = True
        thread.start_new_thread(self.time_handler, ())
        try:
            while (not self.__shutdown and self.stream
		   and not self.stream.eof and self.stream.socket is not None):
                try:
                    self.stream.loop_iter(timeout)
                except (KeyboardInterrupt, SystemExit, FatalStreamError, \
                        StreamError):
                    raise
                except:
                    self.__logger.exception("Exception cought:")
        finally:
            ## TODO : for jid in self.__storage.keys(())
            ## for name in self.__storage.keys((jid,))
            self.running = False
            if self.stream:
                for jid in self.__storage.keys(()):
                    p = Presence(from_jid = unicode(self.jid), to_jid = jid, \
                                 stanza_type = "unavailable")
                    self.stream.send(p)
                for jid, name in self.__storage.keys():
                    if self.__storage[(jid, name)].status != "offline":
                        p = Presence(from_jid = name + "@" + unicode(self.jid), \
                                     to_jid = jid, \
                                     stanza_type = "unavailable")
                        self.stream.send(p)
            threads = threading.enumerate()
            for th in threads:
                try:
                    th.join(10 * timeout)
                except:
                    pass
            for th in threads:
                try:
                    th.join(timeout)
                except:
                    pass
            self.disconnect()
            del self.__storage
            self.__logger.debug("Exitting normally")

    """ Stop method handler """
    def signal_handler(self, signum, frame):
        self.__logger.debug("Signal %i received, shutting down..." % (signum,))
        self.__shutdown = 1

    """ SIGALRM signal handler """
    def time_handler(self):
        self.__logger.debug("Check mail thread started...")
        while self.running:
            self.check_all_mail()
            self.__logger.debug("Resetting alarm signal")
            if self.__count == 0:
                self.__logger.debug("Dumping registered accounts Database")
                self.__storage.sync()
                self.__count = 60
            else:
                self.__count -= 1
            time.sleep(60)

    """ Component authentication handler """
    def authenticated(self):
	self.__logger.debug("AUTHENTICATED")
        Component.authenticated(self)
	for jid in self.__storage.keys(()):
	    p = Presence(from_jid = unicode(self.jid), \
                         to_jid = jid, stanza_type = "probe")
            self.stream.send(p)
        for jid, name in self.__storage.keys():
	    p = Presence(from_jid = name + "@" + unicode(self.jid), \
                         to_jid = jid, stanza_type = "probe")
            self.stream.send(p)

        self.stream.set_iq_get_handler("query", "jabber:iq:version", \
				       self.get_version)
        self.stream.set_iq_get_handler("query", "jabber:iq:register", \
				       self.get_register)
        self.stream.set_iq_set_handler("query", "jabber:iq:register", \
				       self.set_register)

        self.stream.set_presence_handler("available", \
					 self.presence_available)

        self.stream.set_presence_handler("probe", \
					 self.presence_available)

        self.stream.set_presence_handler("unavailable", \
					 self.presence_unavailable)

        self.stream.set_presence_handler("unsubscribe", \
					 self.presence_unsubscribe)
        self.stream.set_presence_handler("unsubscribed", \
					 self.presence_unsubscribed)
        self.stream.set_presence_handler("subscribe", \
					 self.presence_subscribe)
        self.stream.set_presence_handler("subscribed", \
					 self.presence_subscribed)

	self.stream.set_message_handler("normal", \
					self.message)
    
    def stream_state_changed(self,state,arg):
        self.__logger.debug("*** State changed: %s %r ***" % (state,arg))

    """ Discovery get info handler """
    def disco_get_info(self, node, iq):
	self.__logger.debug("DISCO_GET_INFO")
	di = DiscoInfo()
	if node is None:
	    di.add_feature("jabber:iq:version")
	    di.add_feature("jabber:iq:register")
	    DiscoIdentity(di, self.__name, "headline", "newmail")
	else:
	    di.add_feature("jabber:iq:register")
	return di

    """ Discovery get nested nodes handler """
    def disco_get_items(self, node, iq):
	self.__logger.debug("DISCO_GET_ITEMS")
        lang_class = self.__lang.get_lang_class_from_node(iq.get_node())
	base_from_jid = unicode(iq.get_from().bare())
	di = DiscoItems()
        if not node:
            for name in self.__storage.keys((base_from_jid,)):
		account = self.__storage[(base_from_jid, name)]
		str_name = lang_class.connection_label % (account.get_type().upper(), name)
		if account.get_type()[0:4] == "imap":
		    str_name += " (" + account.mailbox + ")"
		DiscoItem(di, JID(name + "@" + unicode(self.jid)), \
			  name, str_name)
	return di

    """ Get Version handler """
    def get_version(self, iq):
	self.__logger.debug("GET_VERSION")
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:version")
        q.newTextChild(q.ns(), "name", self.__name)
        q.newTextChild(q.ns(), "version", "0.2")
        self.stream.send(iq)
        return 1

    """ Send back register form to user """
    def get_register(self, iq):
	self.__logger.debug("GET_REGISTER")
        lang_class = self.__lang.get_lang_class_from_node(iq.get_node())
	base_from_jid = unicode(iq.get_from().bare())
        to = iq.get_to()
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:register")
        if to and to != self.jid:
	    self.get_reg_form_init(lang_class,
                                   base_from_jid,
                                   to.node).attach_xml(q)
	else:
	    self.get_reg_form(lang_class).attach_xml(q)
	self.stream.send(iq)
        return 1

    """ Handle user registration response """
    def set_register(self, iq):
	self.__logger.debug("SET_REGISTER")
        lang_class = self.__lang.get_lang_class_from_node(iq.get_node())
        to = iq.get_to()
	from_jid = iq.get_from()
        base_from_jid = unicode(from_jid.bare())
        remove = iq.xpath_eval("r:query/r:remove", \
			       {"r" : "jabber:iq:register"})
        if remove:
            for jid, name in self.__storage.keys():
                p = Presence(from_jid = name + "@" + unicode(self.jid), \
                             to_jid = from_jid, \
                             stanza_type = "unsubscribe")
                self.stream.send(p)
                p = Presence(from_jid = name + "@" + unicode(self.jid), \
                             to_jid = from_jid, \
                             stanza_type = "unsubscribed")
                self.stream.send(p)
                del self.__storage[(jid, name)]
	    p = Presence(from_jid = self.jid, to_jid = from_jid, \
			 stanza_type = "unsubscribe")
	    self.stream.send(p)
	    p = Presence(from_jid = self.jid, to_jid = from_jid, \
			 stanza_type = "unsubscribed")
	    self.stream.send(p)
	    return 1

	query = iq.get_query()
	x = X()
	x.from_xml(query.children)

	if x.fields.has_key("name"):
	    name = x.fields["name"].value.lower()
	else:
	    name = u""

	if x.fields.has_key("login"):
	    login = x.fields["login"].value
	else:
	    login = u""

	if x.fields.has_key("password"):
	    password = x.fields["password"].value
	else:
	    password = u""

	store_password = x.fields.has_key("store_password") \
                         and (x.fields["store_password"].value == "1")

	if x.fields.has_key("host"):
	    host = x.fields["host"].value
	else:
	    host = u""

	if x.fields.has_key("mailbox"):
	    mailbox = x.fields["mailbox"].value
	else:
	    mailbox = u""

	if x.fields.has_key("type"):
	    type = x.fields["type"].value
	else:
	    type = u"pop3"

	if x.fields.has_key("port") and x.fields["port"].value != "":
	    port = int(x.fields["port"].value)
	else:
	    port = None

	if x.fields.has_key("chat_action") and x.fields["chat_action"].value != "":
	    chat_action = int(x.fields["chat_action"].value)
	else:
	    chat_action = mailconnection.DO_NOTHING

	if x.fields.has_key("online_action") and x.fields["online_action"].value != "":
	    online_action = int(x.fields["online_action"].value)
	else:
	    online_action = mailconnection.DO_NOTHING
        
	if x.fields.has_key("away_action") and x.fields["away_action"].value != "":
	    away_action = int(x.fields["away_action"].value)
	else:
	    away_action = mailconnection.DO_NOTHING

	if x.fields.has_key("xa_action") and x.fields["xa_action"].value != "":
	    xa_action = int(x.fields["xa_action"].value)
	else:
	    xa_action = mailconnection.DO_NOTHING

	if x.fields.has_key("dnd_action") and x.fields["dnd_action"].value != "":
	    dnd_action = int(x.fields["dnd_action"].value)
	else:
	    dnd_action = mailconnection.DO_NOTHING

	if x.fields.has_key("offline_action") and x.fields["offline_action"].value != "":
	    offline_action = int(x.fields["offline_action"].value)
	else:
	    offline_action = mailconnection.DO_NOTHING

	if x.fields.has_key("interval") and x.fields["interval"].value != "":
	    interval = int(x.fields["interval"].value)
	else:
	    interval = None

	live_email_only = x.fields.has_key("live_email_only") \
                          and (x.fields["live_email_only"].value == "1")

	self.__logger.debug(u"New Account: %s, %s, %s, %s, %s, %s, %s, %s %i %i %i %i %i %i %i %s" \
			    % (name, login, password, str(store_password), host, str(port), \
                               mailbox, type, chat_action, online_action, away_action, \
                               xa_action, dnd_action, offline_action, interval, str(live_email_only)))

        iq = iq.make_result_response()
        self.stream.send(iq)

	if not self.__storage.has_key((base_from_jid,)):
	    p = Presence(from_jid = self.jid, to_jid = base_from_jid, \
			 stanza_type="subscribe")
	    self.stream.send(p)

	## Update account
	if port != None:
	  socket = host + ":" + str(port)
	else:
	  socket = host
	if self.__storage.has_key((base_from_jid, name)):
            account = self.__storage[(base_from_jid, name)]
	    m = Message(from_jid = self.jid, to_jid = from_jid, \
			stanza_type = "normal", \
                        subject = lang_class.update_account_message_subject \
                        % (type, name), \
			body = lang_class.update_account_message_body \
			% (login, password, socket))
	    self.stream.send(m)
	else:
            account = mailconnection_factory.get_new_mail_connection(type)
	    m = Message(from_jid = self.jid, to_jid = from_jid, \
			stanza_type = "normal", \
                        subject = lang_class.new_account_message_subject \
			% (type, name), \
			body = lang_class.new_account_message_body \
			% (login, password, socket))
	    self.stream.send(m)
	    p = Presence(from_jid = name + "@" + unicode(self.jid), \
			 to_jid = base_from_jid, \
			 stanza_type="subscribe")
	    self.stream.send(p)
 	account.login = login
 	account.password = password
        account.store_password = store_password
 	account.host = host
        account.chat_action = chat_action
        account.online_action = online_action
        account.away_action = away_action
        account.xa_action = xa_action
        account.dnd_action = dnd_action
        account.offline_action = offline_action
        account.interval = interval
        account.live_email_only = live_email_only

	if port:
	    account.port = port

 	if type[0:4] == "imap":
 	    account.mailbox = mailbox
        self.__storage[(base_from_jid, name)] = account
        
        return 1

    """ Handle presence availability """
    def presence_available(self, stanza):
	self.__logger.debug("PRESENCE_AVAILABLE")
	from_jid = stanza.get_from()
        base_from_jid = unicode(from_jid.bare())
        lang_class = self.__lang.get_lang_class_from_node(stanza.get_node())
	name = stanza.get_to().node
	show = stanza.get_show()
        self.__logger.debug("SHOW : " + str(show))
        if name:
            self.__logger.debug("TO : " + name + " " + base_from_jid)
        if not name and self.__storage.has_key((base_from_jid,)):
            p = Presence(from_jid = self.jid, \
                         to_jid = from_jid, \
                         status = \
                         str(len(self.__storage.keys((base_from_jid,)))) \
                         + " accounts registered.", \
                         show = show, \
                         stanza_type = "available")
            self.stream.send(p)
        elif self.__storage.has_key((base_from_jid, name)):
            account = self.__storage[(base_from_jid, name)]
            account.default_lang_class = lang_class
            old_status = account.status
            # Make available to receive mail only when online
            if show is None:
                account.status = "online" # TODO get real status = (not show)
            else:
                account.status = show
            p = Presence(from_jid = name + "@" + \
                         unicode(self.jid), \
                         to_jid = from_jid, \
                         status = account.get_status_msg(), \
                         show = show, \
                         stanza_type = "available")
            self.stream.send(p)
            if account.store_password == False \
                   and old_status == "offline":
                self.__ask_password(name, from_jid, lang_class, account)
        return 1

    def __ask_password(self, name, from_jid, lang_class, account):
        if not account.waiting_password_reply \
               and account.status != "offline":
            account.waiting_password_reply = True
            msg = Message(from_jid = name + "@" + unicode(self.jid), \
                          to_jid = from_jid, \
                          stanza_type = "normal", \
                          subject = u"[PASSWORD] " + lang_class.ask_password_subject, \
                          body = lang_class.ask_password_body % \
                          (account.host, account.login))
            self.stream.send(msg)

    """ handle presence unavailability """
    def presence_unavailable(self, stanza):
	self.__logger.debug("PRESENCE_UNAVAILABLE")
	from_jid = stanza.get_from()
        base_from_jid = unicode(from_jid.bare())
        if stanza.get_to() == unicode(self.jid):
	    for jid, name in self.__storage.keys():
                account = self.__storage[(base_from_jid, name)]
                account.status = "offline"
                account.waiting_password_reply = False
                if account.store_password == False:
                    self.__logger.debug("Forgetting password")
                    account.password = None
		p = Presence(from_jid = name + "@" + unicode(self.jid), \
			     to_jid = from_jid, \
			     stanza_type = "unavailable")
		self.stream.send(p)
	    
	p = Presence(from_jid = stanza.get_to(), to_jid = from_jid, \
		     stanza_type = "unavailable")
        self.stream.send(p)
        return 1

    """ handle subscribe presence from user """
    def presence_subscribe(self, stanza):
	self.__logger.debug("PRESENCE_SUBSCRIBE")
        p = stanza.make_accept_response()
        self.stream.send(p)
        return 1

    """ handle subscribed presence from user """
    def presence_subscribed(self, stanza):
	self.__logger.debug("PRESENCE_SUBSCRIBED")
	name = stanza.get_to().node
	from_jid = stanza.get_from()
        base_from_jid = unicode(from_jid.bare())
        if name is not None and self.__storage.has_key((base_from_jid, name)):
            account = self.__storage[(base_from_jid, name)]
            account.status = "online" # TODO retrieve real status
            p = Presence(from_jid = stanza.get_to(), to_jid = from_jid, \
                         status = account.get_status_msg(), \
                         stanza_type = "available")
            self.stream.send(p)
        return 1

    """ handle unsubscribe presence from user """
    def presence_unsubscribe(self, stanza):
	self.__logger.debug("PRESENCE_UNSUBSCRIBE")
	name = stanza.get_to().node
	from_jid = stanza.get_from()
        base_from_jid = unicode(from_jid.bare())
        if name is not None and self.__storage.has_key((base_from_jid, name)):
	    del self.__storage[(base_from_jid, name)]
	p = Presence(from_jid = stanza.get_to(), to_jid = from_jid, \
		     stanza_type = "unsubscribe")
	self.stream.send(p)
        p = stanza.make_accept_response()
        self.stream.send(p)
        return 1

    """ handle unsubscribed presence from user """
    def presence_unsubscribed(self, stanza):
	self.__logger.debug("PRESENCE_UNSUBSCRIBED")
	p = Presence(from_jid = stanza.get_to(), to_jid = stanza.get_from(), \
		     stanza_type = "unavailable")
        self.stream.send(p)
        self.__storage.sync()
        return 1

    """ Handle new message """
    def message(self, message):
	self.__logger.debug("MESSAGE: " + message.get_body())
        lang_class = self.__lang.get_lang_class_from_node(message.get_node())
	name = message.get_to().node
	base_from_jid = unicode(message.get_from().bare())
        if re.compile("\[PASSWORD\]").search(message.get_subject()) is not None \
               and self.__storage.has_key((base_from_jid, name)):
            account = self.__storage[(base_from_jid, name)]
            account.password = message.get_body()
            account.waiting_password_reply = False
            msg = Message(from_jid = name + "@" + unicode(self.jid), \
                          to_jid = message.get_from(), \
                          stanza_type = "normal", \
                          subject = lang_class.password_saved_for_session, \
                          body = lang_class.password_saved_for_session)
            self.stream.send(msg)
	return 1

    """ Check mail account """
    def check_mail(self, jid, name):
	self.__logger.debug("CHECK_MAIL " + unicode(jid) + " " + name)
	account = self.__storage[(jid, name)]
        action = account.action

        if action != mailconnection.DO_NOTHING:
            try:
                if account.password is None:
                    self.__ask_password(name, jid, account.default_lang_class, account)
                    return
                self.__logger.debug("Checking " + name)
                self.__logger.debug("\t" + account.login \
                                    + "@" + account.host)
                account.connect()
                mail_list = account.get_mail_list()
                if not mail_list or mail_list[0] == '':
                    num = 0
                else:
                    num = len(mail_list)
                # unseen mails checked by external client
                # TODO : better test to find
                if num < account.lastmail:
                    account.lastmail = 0
                if action == mailconnection.RETRIEVE:
                    while account.lastmail < num:
                        (body, email_from) = account.get_mail(int(mail_list[account.lastmail]))
                        mesg = Message(from_jid = name + "@" + \
                                       unicode(self.jid), \
                                       to_jid = jid, \
                                       stanza_type = "normal", \
                                       subject = account.default_lang_class.new_mail_subject % (email_from), \
                                       body = body)
                        self.stream.send(mesg)
                        account.lastmail += 1
                else:
                    body = ""
                    new_mail_count = 0
                    while account.lastmail < num:
                        (tmp_body, from_email) = \
                               account.get_mail_summary(int(mail_list[account.lastmail]))
                        body += tmp_body + "\n----------------------------------\n"
                        account.lastmail += 1
                        new_mail_count += 1
                    if body != "":
                        mesg = Message(from_jid = name + "@" + \
                                       unicode(self.jid), \
                                       to_jid = jid, \
                                       stanza_type = "headline", \
                                       subject = account.default_lang_class.new_digest_subject % (new_mail_count), \
                                       body = body)
                        self.stream.send(mesg)
                account.disconnect()
                account.in_error = False
            except Exception,e:
                if account.in_error == False:
                    account.in_error = True
                    msg = Message(from_jid = name + "@" + unicode(self.jid), \
                                  to_jid = jid, \
                                  stanza_type = "error", \
                                  subject = account.default_lang_class.check_error_subject, \
                                  body = account.default_lang_class.check_error_body \
                                  % (e))
                    self.stream.send(msg)
                type, value, stack = sys.exc_info()
                self.__logger.debug("Error while checking mail : %s\n%s" \
                                    % (e, "".join(traceback.format_exception
                                                  (type, value, stack, 5))))

    """ check mail handler """
    def check_all_mail(self):
	self.__logger.debug("CHECK_ALL_MAIL")
        for jid, name in self.__storage.keys():
            account = self.__storage[(jid, name)]
            if account.first_check and account.live_email_only:
                account.first_check = False
                if account.password is None:
                    self.__ask_password(name, jid, account.default_lang_class, account)
                    return
                try:
                    account.connect()
                    mail_list = account.get_mail_list()
                    if not mail_list or mail_list[0] == '':
                        account.lastmail = 0
                    else:
                        account.lastmail = len(mail_list)
                    account.disconnect()
                    account.in_error = False
                except Exception,e:
                    if account.in_error == False:
                        account.in_error = True
                        msg = Message(from_jid = name + "@" + unicode(self.jid), \
                                      to_jid = jid, \
                                      stanza_type = "error", \
                                      subject = account.default_lang_class.check_error_subject, \
                                      body = account.default_lang_class.check_error_body \
                                      % (e))
                        self.stream.send(msg)
                    type, value, stack = sys.exc_info()
                    self.__logger.debug("Error while first checking mail : %s\n%s" \
                                        % (e, "".join(traceback.format_exception
                                                      (type, value, stack, 5))))
            account.lastcheck += 1
            if account.lastcheck == account.interval:
                account.lastcheck = 0
                self.check_mail(jid, name)
