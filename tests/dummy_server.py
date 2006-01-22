##
## dummy_server.py
## Login : <adro8400@claralinux>
## Started on  Fri May 13 12:53:17 2005 adro8400
## $Id: dummy_server.py,v 1.1 2005/07/11 20:39:31 dax Exp $
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

import sys
import time
import traceback
import re
import os
import socket
import types
import select
import xml.dom.minidom
import utils
from pyxmpp import xmlextra

class DummyServer:
    def __init__(self, host, port, responses = None):
        for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                s = socket.socket(af, socktype, proto)
            except socket.error, msg:
                s = None
                continue
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(sa)
                s.listen(1)
            except socket.error, msg:
                s.close()
                s = None
                continue
            break
        self.socket = s
        self.responses = None
        self.queries = None
        self.real_queries = []
        
    def serve(self):
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
#                    print >>sys.stderr, 'Sending : ', response
                    conn.send(response)
                data = rfile.readline()
                if not data:
                    break
                else:
                    self.real_queries.append(data)
#                    print >>sys.stderr, 'Receive : ', data
        conn.close()
        self.socket.close()
        self.socket = None

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
                  " queries, got " + str(len(self.real_queries))
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
                        # TODO : this approximation is not clean
                        # received size is based on the expected size in self.queries
                        data = conn.recv(1024 + len(self.queries[idx]))
                        print "receive : " + data
                        if data:
                            ## TODO : without this log, test_set_register in test_component wait forever
                            #print "-----------RECEIVE1 " + data
                            r = self._reader.feed(data)
                    except:
                        type, value, stack = sys.exc_info()
                        print "".join (traceback.format_exception 
                                       (type, value, stack, 5))
                        raise
                    # TODO verify got all data </stream>
                    if data:
                        self.real_queries.append(data)
                    # if response is a function apply it (it must return a string)
                    # it is given previous received data
                    if isinstance(self.responses[idx], types.FunctionType):
                        response = self.responses[idx](data)
                    else:
                        response = self.responses[idx]
                    if response is not None:
                        print >>sys.stderr, '---------SENDING : ', response
                        conn.send(response)
                data = conn.recv(1024)
                if data:
                    print "-----------RECEIVE2 " + data
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
            full_recv_queries += self.queries[idx].rstrip(os.linesep)
        # Do not receive it but add it so that xml parsing can succeed
        #full_real_queries += "</stream:stream>"
        print full_real_queries
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
    

