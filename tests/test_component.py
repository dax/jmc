##
## test_mailconnection_factory.py
## Login : <adro8400@claralinux>
## Started on  Fri May 20 10:46:58 2005 adro8400
## $Id: test_component.py,v 1.2 2005/09/18 20:24:07 dax Exp $
## 
## Copyright (C) 2005 adro8400
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

import thread
import unittest
import dummy_server
import time
import traceback
from pyxmpp import xmlextra
from jabber.component import *
from jabber.config import Config

class TestStreamHandler(xmlextra.StreamHandler):
    def __init__(self, expected_balises = []):
        xmlextra.StreamHandler.__init__(self)
        self.expected_balises = expected_balises

    def stream_start(self, doc):
        pass
        
    def stream_end(self, doc):
        pass

    def stanza(self, notused, node):
        pass

class MailComponent_TestCase_NoConnection(unittest.TestCase):
    def setUp(self):
        self.mail_component = MailComponent(Config("tests/jmc-test.xml"))

    def tearDown(self):
        self.mail_component = None
        
    def test_get_reg_form(self):
        reg_form = self.mail_component.get_reg_form()
        reg_form2 = self.mail_component.get_reg_form()
        self.assertTrue(reg_form is reg_form2)

#TODO
class MailComponent_TestCase_Basic(unittest.TestCase):
    def setUp(self):
        self.handler = TestStreamHandler()
        self.mail_component = MailComponent(Config("tests/jmc-test.xml"))
        self.server = dummy_server.XMLDummyServer("localhost", 55555, None, self.handler)
        thread.start_new_thread(self.server.serve, ())

    def tearDown(self):
        self.server = None
        self.mail_component = None
        
    def test_run(self):
        self.server.responses = ["<?xml version='1.0'?><stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' id='4258238724' from='localhost'>", \
                                 "<handshake/></stream:stream>"]
        self.server.queries = ["<?xml version='1.0' encoding='UTF-8'?><stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' to='jmc.localhost' version='1.0'>", \
                               "<handshake>[0-9abcdef]*</handshake></stream:stream>"]
        self.mail_component.run(1)
        self.failUnless(self.server.verify_queries())
        # TODO : more assertion
        
class MailComponent_TestCase_NoReg(unittest.TestCase):
    def setUp(self):
        self.handler = TestStreamHandler()
