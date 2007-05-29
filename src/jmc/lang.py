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

import jcl.lang


class Lang(jcl.lang.Lang):
    class en(jcl.lang.Lang.en):
        register_title = u"Jabber Mail connection registration"
        component_name = u"Jabber Mail Component"

        field_login = u"Login"
        field_password = u"Password"
        field_host = u"Host"
        field_port = u"Port"
        field_ssl = u"Secure connection (SSL)"
        field_store_password = u"Store password on Jabber server?"
        field_live_email_only = u"Reports only emails received while connected to Jabber"
        field_interval = u"Mail check interval (in minutes)"
        field_mailbox = u"Mailbox path"

        field_action_1 = u"Retrieve digest"
        field_chat_action_1 = field_action_1
        field_online_action_1 = field_action_1
        field_away_action_1 = field_action_1
        field_xa_action_1 = field_action_1
        field_dnd_action_1 = field_action_1
        field_offline_action_1 = field_action_1

        field_action_2 = u"Retrieve full email"
        field_chat_action_2 = field_action_2
        field_online_action_2 = field_action_2
        field_away_action_2 = field_action_2
        field_xa_action_2 = field_action_2
        field_dnd_action_2 = field_action_2
        field_offline_action_2 = field_action_2

        new_mail_subject = u"New email from %s"
        new_digest_subject = u"%i new email(s)"

        type_imap_name = u"IMAP accounts"
        type_pop3_name = u"POP3 accounts"

        send_mail_error_no_to_header_subject = u"No header \"TO\" found"
        send_mail_error_no_to_header_body = u"No header \"TO\" found in receive message.\n" \
            u"Please use following syntax to specify destination email address:\n" \
            u"TO: user@test.com\n"
        send_mail_ok_subject = u"Email sent"
        send_mail_ok_body = u"Your email was sent to %s."

    class fr(jcl.lang.Lang.fr):
        component_name = u"Jabber Mail Component"
        register_title = u"Enregistrement d'une nouvelle connexion à un " \
                         u"serveur email."

        field_login = u"Nom d'utilisateur"
        field_password = u"Mot de passe"
        field_host = u"Adresse du serveur email"
        field_port = u"Port du serveur email"
        field_ssl = u"Connexion sécurisé (SSL)"
        field_store_password = u"Sauvegarder le mot de passe sur le serveur Jabber ?"
        field_live_email_only = u"Vérifier les nouveaux emails seulement " \
            "lorsqu'une session Jabber est ouverte"
        field_interval = u"Interval de vérification de nouveaux emails (en minutes)"
        field_mailbox = u"Chemin de la boîte email"

        field_action_1 = u"Envoyer un résumé"
        field_chat_action_1 = field_action_1
        field_online_action_1 = field_action_1
        field_away_action_1 = field_action_1
        field_xa_action_1 = field_action_1
        field_dnd_action_1 = field_action_1
        field_offline_action_1 = field_action_1

        field_action_2 = u"Envoyer l'email complet"
        field_chat_action_2 = field_action_2
        field_online_action_2 = field_action_2
        field_away_action_2 = field_action_2
        field_xa_action_2 = field_action_2
        field_dnd_action_2 = field_action_2
        field_offline_action_2 = field_action_2

        new_mail_subject = u"Nouvel email de %s"
        new_digest_subject = u"%i nouveau(x) email(s)"

        type_imap_name = u"comptes IMAP"
        type_pop3_name = u"comptes POP3"

        send_mail_error_no_to_header_subject = u"L'en-tête \"TO\" n'a pas été "\
            u"trouvé"
        send_mail_error_no_to_header_body = u"L'en-tête \"TO\" n'a pas été " \
            u"trouvé dans le message envoyé.\n" \
            u"Utiliser la syntax suivante pour spécifier l'adresse email du " \
            u"destinataire :\nTO: user@test.com\n"
        send_mail_ok_subject = u"Email envoyé"
        send_mail_ok_body = u"Votre email a été envoyé à %s."

    class nl(jcl.lang.Lang.nl):
        # TODO: when finish, delete this line and uncomment in tests/lang.py the makeSuite(Language_nl_TestCase, 'test') line
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
                                      u"en wachtwoord '%s' op '%s'"
        new_account_message_subject = u"Nieuwe %s verbinding '%s' aangemaakt"
        new_account_message_body = u"Geregistreerd met " \
                                   u"gebruikersnaam '%s' en wachtwoord '%s' op '%s'"
        ask_password_subject = u"Wachtwoordaanvraag"
        ask_password_body = u"Antwoord dit bericht met het volgende wachtwoord" \
                            u"voor de volgende account: \n" \
                            u"\thost = %s\n" \
                            u"\tlogin = %s\n"
        password_saved_for_session = u"Het wachtwoord zal worden bewaard tijdens uw Jabber-sessie"
        check_error_subject = u"Fout tijdens controle op e-mails."
        check_error_body = u"Fout tijdens controle op e-mails:\n\t%s"
        new_mail_subject = u"Nieuwe e-mail van %s"
        new_digest_subject = u"%i nieuwe e-mail(s)"

    class es(jcl.lang.Lang.es):
        # TODO: when finish, delete this line and uncomment in tests/lang.py the makeSuite(Language_es_TestCase, 'test') line
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

    class pl(jcl.lang.Lang.pl):
        # TODO: when finish, delete this line and uncomment in tests/lang.py the makeSuite(Language_pl_TestCase, 'test') line
        register_title = u"Rejestracja w komponencie E-Mail"
        register_instructions = u"Wprowadź parametry połączenia"
        account_name = u"Nazwa połączenia"
        account_login = u"Nazwa użytkownika"
        account_password = u"Hasło"
        account_password_store = u"Zachować hasło na serwerze Jabbera? "
        account_host = u"Nazwa hosta"
        account_port = u"Port"
        account_type = u"Typ serwera email"
        account_mailbox = u"Ścieżka do skrzynki odbiorczej (IMAP)"
        account_ffc_action = u"Akcja gdy status to 'Chętny do rozmowy'"
        account_online_action = u"Akcja gdy status to 'Dostępny'"
        account_away_action = u"Akcja gdy status to 'Zaraz wracam'"
        account_xa_action = u"Akcja gdy status to 'Niedostępny'"
        account_dnd_action = u"Akcja gdy status to 'Nie przeszkadzać'"
        account_offline_action = u"Akcja gdy status to 'Rozłączony'"
        account_check_interval = u"Sprawdzaj email co (w minutach)"
        account_live_email_only = u"Raportuj otrzymane emaile tylko\n gdy podłączony do Jabbera"
        action_nothing = u"Nic nie rób"
        action_retrieve = u"Pobierz emaila"
        action_digest = u"Wyślij zarys emaila"
        update_title = u"Modyfikacja połączenia z komponentem mailowym"
        update_instructions = u"Modyfikacja połączenia '%s'"
        connection_label = u"%s połączenie '%s'"
        update_account_message_subject = u"Zmodyfikowane %s połączenie '%s'"
        update_account_message_body = u"Zarejestrowany z nazwą użytkownika '%s' i hasłem '%s' na '%s'"
        new_account_message_subject = u"Nowe %s połączenie '%s' utworzone"
        new_account_message_body = u"Zarejestrowany z nazwą użytkownika '%s' i hasłem '%s' na '%s'"
        ask_password_subject = u"Żądanie hasła"
        ask_password_body = u"Odpowiedz na ta wiadomosc z hasłem dla podanego konta: \n" \
                            "\tnazwa hosta = %s\n" \
                            "\tnazwa uzytkownika = %s\n"
        password_saved_for_session = u"Hasło będzie przechowywane podczas Twojej sesji Jabbera"
        check_error_subject = u"Błąd podczas sprawdzania emaili."
        check_error_body = u"Pojawił się błąd podczas sprawdzania emaili:\n\t%s"
        new_mail_subject = u"Nowy email od %s"
        new_digest_subject = u"%i nowy(ch) email(i)"

    class cs(jcl.lang.Lang.cs):
        # TODO: when finish, delete this line and uncomment in tests/lang.py the makeSuite(Language_cs_TestCase, 'test') line
        register_title = u"Jabber MailNotify registrace"
        register_instructions = u"Vložte nastavení spojení"
        account_name = u"Název spojení"
        account_login = u"Přihlašovací jméno"
        account_password = u"Heslo"
        account_password_store = u"Uložit heslo na Jabber serveru?"
        account_host = u"Poštovní server"
        account_port = u"Port"
        account_type = u"Typ poštovního serveru"
        account_mailbox = u"Cesta IMAP schránky"
        account_ffc_action = u"Akce při statusu 'Ukecaný'"
        account_online_action = u"Akce při statusu 'Přítomen'"
        account_away_action = u"Akce při statusu 'Pryč'"
        account_xa_action = u"Akce při statusu 'Nepřítomen'"
        account_dnd_action = u"Akce při statusu 'Nerušit'"
        account_offline_action = u"Akce při statusu 'Odpojen'"
        account_check_interval = u"Interval kontroly pošty (v minutách)"
        account_live_email_only = u"Informuj pouze o emailech, které přišly během připojení k Jabberu"
        action_nothing = u"Nedělej nic"
        action_retrieve = u"Přijmi poštu"
        action_digest = u"Pošli upozornění na novou poštu"
        update_title = u"Jabber - aktualizace spojení k emailu"
        update_instructions = u"Aktualizace spojení '%s'"
        connection_label = u"%s spojení '%s'"
        update_account_message_subject = u"Aktualizováno %s spojení '%s'"
        update_account_message_body = u"Registrováno s přihlašovacím jménem '%s' a " \
                                      u"heslem '%s' v '%s'"
        new_account_message_subject = u"Nové spojení %s '%s' aktualizováno"
        new_account_message_body = u"Registrováno " \
                                   u"s přihlašovacím jménem '%s' a heslem '%s' v '%s'"
        ask_password_subject = u"Žádost o heslo"
        ask_password_body = u"Odpovězte na tuto zprávu posláním hesla " \
                            u"pro následující spojení: \n" \
                            u"\thost = %s\n" \
                            u"\tlogin = %s\n"
        password_saved_for_session = u"Heslo bude uchováno během vašeho připojení k Jabberu"
        check_error_subject = u"Chyba při kontrole emailů."
        check_error_body = u"Nějaká chyba nastala při kontrole emailů:\n\t%s"
        new_mail_subject = u"Nový email od %s"
        new_digest_subject = u"%i má nový(é) email(y)"

    class ru:
        # TODO: when finish, delete this line and uncomment in tests/lang.py the makeSuite(Language_ru_TestCase, 'test') line
        register_title = u"Учетные данные соединения"
        register_instructions = u"Введите данные для соединения"
        account_name = u"Имя соединения"
        account_login = u"Логин@gmail.ru"
        account_password = u"Пароль"
        account_password_store = u"Сохранять пароль на сервере?"
        account_host = u"Хост"
        account_port = u"Порт (обычно, 110)"
        account_type = u"Тип учетной записи"
        account_mailbox = u"Путь к почтовому ящику (IMAP)"
        account_ffc_action = u"Действие для состояния 'Free For Chat'"
        account_online_action = u"Действие для состояния 'Online'"
        account_away_action = u"Действие для состояния 'Away'"
        account_xa_action = u"Действие для состояния 'Not Available'"
        account_dnd_action = u"Действие для состояния 'Do not Disturb'"
        account_offline_action = u"Действие для состояния 'Offline'"
        account_check_interval = u"Интервал проверки почты (в минутах)"
        account_live_email_only = u"Сообщать о письмах только на момент подключения"
        action_nothing = u"Не делать ничего"
        action_retrieve = u"Показать почту"
        action_digest = u"Показать уведомление"
        update_title = u"Уточнение параметров"
        update_instructions = u"Изменяем соединение '%s'"
        connection_label = u"%s соединение '%s'"
        update_account_message_subject = u"Данные для  %s обновлены '%s'"
        update_account_message_body = u"Зарегистрирован с логином '%s' и " \
                                      u"паролем '%s' на '%s'"
        new_account_message_subject = u"Новое %s соединение '%s' создано"
        new_account_message_body = u"Перерегистрирован с " \
                                   u"логином '%s' и паролем '%s' на '%s'"
        ask_password_subject = u"Запрос пароля"
        ask_password_body = u"Ответьте на это сообщение с паролем " \
                            u"для следующей учетной записи: \n" \
                            u"\tХост = %s\n" \
                            u"\tЛогин = %s\n"
        password_saved_for_session = u"Пароль будет сохранен только на время Вашей сессии."
        check_error_subject = u"Ошибка при проверке почты."
        check_error_body = u"Возникла ошибка при проверке почты:\n\t%s"
        new_mail_subject = u"Новая почта от %s"
        new_digest_subject = u"%i новое(ые) письмо(а)"
