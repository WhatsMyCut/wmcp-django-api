from constance.admin import ConstanceForm
from django import forms

from apps.general.validators import is_valid_email


class CustomConstanceAdminForm(ConstanceForm):
    def clean(self):
        cleaned_data = super().clean()

        # Validate STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL
        pairs = cleaned_data.get('STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL') or ''
        for pair in pairs.split(','):
            if not pair:
                continue
            try:
                email, raw_amount = pair.strip().split('=')
            except Exception:
                raise forms.ValidationError('Invalid {email}={amount$} pair of values in '
                                            'STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL: %s' % pair)
            if not is_valid_email(email.strip()):
                raise forms.ValidationError('Invalid "email" in STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL: %s' % email)
            try:
                int(raw_amount.strip().replace('$', ''))
            except Exception:
                raise forms.ValidationError('Invalid "amount" in STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL: %s'
                                            % raw_amount)
        return cleaned_data