#        logger = logging.getLogger()
#        logger.addHandler(logging.StreamHandler())
#        logger.setLevel(logging.DEBUG)
        self.mail_component = MailComponent(Config("tests/jmc-test.xml"))
        self.server = dummy_server.XMLDummyServer("localhost", 55555, None, self.handler)
        thread.start_new_thread(self.server.serve, ())

    def tearDown(self):
        self.server = None
        self.mail_component = None
        
    def test_disco_get_items(self):
        self.server.responses = ["<?xml version='1.0'?><stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' id='4258238724' from='localhost'>", \
                                 "<handshake/><iq type='get' to='jmc.localhost' id='aabca'><query xmlns='http://jabber.org/protocol/disco#info'/></iq>", \
                                 "</stream:stream>"]
        self.server.queries = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + \
                               "<stream:stream xmlns:stream=\"http://etherx.jabber.org/streams\" xmlns=\"jabber:component:accept\" to=\"jmc.localhost\" version=\"1.0\">", \
                               "<handshake>[0-9abcdef]*</handshake>", \
                               "<iq from=\"jmc.localhost\" type=\"result\" id=\"aabca\"><query xmlns=\"http://jabber.org/protocol/disco#info\"><feature var=\"jabber:iq:version\"/><feature var=\"jabber:iq:register\"/><identity name=\"Jabber Mail Component\" category=\"headline\" type=\"mail\"/></query></iq></stream:stream>"]
        self.mail_component.run(1)
        self.failUnless(self.server.verify_queries())

    def test_get_register(self):
        self.server.responses = ["<?xml version='1.0'?><stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' id='4258238724' from='localhost'>", \
                                 "<handshake/><iq type='get' to='jmc.localhost' from='test@localhost/test' id='aad9a'><query xmlns='jabber:iq:register'/></iq>", \
                                 "</stream:stream>"]
        self.server.queries = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + \
                               "<stream:stream xmlns:stream=\"http://etherx.jabber.org/streams\" xmlns=\"jabber:component:accept\" to=\"jmc.localhost\" version=\"1.0\">", \
                               "<handshake>[0-9abcdef]*</handshake>", \
                               "<iq from=\"jmc.localhost\" to=\"test@localhost/test\" type=\"result\" id=\"aad9a\">" + \
                               "<query xmlns=\"jabber:iq:register\">" + \
                               "<x xmlns=\"jabber:x:data\">" + \
                               "<title>Jabber Mail connection registration</title>" + \
                               "<instructions>Enter anything below</instructions>" + \
                               "<field type=\"text-single\" label=\"Connection name\" var=\"name\"/>" + \
                               "<field type=\"text-single\" label=\"Login\" var=\"login\"/>" + \
                               "<field type=\"text-private\" label=\"Password\" var=\"password\"/>" + \
                               "<field type=\"text-single\" label=\"Host\" var=\"host\"/>" + \
                               "<field type=\"text-single\" label=\"Port\" var=\"port\"/>" + \
                               "<field type=\"list-single\" label=\"Mailbox type\" var=\"type\">" + \
                               "<option label=\"POP3\">" + \
                               "<value>pop3</value>" + \
                               "</option>" + \
                               "<option label=\"POP3S\">" + \
                               "<value>pop3s</value>" + \
                               "</option>" + \
                               "<option label=\"IMAP\">" + \
                               "<value>imap</value>" + \
                               "</option>" + \
                               "<option label=\"IMAPS\">" + \
                               "<value>imaps</value>" + \
                               "</option>" + \
                               "</field>" + \
                               "<field type=\"text-single\" label=\"Mailbox (IMAP)\" var=\"mailbox\">" + \
                               "<value>INBOX</value>" + \
                               "</field>" + \
                               "<field type=\"list-single\" label=\"Action when state is 'Free For Chat'\" var=\"ffc_action\">" + \
                               "<value>2</value>" + \
                               "<option label=\"Do nothing\">" + \
                               "<value>0</value>" + \
                               "</option>" + \
                               "<option label=\"Send mail digest\">" + \
                               "<value>1</value>" + \
                               "</option>" + \
                               "<option label=\"Retrieve mail\">" + \
                               "<value>2</value>" + \
                               "</option>" + \
                               "</field>" + \
                               "<field type=\"list-single\" label=\"Action when state is 'Online'\" var=\"online_action\">" + \
                               "<value>2</value>" + \
                               "<option label=\"Do nothing\">" + \
                               "<value>0</value>" + \
                               "</option>" + \
                               "<option label=\"Send mail digest\">" + \
                               "<value>1</value>" + \
                               "</option>" + \
                               "<option label=\"Retrieve mail\">" + \
                               "<value>2</value>" + \
                               "</option>" + \
                               "</field>" + \
                               "<field type=\"list-single\" label=\"Action when state is 'Away'\" var=\"away_action\">" + \
                               "<value>1</value>" + \
                               "<option label=\"Do nothing\">" + \
                               "<value>0</value>" + \
                               "</option>" + \
                               "<option label=\"Send mail digest\">" + \
                               "<value>1</value>" + \
                               "</option>" + \
                               "<option label=\"Retrieve mail\">" + \
                               "<value>2</value>" + \
                               "</option>" + \
                               "</field>" + \
                               "<field type=\"list-single\" label=\"Action when state is 'Extended Away'\" var=\"ea_action\">" + \
                               "<value>1</value>" + \
                               "<option label=\"Do nothing\">" + \
                               "<value>0</value>" + \
                               "</option>" + \
                               "<option label=\"Send mail digest\">" + \
                               "<value>1</value>" + \
                               "</option>" + \
                               "<option label=\"Retrieve mail\">" + \
                               "<value>2</value>" + \
                               "</option>" + \
                               "</field>" + \
                               "<field type=\"list-single\" label=\"Action when state is 'Offline'\" var=\"offline_action\">" + \
                               "<value>0</value>" + \
                               "<option label=\"Do nothing\">" + \
                               "<value>0</value>" + \
                               "</option>" + \
                               "<option label=\"Send mail digest\">" + \
                               "<value>1</value>" + \
                               "</option>" + \
                               "<option label=\"Retrieve mail\">" + \
                               "<value>2</value>" + \
                               "</option>" + \
                               "</field>" + \
                               "<field type=\"text-single\" label=\"Mail check interval (in minutes)\" var=\"interval\">" + \
                               "<value>5</value>" + \
                               "</field>" + \
                               "</x>" + \
                               "</query>" + \
                               "</iq>" + \
                               "</stream:stream>"]
        self.mail_component.run(1)
        self.failUnless(self.server.verify_queries())
        

    def test_disco_get_info(self):
        self.server.responses = ["<?xml version='1.0'?><stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' id='4258238724' from='localhost'>", \
                                 "<handshake/><iq type='get' to='jmc.localhost' from='test@localhost/test' id='aad9a'><query xmlns='http://jabber.org/protocol/disco#info'/></iq>", \
                                 "</stream:stream>"]
        self.server.queries = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + \
                               "<stream:stream xmlns:stream=\"http://etherx.jabber.org/streams\" xmlns=\"jabber:component:accept\" to=\"jmc.localhost\" version=\"1.0\">", \
                               "<handshake>[0-9abcdef]*</handshake>", \
                               "<iq from=\"jmc.localhost\" to=\"test@localhost/test\" type=\"result\" id=\"aad9a\">" + \
                               "<query xmlns=\"http://jabber.org/protocol/disco#info\">" + \
                               "<feature var=\"jabber:iq:version\"/>" + \
                               "<feature var=\"jabber:iq:register\"/>" + \
                               "<identity name=\"Jabber Mail Component\" category=\"headline\" type=\"mail\"/>" + \
                               "</query></iq>" + \
                               "</stream:stream>"]
        self.mail_component.run(1)
        self.failUnless(self.server.verify_queries())

