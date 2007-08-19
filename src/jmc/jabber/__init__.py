"""Jabber component classes"""
__revision__ = ""

import re

from jcl.jabber import Handler
import jcl.model.account as account

from jmc.model.account import NoAccountError, SMTPAccount

class MailHandler(Handler):
    """Define filter for email address in JID"""

    def __init__(self, component):
        Handler.__init__(self, component)
        self.dest_jid_regexp = re.compile(".*%.*")

    def filter(self, stanza, lang_class):
        """Return empty array if JID match '.*%.*@componentJID'"""
        node = stanza.get_to().node
        if node is not None and self.dest_jid_regexp.match(node):
            bare_from_jid = unicode(stanza.get_from().bare())
            accounts = account.get_accounts(bare_from_jid, SMTPAccount)
            if accounts.count() == 0:
                raise NoAccountError()
            else:
                default_account = accounts.newClause(\
                    SMTPAccount.q.default_account == True)
                if default_account.count() > 0:
                    return default_account
                else:
                    return accounts
        return None
