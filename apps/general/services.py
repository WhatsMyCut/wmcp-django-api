import pprint
from typing import List

import html2text
import mandrill
import pytz
from constance import config as dynamic_settings
from django.conf import settings
from django.core.mail import send_mail, get_connection, EmailMultiAlternatives
from django.template.loader import render_to_string
from exponent_server_sdk import PushClient
from exponent_server_sdk import PushMessage
from twilio.rest import Client as TwilioClient

from apps.general.loggers import sentry_logger
from apps.general.utils import in_tests


def get_mandrill_mailer():
    if getattr(settings, 'MANDRILL_API_KEY', None):
        client = mandrill.Mandrill(settings.MANDRILL_API_KEY)
        return MandrillEmailer(client, settings.MANDRILL_SUBACCOUNT)
    else:
        return MandrillEmailPrinter()


def get_sms_sender():
    if getattr(settings, 'TWILIO_ACCOUNT', None) and getattr(settings, 'TWILIO_API_KEY', None) and not in_tests():
        return TwilioSMSSender(account=settings.TWILIO_ACCOUNT, api_key=settings.TWILIO_API_KEY)
    else:
        return DevSMSSender()


def get_push_sender(force_real=False):
    return DevPushSender() if not force_real and (settings.DEBUG or in_tests()) else PushSender()


class TwilioSMSSender:
    def __init__(self, account, api_key):
        self._account = account
        self._api_key = api_key

    def send_sms(self, to, from_phone, text, messaging_service_sid=None):
        client = TwilioClient(self._account, self._api_key)
        return client.messages.create(to=to, from_=from_phone, body=text, messaging_service_sid=messaging_service_sid)


class DevSMSSender:
    def send_sms(self, to, from_phone, text, messaging_service_sid=None):
        if not getattr(settings, 'SUPPRESS_DEBUG_SMS', None):
            print('**** Sending DEBUG SMS ****')
            pprint.pprint(locals())
        return True


class PushSender:
    def send_push_message(self, token, message, extra=None, priority='high'):
        try:
            response = PushClient().publish(PushMessage(to=token, body=message, data=extra, priority=priority))
        except Exception as exc:
            # Encountered some likely formatting/validation error.
            if getattr(settings, 'DJANGO_SENTRY_URL', None):
                sentry_logger.exception('PushServerError: %s' % exc, exc_info=exc, extra={
                    'token': token,
                    'push_message': message,
                    'extra': extra,
                    'errors': getattr(exc, 'errors', None),
                    'response_data': getattr(exc, 'response_data', None),
                })
            raise

        try:
            # We got a response back, but we don't know whether it's an error yet.
            # This call raises errors so we can handle them with normal exception flows.
            response.validate_response()
        except Exception as exc:
            # Encountered some other per-notification error.
            push_response = getattr(exc, 'push_response', None)
            if getattr(settings, 'DJANGO_SENTRY_URL', None):
                sentry_logger.exception('PushResponseError or DeviceNotRegisteredError: %s' % exc, exc_info=exc, extra={
                    'token': token,
                    'push_message': message,
                    'extra': extra,
                    'push_response': push_response._asdict() if push_response else None,
                })
            raise


class DevPushSender:
    def send_push_message(self, token, message, extra=None):
        if not getattr(settings, 'SUPPRESS_DEBUG_PUSH_MESSAGES', None):
            print('**** Sending DEBUG PUSH MESSAGES ****')
            pprint.pprint(locals())
        return True


class BaseEmailer:
    def wrap_html(self, html_body, request):
        return render_to_string('general/email.html', {'body': html_body}, request)

    @staticmethod
    def split_email_and_name(email):
        """ Splits emails like "John Smith <john@smith.com>" into 2 variables:
            - John Smith
            - john@smith.com
        """
        if '<' not in email or '>' not in email:
            return email
        name, email2 = email.split('<')
        return name.strip(), email2.replace('>', '').strip()

    def _create_mandrill_message(self, from_email, to, variables, subject=None, attachments=None):
        message = {
            'from_email': from_email,
            'to': [{'email': to, 'type': 'to'}],
            'merge_language': 'handlebars',
            'merge_vars': [
                {
                    'rcpt': to,
                    'vars': variables
                }
            ],
            'subaccount': getattr(self, 'subaccount', ''),
        }
        if subject:
            message['subject'] = subject
        if attachments:
            message['attachments'] = attachments
        if '<' in from_email and '>' in from_email:
            from_name, from_email = self.split_email_and_name(from_email)
            message['from_email'] = from_email
            message['from_name'] = from_name
        return message


