##
## lang.py
## Login : David Rousselie <david.rousselie@happycoders.org>
## Started on  Sat Jan 28 16:37:11 2006 David Rousselie
## $Id$
## 
## Copyright (C) 2006 David Rousselie
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


class Lang:
    class en:
        register_title = u"Jabber Mail connection registration"
        register_instructions = u"Enter connection parameters"
        account_name = u"Connection name"
        account_login = u"Login"
        account_password = u"Password"
        account_host = u"Host"
        account_port = u"Port"
        account_type = u"Mail serveur type"
        account_mailbox = u"Mailbox path (IMAP)"
        account_ffc_action = u"Action when state is 'Free For Chat'"
        account_online_action = u"Action when state is 'Online'"
        account_away_action = u"Action when state is 'Away'"
        account_xa_action = u"Action when state is 'Not Available'"
        account_dnd_action = u"Action when state is 'Do not Disturb'"
        account_offline_action = u"Action when state is 'Offline'"
        account_check_interval = u"Mail check interval (in minutes)"
        action_nothing = u"Do nothing"
        action_retrieve = u"Retrieve mail"
        action_digest = u"Send mail digest"
        update_title = u"Jabber mail connection update"
        update_instructions = u"Modifying connection "
        connection = u" connection "
        update_account_message = u"Updated %s connection '%s': Registered with "\
                                 "username '%s' and password '%s' on '%s'"
        new_account_message = u"New %s connection '%s': Registered with " \
                              "username '%s' and password '%s' on '%s'"
        
    class fr:
        register_title = u"Enregistrement d'une nouvelle connexion à un serveur email."
        register_instructions = u"Entrer les paramètres de connexion"
        # TODO
        account_name = u"Connection name"
        account_login = u"Login"
        account_password = u"Password"
        account_host = u"Host"
        account_port = u"Port"
        account_type = u"Mail serveur type"
        account_mailbox = u"Mailbox path (IMAP)"
        account_ffc_action = u"Action when state is 'Free For Chat'"
        account_online_action = u"Action when state is 'Online'"
        account_away_action = u"Action when state is 'Away'"
        account_xa_action = u"Action when state is 'Not Available'"
        account_dnd_action = u"Action when state is 'Do not Disturb'"
        account_offline_action = u"Action when state is 'Offline'"
        account_check_interval = u"Mail check interval (in minutes)"
        action_nothing = u"Do nothing"
        action_retrieve = u"Retrieve mail"
        action_digest = u"Send mail digest"
        update_title = u"Jabber mail connection update"
        update_instructions = u"Modifying connection "
        connection = u" connection "
        update_account_message = u"Updated %s connection '%s': Registered with "\
                                 "username '%s' and password '%s' on '%s'"
        new_account_message = u"New %s connection '%s': Registered with " \
                              "username '%s' and password '%s' on '%s'"

    