#    def test_set_register(self):
#         self.server.responses = ["<?xml version='1.0'?><stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' id='4258238724' from='localhost'>", \
#                                  "<handshake/>" + \
#                                  "<iq from='test@localhost/test' to='jmc.localhost' type='set' id='aacaa'>" + \
#                                  "<query xmlns='jabber:iq:register'>" + \
#                                  "<x xmlns='jabber:x:data' type='submit'>" + \
#                                  "<field type='text-single' var='name'>" + \
#                                  "<value>test</value>" + \
#                                  "</field>" + \
#                                  "<field type='text-single' var='login'>" + \
#                                  "<value>logintest</value>" + \
#                                  "</field>" + \
#                                  "<field type='text-private' var='password'>" + \
#                                  "<value>passtest</value>" + \
#                                  "</field>" + \
#                                  "<field type='text-single' var='host'>" + \
#                                  "<value>hosttest</value>" + \
#                                  "</field>" + \
#                                  "<field type='text-single' var='port'>" + \
#                                  "<value>993</value>" + \
#                                  "</field>" + \
#                                  "<field type='list-single' var='type'>" + \
#                                  "<value>imaps</value>" + \
#                                  "</field>" + \
#                                  "<field type='text-single' var='mailbox'>" + \
#                                  "<value>INBOX</value>" + \
#                                  "</field>" + \
#                                  "<field type='list-single' var='ffc_action'>" + \
#                                  "<value>2</value>" + \
#                                  "</field>" + \
#                                  "<field type='list-single' var='online_action'>" + \
#                                  "<value>2</value>" + \
#                                  "</field>" + \
#                                  "<field type='list-single' var='away_action'>" + \
#                                  "<value>1</value>" + \
#                                  "</field>" + \
#                                  "<field type='list-single' var='ea_action'>" + \
#                                  "<value>1</value>" + \
#                                  "</field>" + \
#                                  "<field type='list-single' var='offline_action'>" + \
#                                  "<value>0</value>" + \
#                                  "</field>" + \
#                                  "<field type='text-single' var='interval'>" + \
#                                  "<value>5</value>" + \
#                                  "</field>" + \
#                                  "</x>" + \
#                                  "</query></iq>" + \
#                                  "<stream:stream>"]
#         self.server.queries = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + \
#                                "<stream:stream xmlns:stream=\"http://etherx.jabber.org/streams\" xmlns=\"jabber:component:accept\" to=\"jmc.localhost\" version=\"1.0\">", \
#                                "<handshake>[0-9abcdef]*</handshake>", \
#                                "<iq from=\"jmc.localhost\" to=\"test@localhost/Psi\" type=\"result\" id=\"aacaa\"/>",
#                                "<stream:stream>"]
#         self.mail_component.run(1)
#         self.failUnless(self.server.verify_queries())
    
class MailComponent_TestCase_Reg(unittest.TestCase):
    def setUp(self):
        self.mail_component = MailComponent(Config("tests/jmc-test.xml"))
        self.mail_component.set_register(iq = None)
        
    def test_get_reg_form_init(self):
        pass

    def test_get_reg_form_init_2pass(self):
        pass

    def test_disco_get_items(self):
        pass

    def test_get_register(self):
        pass

    def test_set_register_update(self):
        pass

    def test_set_register_remove(self):
        pass

    def test_presence_available_transport(self):
        pass

    def test_presence_available_mailbox(self):
        pass

    def test_presence_unavailable_transport(self):
        pass

    def test_presence_unavailable_mailbox(self):
        pass

    def test_presence_subscribe(self):
        pass

    def test_presence_subscribed_transport(self):
        pass

    def test_presence_subscribed_mailbox(self):
        pass

    def test_presence_unsubscribe(self):
        pass

    def test_presence_unsubscribed(self):
        pass

    def test_check_mail(self):
        pass
    
