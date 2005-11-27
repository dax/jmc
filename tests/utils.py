##
## utils.py
## Login : <dax@happycoders.org>
## Started on  Mon Oct 24 21:44:43 2005 dax
## $Id$
## 
## Copyright (C) 2005 dax
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

import xml.dom.minidom

#document = "<stream:stream xmlns:stream='http://etherx.jabber.org/streams' xmlns='jabber:component:accept' id='4258238724' from='localhost'>"
# document = """\
# <slideshow attr='value'>
# <title>Demo slideshow</title>
# <slide><title>Slide title</title>
# <point>This is a demo</point>
# <point>Of a program for processing slides</point>
# </slide>

# <slide><title>Another demo slide</title>
# <point>It is important</point>
# <point>To have more than</point>
# <point>one slide</point>
# </slide>
# </slideshow>
# """

# document1 = """\
# <slideshow attr='value'>
# <title>Demo slideshow</title>
# <slide><title>Slide title</title>
# <point>This is a demo</point>
# <point>Of a program for processing slides</point>
# </slide>

# <slide><title>Another demo slide</title>
# <point>It is important1</point>
# <point>To have more than</point>
# <point>one slide</point>
# </slide>
# </slideshow>
# """

#dom = xml.dom.minidom.parseString(document)
#dom1 = xml.dom.minidom.parseString(document)

# def getText(nodelist):
#     rc = ""
#     for node in nodelist:
#         if node.nodeType == node.TEXT_NODE:
#             rc = rc + node.data
#     return rc

def xmldiff(node1, node2):
    if node1.nodeType == node1.TEXT_NODE:
        if not node2.nodeType == node2.TEXT_NODE \
               or node1.data != node2.data:
            return False
    elif node1.nodeType == node1.DOCUMENT_NODE:
        if not node2.nodeType == node2.DOCUMENT_NODE:
            return False
    elif node1.tagName != node2.tagName:
        return False
    else:
        for attr in node1._get_attributes().keys():
            if not node2.hasAttribute(attr) \
                   or node1.getAttribute(attr) != node2.getAttribute(attr):
                return False
    for i in range(len(node1.childNodes)):
        if not xmldiff(node1.childNodes[i], node2.childNodes[i]):
            return False
    return True

#print xmldiff(dom, dom1)

# def nodediff(node1, node2):
#     if not node1.name == node2.name:
#         return False
#     for properties in node1.properties:
#         if node2.hasAttribute(attr):

# def xmldiff(xpath, node1, node2):
#     if not nodediff(node1, node2):
#         return False
#     for child in node1.children:
    
