# -*- coding: utf-8 -*-
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
    def __init__(self, default_lang = "en"):
        self.default_lang = default_lang

    def get_lang_from_node(self, node):
        lang = node.getLang()
        if lang is None:
            print "Using default lang " + self.default_lang
            lang = self.default_lang
        return lang

    def get_lang_class(self, lang):
        return getattr(Lang, lang)

    def get_lang_class_from_node(self, node):
        return self.get_lang_class(self.get_lang_from_node(node))

    class en:
        register_title = u"Jabber Mail connection registration"
        register_instructions = u"Enter connection parameters"
        account_name = u"Connection name"
        account_login = u"Login"
        account_password = u"Password"
        account_password_store = u"Store password on Jabber server?"
        account_host = u"Host"
        account_port = u"Port"
        account_type = u"Mail server type"
        account_mailbox = u"Mailbox path (IMAP)"
        account_ffc_action = u"Action when state is 'Free For Chat'"
        account_online_action = u"Action when state is 'Online'"
        account_away_action = u"Action when state is 'Away'"
        account_xa_action = u"Action when state is 'Not Available'"
        account_dnd_action = u"Action when state is 'Do not Disturb'"
        account_offline_action = u"Action when state is 'Offline'"
        account_check_interval = u"Mail check interval (in minutes)"
        account_live_email_only = u"Reports only emails received while connected to Jabber"
        action_nothing = u"Do nothing"
        action_retrieve = u"Retrieve mail"
        action_digest = u"Send mail digest"
        update_title = u"Jabber mail connection update"
        update_instructions = u"Modifying connection '%s'"
        connection_label = u"%s connection '%s'"
        update_account_message_subject = u"Updated %s connection '%s'"
        update_account_message_body = u"Registered with username '%s' and " \
                                      "password '%s' on '%s'"
        new_account_message_subject = u"New %s connection '%s' created"
        new_account_message_body = u"Registered with " \
                                   "username '%s' and password '%s' on '%s'"
        ask_password_subject = u"Password request"
        ask_password_body = u"Reply to this message with the password " \
                            "for the following account: \n" \
                            "\thost = %s\n" \
                            "\tlogin = %s\n"
        password_saved_for_session = u"Password will be kept during your Jabber session"
        check_error_subject = u"Error while checking emails."
        check_error_body = u"An error appears while checking emails:\n\t%s"
        new_mail_subject = u"New email from %s"
        new_digest_subject = u"%i new email(s)"

    class fr:
        register_title = u"Enregistrement d'une nouvelle connexion à un serveur email."
        register_instructions = u"Entrer les paramètres de connexion"
        account_name = u"Nom de la connexion"
        account_login = u"Nom d'utilisateur"
        account_password = u"Mot de passe"
        account_password_store = u"Sauvegarder le mot de passe sur le serveur Jabber ?"
        account_host = u"Adresse du serveur email"
        account_port = u"Port du serveur email"
        account_type = u"Type du serveur email"
        account_mailbox = u"Chemin de la boîte email (IMAP)"
        account_ffc_action = u"Action lorsque l'état est 'Free For Chat'"
        account_online_action = u"Action lorsque l'état est 'Online'"
        account_away_action = u"Action lorsque l'état est 'Away'"
        account_xa_action = u"Action lorsque l'état est 'Not Available'"
        account_dnd_action = u"Action lorsque l'état est 'Do not Disturb'"
        account_offline_action = u"Action lorsque l'état est 'Offline'"
        account_check_interval = u"Interval de vérification de nouveaux emails (en minutes)"
        account_live_email_only = u"Vérifier les nouveaux emails seulement " \
                                  "lorsqu'une session Jabber est ouverte"
        action_nothing = u"Ne rien faire"
        action_retrieve = u"Récupérer l'email"
        action_digest = u"Envoyer un résumé"
        update_title = u"Mise à jour du compte JMC"
        update_instructions = u"Modification de la connexion '%s'"
        connection_label = u"Connexion %s '%s'"
        update_account_message_subject = u"La connexion %s '%s' a été mise à jour"
        update_account_message_body = u"Nom d'utilisateur : '%s'\nMot de passe : '%s'\nsur : '%s'"
        new_account_message_subject = u"La connexion %s '%s' a été créée"
        new_account_message_body = u"Nom d'utilisateur : '%s'\nMot de passe : '%s'\nsur : '%s'"
        ask_password_subject = u"Demande de mot de passe"
        ask_password_body = u"Répondre à ce message avec le mot de passe du " \
                            "compte suivant : \n" \
                            "\thost = %s\n" \
                            "\tlogin = %s\n"
        password_saved_for_session = u"Le mot de passe sera garder tout au " \
                                     "long de la session Jabber."
        check_error_subject = u"Erreur lors de la vérification des emails."
        check_error_body = u"Une erreur est survenue lors de la vérification " \
                           "des emails :\n\t%s"
        new_mail_subject = u"Nouvel email de %s"
        new_digest_subject = u"%i nouveau(x) email(s)"

    class nl:
        register_title = u"Registratie van verbindingen voor Jabber Mail"
        register_instructions = u"Instellingen voor verbinding"
        account_name = u"Accountnaam"
        account_login = u"Gebruikersnaam"
        account_password = u"Wachtwoord"
        account_password_store = u"Wachtwoord opslaan op Jabber-server?"
        account_host = u"Server"
        account_port = u"Poort"
        account_type = u"Soort account"
        account_mailbox = u"Pad naar mailbox (IMAP)"
        account_ffc_action = u"Actie bij aanwezigheid 'Chat'"
        account_online_action = u"Actie bij aanwezigheid 'Beschikbaar'"
        account_away_action = u"Actie bij aanwezigheid 'Afwezig'"
        account_xa_action = u"Actie bij aanwezigheid 'Langdurig afwezig'"
        account_dnd_action = u"Actie bij aanwezigheid 'Niet storen'"
        account_offline_action = u"Actie bij aanwezigheid 'Niet beschikbaar'"
        account_check_interval = u"Controle-interval (in minuten)"
        account_live_email_only = u"Enkel controleren op e-mails als er een" \
                                  "verbinding is met Jabber"
        action_nothing = u"Niets doen"
        action_retrieve = u"E-mail ophalen"
        action_digest = u"Samenvatting verzenden"
        update_title = u"Bijwerken van JMC"
        update_instructions = u"Verbinding '%s' aanpassen"
        connection_label = u"%s verbinding '%s'"
        update_account_message_subject = u"Verbinding %s '%s' werd bijgewerkt"
        update_account_message_body = u"Geregistreerd met gebruikersnaam '%s'"\
                                      "en wachtwoord '%s' op '%s'"
        new_account_message_subject = u"Nieuwe %s verbinding '%s' aangemaakt"
        new_account_message_body = u"Geregistreerd met " \
                                   "gebruikersnaam '%s' en wachtwoord '%s' op '%s'"
        ask_password_subject = u"Wachtwoordaanvraag"
        ask_password_body = u"Antwoord dit bericht met het volgende wachtwoord" \
                            "voor de volgende account: \n" \
                            "\thost = %s\n" \
                            "\tlogin = %s\n"
        password_saved_for_session = u"Het wachtwoord zal worden bewaard tijdens uw Jabber-sessie"
        check_error_subject = u"Fout tijdens controle op e-mails."
        check_error_body = u"Fout tijdens controle op e-mails:\n\t%s"
        new_mail_subject = u"Nieuwe e-mail van %s"
        new_digest_subject = u"%i nieuwe e-mail(s)"

    class es:
        register_title = u"Registro de nueva cuenta de email"
        register_instructions = u"Inserta los datos para la nueva cuenta"
        account_name = u"Nombre para la cuenta"
        account_login = u"Usuario (login)"
        account_password = u"Contraseña"
        account_password_store = u"¿Guardar la contraseña en el servidor Jabber?"
        account_host = u"Host"
        account_port = u"Puerto"
        account_type = u"Tipo de servidor Mail"
        account_mailbox = u"Ruta del mailbox (solo para IMAP)"
        account_ffc_action = u"Acción para cuando tu estado sea 'Listopara hablar'"
        account_online_action = u"Acción para cuando tu estado sea 'Conectado'"
        account_away_action = u"Acción para cuando tu estado sea 'Ausente'"
        account_xa_action = u"Acción para cuando tu estado sea 'No disponible'"
        account_dnd_action = u"Acción para cuando tu estado sea 'No molestar'"
        account_offline_action = u"Acción para cuando tu estado sea 'Desconectado'"
        account_check_interval = u"Intervalo para comprobar emails nuevos (en minutos)"
        account_live_email_only = u"Avisarme de emails nuevos solo cuando esté conectado"
        action_nothing = u"No hacer nada"
        action_retrieve = u"Mostrarme el email"
        action_digest = u"Enviar resúmen"
        update_title = u"Actualización de cuenta de email"
        update_instructions = u"Modifica los datos de la cuenta '%s'"
        connection_label = u"%s conexión '%s'"
        update_account_message_subject = u"Actualizada %s conexión '%s'"
        update_account_message_body = u"Registrado con el usuario '%s' y contraseña '%s' en '%s'"
        new_account_message_subject = u"Nueva %s conexión '%s' creada"
        new_account_message_body = u"Registrado con usuario '%s' y contraseña '%s' en '%s'"
        ask_password_subject = u"Petición de contraseña"
        ask_password_body = u"Para avisarte de emails nuevos, contesta a este mensaje con la contraseña " \
                            "de la cuenta: \n" \
                            "\tHost = %s\n" \
                            "\tUsuario = %s\n"
        password_saved_for_session = u"La contraseña será guardada para esta sesión únicamente."
        check_error_subject = u"Error al revisar los emails."
        check_error_body = u"Un error apareció al revisar los emails:\n\t%s"
        new_mail_subject = u"Nuevo email en %s"
        new_digest_subject = u"%i email(s) nuevo(s)"
