##
## disco.py
## Login : David Rousselie <dax@happycoders.org>
## Started on  Sun Jul  8 20:55:46 2007 David Rousselie
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

from jcl.jabber.command import CommandRootDiscoGetInfoHandler

class MailRootDiscoGetInfoHandler(CommandRootDiscoGetInfoHandler):
    def handle(self, stanza, lang_class, node, disco_obj, data):
        """Add jabber:iq:gateway support"""
        disco_infos = CommandRootDiscoGetInfoHandler.handle(self, stanza, lang_class,
                                                            node, disco_obj, data)
        disco_infos[0].add_feature("jabber:iq:gateway")
        disco_infos[0].add_identity(self.component.name, "headline", "newmail")
        return disco_infos
