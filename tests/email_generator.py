##
# -*- coding: iso-8859-1 -*-
## email_generator.py
## Login : <adro8400@claralinux>
## Started on  Tue May 17 15:33:35 2005 adro8400
## $Id: email_generator.py,v 1.1 2005/07/11 20:39:31 dax Exp $
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

from email.Header import Header
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart

def _create_multipart(encoded):
    msg = MIMEMultipart()
    if encoded:
        part1 = MIMEText("Encoded multipart1 with 'iso-8859-15' charset (éàê)", \
                         _charset = "iso-8859-15")
        msg.attach(part1)
        part2 = MIMEText("Encoded multipart2 with 'iso-8859-15' charset (éàê)", \
                         _charset = "iso-8859-15")
        msg.attach(part2)
    else:
        part1 = MIMEText("Not encoded multipart1")
        msg.attach(part1)
        part2 = MIMEText("Not encoded multipart2")
        msg.attach(part2)
    return msg

def _create_singlepart(encoded):
    if encoded:
        return MIMEText("Encoded single part with 'iso-8859-15' charset (éàê)", \
                        _charset = "iso-8859-15")
    else:
        return MIMEText("Not encoded single part")

def generate(encoded, multipart, header):
    msg = None
    if multipart:
        msg = _create_multipart(encoded)
    else:
        msg = _create_singlepart(encoded)
    if header:
        if encoded:
            msg['Subject'] = Header("encoded subject (éàê)", "iso-8859-15")
            msg['From'] = Header("encoded from (éàê)", "iso-8859-15")
        else:
            msg['Subject'] = Header("not encoded subject")
            msg['From'] = Header("not encoded from")
    return msg

