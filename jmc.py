#!/usr/bin/python -u
##
## Jabber Mail Component
## jmc.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Fri Jan  7 11:06:42 2005 
## $Id: jmc.py,v 1.3 2005/07/11 20:39:31 dax Exp $
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
import os.path
import logging

from jabber import mailconnection
from jabber.component import MailComponent, ComponentFatalError
from jabber.config import Config

def main(config_file = "jmc.xml", isDebug = 0):
    try:
        reload(sys)
        sys.setdefaultencoding('utf-8')
        del sys.setdefaultencoding
        logger = logging.getLogger()
        logger.addHandler(logging.StreamHandler())
        if isDebug > 0:
            logger.setLevel(logging.DEBUG)
        try:
	    logger.debug("Loading config file " + config_file)
            config = Config(config_file)
        except:
            print >>sys.stderr, "Couldn't load config file:", \
		str(sys.exc_value)
            sys.exit(1)

        mailconnection.default_encoding = config.get_content("config/mail_default_encoding")
        print "creating component..."
        mailcomp = MailComponent(config.get_content("config/jabber/service"), \
                                 config.get_content("config/jabber/secret"), \
                                 config.get_content("config/jabber/server"), \
                                 int(config.get_content("config/jabber/port")), \
                                 config.get_content("config/jabber/language"), \
                                 int(config.get_content("config/check_interval")), \
                                 config.get_content("config/spooldir"), \
                                 config.get_content("config/storage"))

        print "starting..."
        mailcomp.run(1)
    except ComponentFatalError,e:
        print e
        print "Aborting."
        sys.exit(1)

if __name__ == "__main__":
    var_option = 0
    file_num = 0
    index = 0
    debug_level = 0
    for opt in sys.argv:
        if var_option == 0 and len(opt) == 2 and opt == "-c":
            var_option += 1
        elif (var_option & 1) == 1 and len(opt) > 0:
            var_option += 1
            file_num = index
        if len(opt) == 2 and opt == "-D":
            debug_level = 1
        index += 1
    if (var_option & 2) == 2:
        main(sys.argv[file_num], debug_level)
    else:
        main("jmc.xml", debug_level)

