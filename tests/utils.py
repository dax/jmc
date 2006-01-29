##
## utils.py
## Login : David Rousselie <dax@happycoders.org>
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
import re

def xmldiff(node1, node2):
    if node1.nodeType == node1.TEXT_NODE:
        if not node2.nodeType == node2.TEXT_NODE \
               or re.compile(node2.data + "$").match(node1.data) is None:
            raise Exception("data in text node " + node1.data + " does not match " + node2.data)
    elif node1.nodeType == node1.DOCUMENT_NODE:
        if not node2.nodeType == node2.DOCUMENT_NODE:
            raise Exception("node1 is Document but not node2 (" + node2.nodeType + ")")
    elif node1.tagName != node2.tagName:
        raise Exception("Different tag name : " + node1.tagName + " != " + node2.tagName)
    else:
        for attr in node1._get_attributes().keys():
            if not node2.hasAttribute(attr) \
                   or node1.getAttribute(attr) != node2.getAttribute(attr):
                raise Exception("(" + node1.tagName + ") Different attributes : " + node1.getAttribute(attr) + " != " + node2.getAttribute(attr))
    if len(node1.childNodes) != len(node2.childNodes):
        raise Exception("(" + node1.tagName + ") Different children number : " + str(len(node1.childNodes)) + " != " + str(len(node2.childNodes)))
    for i in range(len(node1.childNodes)):
        xmldiff(node1.childNodes[i], node2.childNodes[i])

# def xmldiff(events1, events2):
#     for (event1, node1) in events1:
#         (event2, node2) = events2.next()
#         print event1 + " " + str(node1)
#         if not (event1 == event2) or not xml_diff_nodes(node1, node2):
#             return False
#     return True

if __name__ == "__main__":
    document1 = """\
    <slideshow attr='value'>
    <title>Demo slideshow</title>
    <slide><title>Slide title</title>
    <point>This is a demo</point>
    <point>Of a program for processing slides</point>
    </slide>
    
    <slide><title>Another demo slide</title>
    <point>It is important</point>
    <point>To have more than</point>
    <point>one slide</point>
    </slide>
    </slideshow>
    """
    
    document2 = """\
    <slideshow attr='value'>
    <title>Demo slideshow</title>
    <slide><title>Slide title</title>
    <point>This is a demo</point>
    <point>Of a program for processing slides</point>
    </slide>
    
    <slide><title>Another demo slide</title>
    <point>It is important</point>
    <point>To have more than</point>
    <point>one slide</point>
    </slide>
    </slideshow>
    """
    
    dom1 = xml.dom.minidom.parseString(document1)
    dom2 = xml.dom.minidom.parseString(document2)
    
    try:
        xmldiff(dom1, dom2)
    except Exception, msg:
        print msg
        
    
