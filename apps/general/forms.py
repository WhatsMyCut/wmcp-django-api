from django import forms
from django.db.models import Q
from graphene.utils.str_converters import to_camel_case

from apps.account.models import ProxyUser
from apps.general.utils import lower
from apps.account.exceptions import AuthException
from apps.general.exceptions import InvalidParamException, ErrorDto
from apps.general.utils import get_modelclass_by_modelname
from apps.resident.models import Resident
from apps.property.models import PropertyActivationCode


def validate_form_raise_errors(form, exception_class=InvalidParamException):
    """ Use this helper in `schema.py` to validate a form and raise validation exception """
    form.is_valid()
    if form.errors:
        errors = [ErrorDto(key=x, message=form.errors[x][0]) for x in form.errors]
        raise exception_class(detail=errors[0].message, errors=errors)
    return form


class CustomCleanFieldsFormMixin:
    raise_unauthorized_for_invalid_resident = False
    INCONSISTENT_MODEL_NAMES = {
        'TypeOption': 'MassageTypeOption',
        'Partner': 'PartnerLocal',
    }

    def clean_primarykey(self, pk_field, cleaned_data):
        """
        Example:
            - given `duration_option_id`
            - get pk from `cleaned_data`
            - retrieve item from DB if exists
            - save it to `self.duration_option`
        """
        argname_base = pk_field.rsplit('_', maxsplit=1)[0]
        pk = cleaned_data.get(pk_field)
        if pk is None:
            setattr(self, argname_base, None)
            return
        modelname = argname_base[0].upper() + to_camel_case(argname_base)[1:]
        modelname = self.INCONSISTENT_MODEL_NAMES.get(modelname, modelname)
        modelclass = get_modelclass_by_modelname(modelname)
        obj = modelclass.objects.filter(id=pk).first()
        if obj is None:
            if self.raise_unauthorized_for_invalid_resident and modelclass == Resident:
                raise AuthException('Invalid resident id.')
            raise forms.ValidationError('Invalid %s: %i. Object does not exist.' % (pk_field, pk))
        setattr(self, argname_base, obj)
        return pk

    def clean_fields(self, cleaned_data):
        for field in getattr(self, 'fields', []):
            if field.endswith('_id'):
                self.clean_primarykey(field, cleaned_data)
            else:
                setattr(self, field, cleaned_data.get(field))

    def clean(self):
        cleaned_data = getattr(super(), 'clean')()
        self.clean_fields(cleaned_data)
        return cleaned_data


class ResidentForm(CustomCleanFieldsFormMixin, forms.Form):
    """ Validates `resident_id` PK value. If invalid, raises AuthException causing logout """

    raise_unauthorized_for_invalid_resident = True
    resident_id = forms.IntegerField(required=True)


class SafeResidentForm(ResidentForm):
    raise_unauthorized_for_invalid_resident = False


class ResidentPartnerLocalForm(ResidentForm):
    partner_local_id = forms.IntegerField(required=True)


class SafeResidentOnboardingForm(ResidentForm):
    raise_unauthorized_for_invalid_resident = False
    onboarding_code = forms.CharField(max_length=255, required=True)

    def clean(self):
        data = super().clean()
        if not PropertyActivationCode.objects.filter(
            resident__id=data['resident_id'], code=data['onboarding_code']).exists():
            raise forms.ValidationError("Invalid resident_id or onboarding_code")
        return data
