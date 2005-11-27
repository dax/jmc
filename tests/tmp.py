import dummy_server

server = dummy_server.DummyServer(("localhost", 1143))
server.responses = ["* OK [CAPABILITY IMAP4 LOGIN-REFERRALS " + \
                    "AUTH=PLAIN]\r\n", \
                    lambda data: "* CAPABILITY IMAP4 " + \
                    "LOGIN-REFERRALS AUTH=PLAIN\r\n" + \
                    data.split()[0] + \
                    " OK CAPABILITY completed\r\n", \
                    lambda data: data.split()[0] + \
                    " OK LOGIN completed\r\n", \
                    lambda data: "* 42 EXISTS\r\n* 1 RECENT\r\n* OK" +\
                    " [UNSEEN 9]\r\n* FLAGS (\Deleted \Seen\*)\r\n*" +\
                    " OK [PERMANENTFLAGS (\Deleted \Seen\*)\r\n" + \
                    data.split()[0] + \
                    " OK [READ-WRITE] SELECT completed\r\n", \
                    lambda data: "* 1 FETCH ((RFC822) {12}\r\nbody text\r\n)\r\n" + \
                    data.split()[0] + " OK FETCH completed\r\n", \
                    lambda data: "* 1 FETCH (FLAGS (\UNSEEN))\r\n" + \
                    data.split()[0] + " OK STORE completed\r\n"]
server.queries = ["CAPABILITY", \
                  "LOGIN login \"pass\"", \
                  "SELECT INBOX", \
                  "FETCH 1 (RFC822)", \
                  "STORE 1 FLAGS (UNSEEN)", \
                  "LOGOUT"]
server.serve()
#server.verify_queries()
