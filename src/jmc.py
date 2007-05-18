##
## jmc.py
## Login : <dax@happycoders.org>
## Started on  Fri Jan 19 18:14:41 2007 David Rousselie
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

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

import jmc
from jmc.runner import JMCRunner

if __name__ == "__main__":
    runner = JMCRunner("Jabber Mail Component", jmc.version)
    runner.configure()
    runner.run()