class Emailer(BaseEmailer):
    def send_email(self, subject, html_body, to):
        send_mail(subject, html2text.html2text(html_body), settings.DEFAULT_FROM_EMAIL, [to], html_message=html_body)

    def send_mass_email(self, data):
        """
        Send several emails using the same connection in the text and html format.
        Use settings.DEFAULT_FROM_EMAIL as sender email.

        :param list data: The list of tuples with structure (subject, html_body, to).
        :return: Number of emails sent.
        """
        connection = get_connection()
        messages = [self._make_email(connection, *x) for x in data]
        result = connection.send_messages(messages)
        connection.close()
        return result

    def _make_email(self, connection, subject, html_body, to):
        email = EmailMultiAlternatives(subject, html2text.html2text(html_body), settings.DEFAULT_FROM_EMAIL, [to],
                                       connection=connection)
        email.attach_alternative(html_body, 'text/html')
        return email


class MandrillEmailer(BaseEmailer):
    def __init__(self, client, subaccount):
        self.client = client
        self.subaccount = subaccount

    def send_email(self, from_email, to, template_name, variables, send_at=None, subject=None, attachments=None):
        message = self._create_mandrill_message(from_email, to, variables, subject, attachments)
        self.client.messages.send_template(
            template_name, template_content='', message=message, async=True, send_at=send_at)

    def send_plain_text_email(self, from_email, to, subject, text, send_at=None):
        message = self._create_mandrill_message(from_email, to, {}, subject)
        message['text'] = text
        self.client.messages.send(message=message, send_at=send_at)

    def cancel_email(self, email):
        if email is None:
            raise Exception("Tried to cancel all scheduled emails")

        emails = self.client.messages.list_scheduled(to=email)

        # This is a safety check to not cancel all our scheduled emails
        if len(emails) > 5:
            raise Exception("Tried to cancel too many emails")

        for email in emails:
            self.client.messages.cancel_scheduled(email['_id'])

    def create_send_at(self, dt):
        return dt.astimezone(pytz.utc).strftime('%Y-%m-%d %H:%M:%S')


class MandrillEmailPrinter(BaseEmailer):
    def send_email(self, from_email, to, template_name, variables, send_at=None, subject=None, attachments=None):
        message = self._create_mandrill_message(from_email=from_email, to=to, variables=variables, subject=subject,
                                                attachments=attachments)
        if not getattr(settings, 'SUPPRESS_DEBUG_EMAILS', None):
            pprint.pprint(message)

    def send_plain_text_email(self, from_email, to, subject, text, send_at=None):
        message = self._create_mandrill_message(from_email, to, {}, subject)
        message['text'] = text
        if not getattr(settings, 'SUPPRESS_DEBUG_EMAILS', None):
            pprint.pprint(message)

    def create_send_at(self, send_datetime):
        pass  # this is just a dummy wrapper for better *Emailer* classes compatibility

    def cancel_email(self, email):
        if email is None:
            raise Exception("Tried to cancel all scheduled emails")


def send_admin_error_notification(message: str, options: List[dict], subject: str):
    mandrill_data = [{
        'name': 'context',
        'content': {
            'message': message,
            'options': options
        }
    }]
    get_mandrill_mailer().send_email(
        from_email=dynamic_settings.CONCIERGE_EMAIL,
        to=dynamic_settings.CONCIERGE_EMAIL,
        template_name=dynamic_settings.MANDRILL_ERROR_NOTIFICATION_TEMPLATE,
        variables=mandrill_data,
        subject=subject
    )
