##
## test_x.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Fri May 20 10:46:58 2005 
## $Id: test_x.py,v 1.1 2005/07/11 20:39:31 dax Exp $
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

import unittest
from jabber.x import *

class X_TestCase(unittest.TestCase):
    def setUp(self):
        self.mail_component = MailComponent()
        
    def test_get_form(self):
	    self.reg_form.add_field(type = "text-single", \
				    label = "Connection name", \
				    var = "name")
	    
	    self.reg_form.add_field(type = "text-single", \
				    label = "Login", \
				    var = "login")
	    
	    self.reg_form.add_field(type = "text-private", \
				    label = "password", \
				    var = "password")
	    
	    self.reg_form.add_field(type = "text-single", \
				    label = "Host", \
				    var = "host")

	    self.reg_form.add_field(type = "text-single", \
				    label = "Port", \
				    var = "port")
	    
	    field = self.reg_form.add_field(type = "list-single", \
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

	    self.reg_form.add_field(type = "text-single", \
				    label = "Mailbox (IMAP)", \
				    var = "mailbox", \
				    value = "INBOX")

	    self.reg_form.add_field(type = "boolean", \
				    label = "Retrieve mail", \
				    var = "retrieve")
        pass

