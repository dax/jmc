##
## dummy_server.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Fri May 13 12:53:17 2005
## $Id: dummy_server.py,v 1.1 2005/07/11 20:39:31 dax Exp $
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
import time
import traceback
import re
import os
import socket
import types
import select
import xml.dom.minidom
from pyxmpp import xmlextra

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

class DummyServer:
    def __init__(self, host, port, responses = None):
        for res in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
            except socket.error, msg:
                print >>sys.stderr, msg
                s = None
                raise socket.error
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(sa)
                s.listen(1)
            except socket.error, msg:
                print >>sys.stderr, msg
                s.close()
                s = None
                raise socket.error
            break
        self.socket = s
        self.responses = None
        self.queries = None
        self.real_queries = []

    def serve(self):
        conn = None
        try:
            conn, addr = self.socket.accept()
            rfile = conn.makefile('rb', -1)
            if self.responses:
                data = None
                for idx in range(len(self.responses)):
                    # if response is a function apply it (it must return a string)
                    # it is given previous received data
                    if isinstance(self.responses[idx], types.FunctionType):
                        response = self.responses[idx](data)
                    else:
                        response = self.responses[idx]
                    if response is not None:
                        #print >>sys.stderr, 'Sending : ', response
                        conn.send(response)
                    data = rfile.readline()
                    if not data:
                        break
                    else:
                        self.real_queries.append(data)
                        #print >>sys.stderr, 'Receive : ', data
            if conn is not None:
                conn.close()
            if self.socket is not None:
                self.socket.close()
                self.socket = None
        except:
            type, value, stack = sys.exc_info()
            print >>sys.stderr, "".join(traceback.format_exception
                                        (type, value, stack, 5))

    def verify_queries(self):
        result = True
        queries_len = len(self.queries)
        if queries_len == len(self.real_queries):
            for idx in range(queries_len):
                real_query = self.real_queries[idx]
                match = (re.compile(self.queries[idx], re.M).match(real_query) is not None)
                if not match:
                    result = False
                    print >>sys.stderr, "Unexpected query :\n" + \
                          "Expected query : _" + self.queries[idx] + "_\n" + \
                          "Receive query : _" + real_query + "_\n"
        else:
            result = False
            print >>sys.stderr, "Expected " + str(queries_len) + \
                  " queries, got " + str(len(self.real_queries)) + \
                  "\t" + str(self.real_queries)
        return result

class XMLDummyServer(DummyServer):
    def __init__(self, host, port, responses, stream_handler):
        DummyServer.__init__(self, host, port, responses)
        self._reader = xmlextra.StreamReader(stream_handler)

    def serve(self):
        try:
            conn, addr = self.socket.accept()
            if self.responses:
                data = None
                for idx in range(len(self.responses)):
                    try:
                        # This approximation is not clean
                        # received size is based on the expected size in self.queries
                        data = conn.recv(1024 + len(self.queries[idx]))
#                        print "receive : " + data
                        if data:
                            #print "-----------RECEIVE1 " + data
                            r = self._reader.feed(data)
                    except:
                        type, value, stack = sys.exc_info()
                        print "".join (traceback.format_exception
                                       (type, value, stack, 5))
                        raise
                    if data:
                        self.real_queries.append(data)
                    # if response is a function apply it (it must return a string)
                    # it is given previous received data
                    if isinstance(self.responses[idx], types.FunctionType):
                        response = self.responses[idx](data)
                    else:
                        response = self.responses[idx]
                    if response is not None:
#                        print >>sys.stderr, '---------SENDING : ', response
                        conn.send(response)
                data = conn.recv(1024)
                if data:
#                    print "-----------RECEIVE2 " + data
                    r = self._reader.feed(data)
                    self.real_queries.append(data)
                conn.close()
                self.socket.close()
                self.socket = None
        except:
            type, value, stack = sys.exc_info()
            print "".join (traceback.format_exception
                           (type, value, stack, 5))
            raise

    def verify_queries(self):
        result = True
        full_real_queries = ""
        full_recv_queries = ""
        for idx in range(len(self.real_queries)):
            full_real_queries += self.real_queries[idx].rstrip(os.linesep)
        for idx in range(len(self.queries)):
            full_recv_queries += self.queries[idx].rstrip(os.linesep)
        # Do not receive it but add it so that xml parsing can succeed
        #full_real_queries += "</stream:stream>"
        real_query = xml.dom.minidom.parseString(full_real_queries)
        recv_query = xml.dom.minidom.parseString(full_recv_queries)
        try:
            utils.xmldiff(real_query, recv_query)
        except Exception, msg:
            result = False
            print >>sys.stderr, msg
        return result

def test():
    server = DummyServer(("localhost", 4242))
    server.responses = ["rep1\n", "rep2\n"]
    server.serve()

if __name__ == '__main__':
    test()
