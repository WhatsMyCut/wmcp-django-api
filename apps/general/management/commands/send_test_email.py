#
# Only run this management command manually
# After you run the script and enter the email, you should receive 2 emails -
#  one from Django's standard method, another one from Mandrill
#

import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.general.services import Emailer as DjangoEmailer, get_mandrill_mailer


class Command(BaseCommand):
    def handle(self, *args, **options):
        to = input("Enter email address to send the test emails to: ")
        if not to:
            print("You did not enter email - exit")
            sys.exit(1)
        django_emailer = DjangoEmailer()
        django_emailer.send_email(
            to=to,
            subject="Test email from Django Emailer",
            html_body="<h1>Caption</h1><p><i>Test HTML text</i></p>")
        mandrill_emailer = get_mandrill_mailer()
        mandrill_emailer.send_email(
            settings.DEFAULT_FROM_EMAIL,
            to,
            'Email 5 - Membership Renew',
            {},
            subject="Test email from Mandrill Emailer")
