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
import logging
import sys
import anydbm
import os

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

class ComponentFatalError(RuntimeError):
    pass

class MailComponent(Component):
    def __init__(self, config):
	Component.__init__(self, \
                           JID(config.get_content("config/jabber/service")), \
                           config.get_content("config/jabber/secret"), \
                           config.get_content("config/jabber/server"), \
                           int(config.get_content("config/jabber/port")), \
                           disco_category = "gateway", \
                           disco_type = "headline")
 	self.__logger = logging.getLogger("jabber.Component")
	self.__shutdown = 0

        # TODO : delete signals not known by Windows
	signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGPIPE, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGALRM, self.time_handler)
	
	self.__interval = int(config.get_content("config/check_interval"))
	self.__config = config
#	self.__registered = {}
        try:
            self.__storage = globals()[config.get_content("config/storage") + "Storage"]()
        except:
            print >>sys.stderr, "Cannot find " \
                  + config.get_content("config/storage") + "Storage class"
            exit(1)
	self.__spool_dir = config.get_content("config/spooldir") + "/" + \
                           config.get_content("config/jabber/service")
        self.__storage.spool_dir = self.__spool_dir
        self.__storage.nb_pk_fields = 2
	self.__reg_form = None
	self.__reg_form_init = None
	# dump registered accounts (save) at least every hour
	self.__count = 60 / self.__interval

    def __del__(self):
        logging.shutdown()
        
    """ Register Form creator """
    def get_reg_form(self):
	if self.__reg_form == None:
	    self.__reg_form = X()
	    self.__reg_form.xmlns = "jabber:x:data"
	    self.__reg_form.title = "Jabber Mail connection registration"
            self.__reg_form.instructions = "Enter anything below"
            self.__reg_form.type = "form"

	    self.__reg_form.add_field(type = "text-single", \
                                      label = "Connection name", \
                                      var = "name")
	    
	    self.__reg_form.add_field(type = "text-single", \
                                      label = "Login", \
                                      var = "login")
	    
	    self.__reg_form.add_field(type = "text-private", \
                                      label = "Password", \
                                      var = "password")
	    
	    self.__reg_form.add_field(type = "text-single", \
                                      label = "Host", \
                                      var = "host")
            
	    self.__reg_form.add_field(type = "text-single", \
                                      label = "Port", \
                                      var = "port")
        
	    field = self.__reg_form.add_field(type = "list-single", \
                                              label = "Mailbox type", \
                                              var = "type")
	    field.add_option(label = "POP3", \
			     value = "pop3")
	    field.add_option(label = "POP3S", \
			     value = "pop3s")
	    field.add_option(label = "IMAP", \
			     value = "imap")
	    field.add_option(label = "IMAPS", \
			     value = "imaps")
            
	    self.__reg_form.add_field(type = "text-single", \
                                      label = "Mailbox (IMAP)", \
                                      var = "mailbox", \
                                      value = "INBOX")
            
	    field = self.__reg_form.add_field(type = "list-single", \
                                              label = "Action when state is 'Free For Chat'", \
                                              var = "ffc_action", \
                                              value = str(mailconnection.RETRIEVE))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form.add_field(type = "list-single", \
                                              label = "Action when state is 'Online'", \
                                              var = "online_action", \
                                              value = str(mailconnection.RETRIEVE))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form.add_field(type = "list-single", \
                                              label = "Action when state is 'Away'", \
                                              var = "away_action", \
                                              value = str(mailconnection.DIGEST))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form.add_field(type = "list-single", \
                                              label = "Action when state is 'Extended Away'", \
                                              var = "ea_action", \
                                              value = str(mailconnection.DIGEST))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form.add_field(type = "list-single", \
                                              label = "Action when state is 'Offline'", \
                                              var = "offline_action", \
                                              value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

            # default interval in config file
	    self.__reg_form.add_field(type = "text-single", \
                                      label = "Mail check interval (in minutes)", \
                                      var = "interval", \
                                      value = "5")

	return self.__reg_form

    """ Register Form modifier for existing accounts """
    def get_reg_form_init(self, jid, name):
	if not self.__storage.has_key((jid, name)):
	    return None
	account = self.__storage[(jid, name)]
	if self.__reg_form_init == None:
	    self.__reg_form_init = X()
	    self.__reg_form_init.xmlns = "jabber:x:data"
	    self.__reg_form_init.title = "Jabber mail connection Modifier"
            self.__reg_form_init.instructions = "Modifier for connection " + \
                                              name
            self.__reg_form_init.type = "form"

	    self.__reg_form_init.add_field(type = "fixed", \
                                           label = "Connection name", \
                                           var = "name", \
                                           value = name)
	    
	    self.__reg_form_init.add_field(type = "text-single", \
                                           label = "Login", \
                                           var = "login", \
                                           value = account.login)
	    
	    self.__reg_form_init.add_field(type = "text-private", \
                                           label = "Password", \
                                           var = "password", \
                                           value = account.password)
	    
	    self.__reg_form_init.add_field(type = "text-single", \
                                           label = "Host", \
                                           var = "host", \
                                           value = account.host)
            
	    self.__reg_form_init.add_field(type = "text-single", \
                                           label = "Port", \
                                           var = "port", \
                                           value = str(account.port))
	    
	    field = self.__reg_form_init.add_field(type = "list-single", \
                                                   label = "Mailbox type", \
                                                   var = "type", \
                                                   value = account.get_type())
	    field.add_option(label = "POP3", \
			     value = "pop3")
	    field.add_option(label = "POP3S", \
			     value = "pop3s")
	    field.add_option(label = "IMAP", \
			     value = "imap")
	    field.add_option(label = "IMAPS", \
			     value = "imaps")
            
	    self.__reg_form_init.add_field(type = "text-single", \
                                           label = "Mailbox (IMAP)", \
                                           var = "mailbox")
            
	    field = self.__reg_form_init.add_field(type = "list-single", \
                                                   label = "Action when state is 'Free For Chat'", \
                                                   var = "ffc_action", \
                                                   value = str(account.ffc_action))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form_init.add_field(type = "list-single", \
                                                   label = "Action when state is 'Online'", \
                                                   var = "online_action", \
                                                   value = str(account.online_action))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form_init.add_field(type = "list-single", \
                                                   label = "Action when state is 'Away'", \
                                                   var = "away_action", \
                                                   value = str(account.away_action))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form_init.add_field(type = "list-single", \
                                                   label = "Action when state is 'Extended Away'", \
                                                   var = "ea_action", \
                                                   value = str(account.ea_action))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    field = self.__reg_form_init.add_field(type = "list-single", \
                                                   label = "Action when state is 'Offline'", \
                                                   var = "offline_action", \
                                                   value = str(account.offline_action))
	    field.add_option(label = "Do nothing", \
			     value = str(mailconnection.DO_NOTHING))
	    field.add_option(label = "Send mail digest", \
			     value = str(mailconnection.DIGEST))
	    field.add_option(label = "Retrieve mail", \
			     value = str(mailconnection.RETRIEVE))

	    self.__reg_form_init.add_field(type = "text-single", \
                                           label = "Mail check interval (in minutes)", \
                                           var = "interval", \
                                           value = str(account.interval))
	else:
	    self.__reg_form_init.fields["login"].value = account.login
	    self.__reg_form_init.fields["password"].value = account.password
	    self.__reg_form_init.fields["host"].value = account.host
	    self.__reg_form_init.fields["port"].value = str(account.port)
	    self.__reg_form_init.fields["type"].value = account.get_type()
	    self.__reg_form_init.fields["ffc_action"].value = str(account.ffc_action)
	    self.__reg_form_init.fields["online_action"].value = str(account.online_action)
	    self.__reg_form_init.fields["away_action"].value = str(account.away_action)
	    self.__reg_form_init.fields["ea_action"].value = str(account.ea_action)
	    self.__reg_form_init.fields["offline_action"].value = str(account.offline_action)
	    self.__reg_form_init.fields["interval"].value = str(account.interval)

	if account.get_type()[0:4] == "imap":
	    self.__reg_form_init.fields["mailbox"].value = account.mailbox
	else:
	    self.__reg_form_init.fields["mailbox"].value = "INBOX"

	return self.__reg_form_init

    """ Looping method """
    def run(self, timeout):
        self.connect()
	# Set check mail timer
        threading.Timer(self.__interval * 60, self.time_handler)
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
# 	    for jid in self.__storage.keys(()):
# 		p = Presence(from_jid = str(self.jid), to_jid = jid, \
# 			     stanza_type = "unavailable")
# 		self.stream.send(p)
# 		for name in self.__registered[jid].keys():
# 		    if self.__storage[(jid, name)].status != "offline":
# 			p = Presence(from_jid = name + "@" + str(self.jid), \
# 				     to_jid = jid, \
# 				     stanza_type = "unavailable")
# 			self.stream.send(p)
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
    def time_handler(self, signum, frame):
        self.__logger.debug("Signal %i received, checking mail..." % (signum,))
	self.check_all_mail()
	self.__logger.debug("Resetting alarm signal")
	threading.Timer(self.__interval * 60, self.time_handler)
	if self.__count == 0:
	    self.__logger.debug("Dumping registered accounts Database")
	    self.__storage.sync()
	    self.__count = 60 / self.__interval
	else:
	    self.__count -= 1

    """ Component authentication handler """
    def authenticated(self):
	self.__logger.debug("AUTHENTICATED")
        Component.authenticated(self)
# 	for jid in self.__registered.keys():
# 	    p = Presence(from_jid = str(self.jid), \
#                          to_jid = jid, stanza_type = "probe")
#             self.stream.send(p)

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
	    DiscoIdentity(di, "Jabber Mail Component", "headline", "mail")
	else:
	    di.add_feature("jabber:iq:register")
	return di

    """ Discovery get nested nodes handler """
    def disco_get_items(self, node, iq):
	self.__logger.debug("DISCO_GET_ITEMS")
	base_from_jid = str(iq.get_from().bare())
	di = DiscoItems()
	if not node and self.__registered.has_key(base_from_jid):
	    for name in self.__registered[base_from_jid].keys():
		account = self.__registered[base_from_jid][name]
		str_name = account.get_type() + " connection " + name
		if account.get_type()[0:4] == "imap":
		    str_name += " (" + account.mailbox + ")"
		DiscoItem(di, JID(name + "@" + str(self.jid)), \
			  name, str_name)
	return di

    """ Get Version handler """
    def get_version(self, iq):
	self.__logger.debug("GET_VERSION")
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:version")
        q.newTextChild(q.ns(), "name", "Jabber Mail Component")
        q.newTextChild(q.ns(), "version", "0.1")
        self.stream.send(iq)
        return 1

    """ Send back register form to user """
    def get_register(self, iq):
	self.__logger.debug("GET_REGISTER")
	base_from_jid = str(iq.get_from().bare())
        to = iq.get_to()
        iq = iq.make_result_response()
        q = iq.new_query("jabber:iq:register")
        if to and to != self.jid:
	    self.get_reg_form_init(base_from_jid, to.node).attach_xml(q)
	else:
	    self.get_reg_form().attach_xml(q)
	self.stream.send(iq)
        return 1

    """ Handle user registration response """
    def set_register(self, iq):
	self.__logger.debug("SET_REGISTER")
        to = iq.get_to()
	from_jid = iq.get_from()
        base_from_jid = str(from_jid.bare())
        remove = iq.xpath_eval("r:query/r:remove", \
			       {"r" : "jabber:iq:register"})
        if remove:
	    if self.__registered.has_key(base_from_jid):
		for name in self.__registered[base_from_jid].keys():
		    p = Presence(from_jid = name + "@" + str(self.jid), \
				 to_jid = from_jid, \
				 stanza_type = "unsubscribe")
		    self.stream.send(p)
		    p = Presence(from_jid = name + "@" + str(self.jid), \
				 to_jid = from_jid, \
				 stanza_type = "unsubscribed")
		    self.stream.send(p)
		del self.__registered[base_from_jid]
#                self.__storage.
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

	if x.fields.has_key("ffc_action") and x.fields["ffc_action"].value != "":
	    ffc_action = int(x.fields["ffc_action"].value)
	else:
	    ffc_action = mailconnection.DO_NOTHING

	if x.fields.has_key("online_action") and x.fields["online_action"].value != "":
	    online_action = int(x.fields["online_action"].value)
	else:
	    online_action = mailconnection.DO_NOTHING
        
	if x.fields.has_key("away_action") and x.fields["away_action"].value != "":
	    away_action = int(x.fields["away_action"].value)
	else:
	    away_action = mailconnection.DO_NOTHING

	if x.fields.has_key("ea_action") and x.fields["ea_action"].value != "":
	    ea_action = int(x.fields["ea_action"].value)
	else:
	    ea_action = mailconnection.DO_NOTHING

	if x.fields.has_key("offline_action") and x.fields["offline_action"].value != "":
	    offline_action = int(x.fields["offline_action"].value)
	else:
	    offline_action = mailconnection.DO_NOTHING

	if x.fields.has_key("interval") and x.fields["interval"].value != "":
	    interval = int(x.fields["interval"].value)
	else:
	    interval = None

	self.__logger.debug(u"New Account: %s, %s, %s, %s, %s, %s, %s %i %i %i %i %i %i" \
			    % (name, login, password, host, str(port), \
                               mailbox, type, ffc_action, online_action, away_action, \
                               ea_action, offline_action, interval))

        iq = iq.make_result_response()
        self.stream.send(iq)

	if not self.__registered.has_key(base_from_jid):
	    self.__registered[base_from_jid] = {}
	    p = Presence(from_jid = self.jid, to_jid = from_jid.bare(), \
			 stanza_type="subscribe")
	    self.stream.send(p)

	## Update account
	if port != None:
	  socket = host + ":" + str(port)
	else:
	  socket = host
	if self.__registered[base_from_jid].has_key(name):
	    m = Message(from_jid = self.jid, to_jid = from_jid, \
			stanza_type = "message", \
			body = u"Updated %s connection '%s': Registered with "\
			"username '%s' and password '%s' on '%s'" \
			% (type, name, login, password, socket))
	    self.stream.send(m)
	else:
	    m = Message(from_jid = self.jid, to_jid = from_jid, \
			stanza_type = "message", \
			body = u"New %s connection '%s': Registered with " \
			"username '%s' and password '%s' on '%s'" \
			% (type, name, login, password, socket))
	    self.stream.send(m)
	    p = Presence(from_jid = name + "@" + str(self.jid), \
			 to_jid = from_jid.bare(), \
			 stanza_type="subscribe")
	    self.stream.send(p)

 	self.__registered[base_from_jid][name] = \
 	    mailconnection_factory.get_new_mail_connection(type)
 	self.__registered[base_from_jid][name].login = login
 	self.__registered[base_from_jid][name].password = password
 	self.__registered[base_from_jid][name].host = host
        self.__registered[base_from_jid][name].ffc_action = ffc_action
        self.__registered[base_from_jid][name].online_action = online_action
        self.__registered[base_from_jid][name].away_action = away_action
        self.__registered[base_from_jid][name].ea_action = ea_action
        self.__registered[base_from_jid][name].offline_action = offline_action

	if port:
	    self.__registered[base_from_jid][name].port = port

	if interval:
	    self.__registered[base_from_jid][name].interval = interval

 	if type[0:4] == "imap":
 	    self.__registered[base_from_jid][name].mailbox = mailbox

	self.__storage.add([base_from_jid, name], self.__registered[base_from_jid][name])
        return 1

    """ Handle presence availability """
    def presence_available(self, stanza):
	self.__logger.debug("PRESENCE_AVAILABLE")
	from_jid = stanza.get_from()
        base_from_jid = str(from_jid.bare())
	name = stanza.get_to().node
	show = stanza.get_show()
        self.__logger.debug("SHOW : " + str(show))
	if self.__registered.has_key(base_from_jid):
	    if not name:
		p = Presence(from_jid = self.jid, \
			     to_jid = from_jid, \
			     status = \
                             str(len(self.__registered[base_from_jid])) \
			     + " accounts registered.", \
			     show = show, \
			     stanza_type = "available")
		self.stream.send(p)
		for name in self.__registered[base_from_jid].keys():
		    account = self.__registered[base_from_jid][name]
		    # Make available to receive mail only when online
		    account.status = "offline" # TODO get real status available = (not show)
		    p = Presence(from_jid = name + "@" + \
				 str(self.jid), \
				 to_jid = from_jid, \
				 status = account.get_status(), \
				 show = show, \
				 stanza_type = "available")
		    self.stream.send(p)
	    elif self.__registered[base_from_jid].has_key(name):
		account = self.__registered[base_from_jid][name]
		# Make available to receive mail only when online
		account.status = "offline" # TODO get real status = (not show)
		p = Presence(from_jid = name + "@" + \
			     str(self.jid), \
			     to_jid = from_jid, \
			     status = account.get_status(), \
			     show = show, \
			     stanza_type = "available")
		self.stream.send(p)
        return 1

    """ handle presence unavailability """
    def presence_unavailable(self, stanza):
	self.__logger.debug("PRESENCE_UNAVAILABLE")
	from_jid = stanza.get_from()
        base_from_jid = str(from_jid.bare())
	if stanza.get_to() == str(self.jid) \
		and self.__registered.has_key(base_from_jid):
	    for name in self.__registered[base_from_jid].keys():
		self.__registered[base_from_jid][name].status = "offline" # TODO get real status
		p = Presence(from_jid = name + "@" + str(self.jid), \
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
        base_from_jid = str(from_jid.bare())
	if self.__registered.has_key(base_from_jid) \
		and self.__registered[base_from_jid].has_key(name):
            account = self.__registered[base_from_jid][name]
            account.status = "online" # TODO retrieve real status
            p = Presence(from_jid = stanza.get_to(), to_jid = from_jid, \
                         status = account.get_status(), \
                         stanza_type = "available")
            self.stream.send(p)
        return 1

    """ handle unsubscribe presence from user """
    def presence_unsubscribe(self, stanza):
	self.__logger.debug("PRESENCE_UNSUBSCRIBE")
	name = stanza.get_to().node
	from_jid = stanza.get_from()
        base_from_jid = str(from_jid.bare())
	if self.__registered.has_key(base_from_jid) \
		and self.__registered[base_from_jid].has_key(name):
	    del self.__registered[base_from_jid][name]
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
	name = message.get_to().node
	base_from_jid = str(message.get_from().bare())
	if name and self.__registered.has_key(base_from_jid):
	    body = message.get_body()
	    cmd = body.split(' ')
	    if cmd[0] == "check":
		self.check_mail(base_from_jid, name)
            elif cmd[0] == "dump":
                body = ""
                for jid in self.__registered.keys():
                    for name in self.__registered[jid].keys():
                        body += name + " for user " + jid
                msg = Message(from_jid = self.jid, to_jid = base_from_jid, \
                              stanza_type = "message", \
                              body = body)
                self.stream.send(msg)
	return 1

#     """ Store registered sessions """
#     def store_registered(self):
# 	self.__logger.debug("STORE_REGISTERED")
# 	try:
# 	    if not os.path.isdir(self.__spool_dir):
# 		os.makedirs(self.__spool_dir)
# 	    str_registered = anydbm.open(self.__spool_dir + "/registered.db", \
#                                          'n')
# 	    self.__logger.debug("Saving registered sessions")
# 	    for jid in self.__registered.keys():
# 		for name in self.__registered[jid].keys():
#                     self.__logger.debug("\t" + jid + ", _" + name + "_")
#                     str_registered[jid + '#' + name] = \
#                                        str(self.__storage[(jid, name)])
# 	    str_registered.close()
# 	except Exception, e:
# 	    print >>sys.stderr, "Cannot save to registered.db : "
# 	    print >>sys.stderr, e

#     """ Load previously registered sessions """
#     def load_registered(self):
# 	self.__logger.debug("LOAD_REGISTERED")
# 	try:
# 	    if not os.path.isdir(self.__spool_dir):
# 		os.makedirs(self.__spool_dir)
# 	    str_registered = anydbm.open(self.__spool_dir + "/registered.db", \
#                                          'c')
# 	    self.__logger.debug("Loading previously registered sessions")
# 	    for key in str_registered.keys():
# 		jid, name = key.split('#')
# 		if not self.__registered.has_key(jid):
# 		    self.__registered[jid] = {}
# 		self.__storage[(jid, name)] = \
# 		    mailconnection_factory.str_to_mail_connection(str_registered[key])
# #		self.__storage[(jid, name)].name = name
# 		self.__logger.debug("Loaded data for %s on %s :" % (jid, name))
# 		self.__logger.debug("\t %s" % (self.__storage[(jid, name)])) 
# 	    str_registered.close()
# 	except Exception, e:
# 	    print >>sys.stderr, "Cannot load registered.db : "
# 	    print >>sys.stderr, e

    """ Check mail account """
    def check_mail(self, jid, name):
	self.__logger.debug("CHECK_MAIL")
	account = self.__storage[(jid, name)]
        action = account.action
        if action != "nothing":
            try:
                self.__logger.debug("Checking " \
                                    + name)
                self.__logger.debug("\t" + account.login \
                                    + "@" + account.host)
                account.connect()
                mail_list = account.get_mail_list()
                if not mail_list or mail_list[0] == '':
                    num = 0
                else:
                    num = len(mail_list)
                # unseen mails checked by external client
                if num < account.lastcheck:
                    account.lastcheck = 0
                if action == "retrieve":
                    while account.lastcheck < num:
                        body = account.get_mail(int(mail_list[account.lastcheck]))
                        mesg = Message(from_jid = name + "@" + \
                                       str(self.jid), \
                                       to_jid = jid, \
                                       stanza_type = "message", \
                                       body = body)
                        self.stream.send(mesg)
                        account.lastcheck += 1
                else:
                    body = ""
                    while account.lastcheck < num:
                        body += \
                             account.get_mail_summary(int(mail_list[account.lastcheck])) \
                             + "\n----------------------------------\n"
                        account.lastcheck += 1
                    if body != "":
                        mesg = Message(from_jid = name + "@" + \
                                       str(self.jid), \
                                       to_jid = jid, \
                                       stanza_type = "headline", \
                                       body = body)
                        self.stream.send(mesg)
			
                account.disconnect()
            except Exception,e:
                self.__logger.debug("Error while checking mail : %s" \
                                    % (e))

    """ check mail handler """
    def check_all_mail(self):
	self.__logger.debug("CHECK_ALL_MAIL")
	for jid in self.__registered.keys():
	    for name in self.__registered[jid].keys():
		self.check_mail(jid, name)
