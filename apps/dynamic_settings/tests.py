import datetime

import graphene
from constance import config
from django.contrib.auth.models import Group
from django.test import TestCase, RequestFactory
from django.urls import reverse
from graphene.test import Client
from model_mommy import mommy

from apps.account.models import ProxyUser
from apps.dynamic_settings.constance_settings import CONSTANCE_CONFIG
from apps.dynamic_settings.utils import DynamicSettingsUtils
from apps.general.graphql import format_error
from apps.property.models import PropertyManagementCompany, CustomerSegment, Property, PropertyContract
from apps.resident.models import Resident


class DynamicSettingsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        from apps.dynamic_settings import schema as app_schema

        class TestQuery(app_schema.Query, graphene.ObjectType):
            pass

        cls.test_schema = graphene.Schema(query=TestQuery)

        cls.pmc = PropertyManagementCompany.objects.create(name='pmc')
        cls.cs = CustomerSegment.objects.create(
            name='cs', registration_email_text='a', resident_onboarding_email_text='b')
        cls.property = mommy.make(Property, name='p', company=cls.pmc, customer_segment=cls.cs, logo=None,
                                  market__name='market')
        cls.property_contract = PropertyContract.objects.create(
            property=cls.property, quantity=1, expiration=datetime.date.today() + datetime.timedelta(days=1))
        cls.user = ProxyUser.objects.create(username='abc@email.com')
        cls.resident = Resident.objects.create(
            email='email1', property=cls.property, property_contract=cls.property_contract, user=cls.user)

    def setUp(self):
        self.client = Client(self.test_schema, format_error=format_error)
        self.request = RequestFactory().post(reverse('graphql_endpoint'))
        self.request.user = self.user
        self._reset_constance_settings_to_default()

    def test_get_public_dynamic_settings(self):
        query = """
            query q {
                siteSettings {
                    FeatureCleaningEnabled
                    FeatureRecurrentSchedulingEnabled
                }
            }
        """
        site_settings = self._execute_site_settings_api_schema(req_string=query, context=self.request)
        self.assertEqual(
            site_settings, {
                'FeatureCleaningEnabled': True,
                'FeatureRecurrentSchedulingEnabled': True,
            }
        )
        query = """
            query q {
                siteSettings {
                    GoogleApiCredentials
                }
            }
        """
        is_error = False
        try:
            self._execute_site_settings_api_schema(req_string=query, context=self.request)
        except KeyError as e:
            if 'data' in str(e):
                is_error = True
        self.assertTrue(is_error)

    def test_assign_permission_to_group(self):
        group = Group.objects.create(name='Staff')
        self.assertFalse(self.user.has_perm('constance.change_config'))
        DynamicSettingsUtils.assign_permission_to_group()
        self.user = ProxyUser.objects.get(pk=self.user.pk)  # reload user & his permissions
        self.assertFalse(self.user.has_perm('constance.change_config'))  # user is not staff
        self.user.is_staff = True
        self.user.save()
        self.user.groups.add(group)
        self.user = ProxyUser.objects.get(pk=self.user.pk)  # reload user & his permissions
        self.assertTrue(self.user.has_perm('constance.change_config'))
        group.delete()

    @staticmethod
    def _reset_constance_settings_to_default():
        for sett_name, sett_value in CONSTANCE_CONFIG.items():
            setattr(config, sett_name, sett_value[0])

    def _execute_site_settings_api_schema(self, req_string, context):
        result = self.client.execute(request_string=req_string, context_value=context)
        return result['data']['siteSettings']
