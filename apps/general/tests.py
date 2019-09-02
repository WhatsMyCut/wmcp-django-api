import datetime
from unittest.mock import patch, call, ANY

import graphene
from celery import current_app
from django.conf import settings
from django.db import transaction
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings
from django_celery_beat.models import PeriodicTask
from graphene.test import Client
from graphene.utils.resolve_only_args import resolve_only_args
import pytz
from dateutil.parser import parse as parse_datetime
from model_mommy import mommy

from apps.appointments.event.models import Event
from apps.appointments.models import Appointment
from apps.general.exceptions import InvalidParamException, ErrorDto, InternalErrorException
from apps.general.graphql import format_error
from apps.general.services import BaseEmailer
from apps.resident.models import Resident
from apps.general.utils import DateUtils, nth_item


class GraphQLTests(SimpleTestCase):
    class TestQuery(graphene.ObjectType):
        test_validation_error_field = graphene.String()
        test_internal_error_field = graphene.String()
        test_system_error_field = graphene.String()

        @resolve_only_args
        def resolve_test_validation_error_field(self):
            raise InvalidParamException(
                detail='Validation failed.',
                errors=[
                    ErrorDto(key='name', message='Maximum length exceeded.'),
                    ErrorDto(key='age', message='Must be integer.'),
                    ErrorDto(key='zip_code', message='Zip code is required.')
                ]
            )

        @resolve_only_args
        def resolve_test_internal_error_field(self):
            raise InternalErrorException(detail='App internal error.')

        @resolve_only_args
        def resolve_test_system_error_field(self):
            raise Exception('System exception.')

    test_schema = graphene.Schema(query=TestQuery)

    def setUp(self):
        self.client = Client(self.test_schema, format_error=format_error)

    def test_returns_formatted_app_validation_error(self):
        query = '''
        query {
          testValidationErrorField
        }
        '''
        result = self.client.execute(request_string=query)
        error = result['errors'][0]
        self.assertEqual(error['message'], 'Validation failed.')
        self.assertEqual(error['code'], InvalidParamException.code)
        self.assertEqual(len(error['errors']), 3)
        self.assertEqual(len([x for x in error['errors'] if x['key'] == 'name']), 1)
        self.assertEqual(len([x for x in error['errors'] if x['message'] == 'Must be integer.']), 1)
        self.assertEqual(len([x for x in error['errors'] if x['key'] == 'zipCode']), 1)

    @patch('apps.general.loggers.django_logger')
    def test_logs_and_returns_formatted_app_internal_error(self, mock_django_logger):
        query = '''
        query {
          testInternalErrorField
        }
        '''
        result = self.client.execute(request_string=query)
        error = result['errors'][0]
        self.assertEqual(error['message'], 'App internal error.')
        self.assertEqual(error['code'], InternalErrorException.code)
        mock_django_logger.error.assert_has_calls(
            [call('App internal error.', exc_info=(ANY, ANY, ANY))]
        )

    @patch('apps.general.loggers.django_logger')
    def test_logs_and_obfuscates_system_error(self, mock_django_logger):
        query = '''
        query {
          testSystemErrorField
        }
        '''

        result = self.client.execute(request_string=query)
        error = result['errors'][0]
        self.assertEqual(error['message'], 'Internal error.')
        mock_django_logger.error.assert_has_calls(
            [call('Exception during GraphQL method execution.', exc_info=(ANY, ANY, ANY))]
        )


class BaseEmailerTests(SimpleTestCase):
    def test_split_email_and_name(self):
        email1 = 'john@smith.com'
        email2 = 'John Smith <john@smith.com>'
        email3 = 'John <john.smith+something@gmail.com>'
        self.assertEqual(BaseEmailer.split_email_and_name(email1), email1)
        self.assertEqual(
            BaseEmailer.split_email_and_name(email2),
            ('John Smith', 'john@smith.com'))
        self.assertEqual(
            BaseEmailer.split_email_and_name(email3),
            ('John', 'john.smith+something@gmail.com'))


class IterUtilsTests(SimpleTestCase):
    def test_returns_nth_element_of_iterator(self):
        items = [2, 4, 6, 8, 12]
        self.assertEqual(nth_item(iter(items), 1), 4)
        self.assertEqual(nth_item(iter(items), 3), 8)
        self.assertEqual(nth_item(iter(items), 5), None)


class GeneralTest(TestCase):

    def setUp(self):
        Resident.objects.all().delete()

    def test_created_modified(self):
        utc_now = DateUtils.utc_now()
        res = mommy.make(Resident)
        self.assertLess((res.created_at - utc_now).total_seconds(), 10)
        original_created_at = res.created_at
        original_modified_at = res.modified_at
        res.first_name = 'John'
        res.save()
        res.refresh_from_db()
        self.assertEqual(res.created_at, original_created_at)
        self.assertGreater(res.modified_at, original_modified_at)
        self.assertLess((res.modified_at - original_created_at).total_seconds(), 10)

    def test_to_sf_datetime(self):
        nf_tz = pytz.timezone('Canada/Newfoundland')
        # test converting 2 local datetimes (with DST and without DST) into UTC
        summer_dt = DateUtils.as_timezone(datetime.datetime(2000, 7, 1, 1, 1, 1), nf_tz)
        winter_dt = DateUtils.as_timezone(datetime.datetime(2000, 1, 1, 1, 1, 1), nf_tz)
        summer_dt_converted = DateUtils.to_sf_datetime(summer_dt, pytz.utc)
        winter_dt_converted = DateUtils.to_sf_datetime(winter_dt, pytz.utc)
        self.assertEqual(summer_dt_converted, '2000-07-01T03:31:01+00:00')
        self.assertEqual(winter_dt_converted, '2000-01-01T04:31:01+00:00')
        # test converting 2 UTC datetimes
        summer_utc = datetime.datetime(2000, 7, 1, 1, 1, 1, tzinfo=pytz.UTC)
        winter_utc = datetime.datetime(2000, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        summer_nf = DateUtils.to_sf_datetime(summer_utc, nf_tz)
        winter_nf = DateUtils.to_sf_datetime(winter_utc, nf_tz)
        self.assertEqual(parse_datetime(summer_nf).strftime('%Y-%m-%d %H:%M'), '2000-06-30 22:31')
        self.assertEqual(parse_datetime(winter_nf).strftime('%Y-%m-%d %H:%M'), '1999-12-31 21:31')
        self.assertEqual(parse_datetime(summer_nf).tzinfo._offset.total_seconds(), -9000)
        self.assertEqual(parse_datetime(winter_nf).tzinfo._offset.total_seconds(), -12600)


class GeneralTransactionalTests(TransactionTestCase):
    @patch('apps.general.decorators.in_tests', return_value=False)
    @patch('apps.salesforce.services.base.SalesForceFactory.init_salesforce')
    def test_run_on_commit_decorator(self, mock_in_tests, mock_init_salesforce):

        ap = mommy.make(Appointment, tips=None)
        with override_settings(SALESFORCE_ENABLED=True, SALESFORCE_TOKEN='dummy'):

            # Don't run the Celery task after save() as there's a rollbacked transaction
            with patch('apps.salesforce.signals.send_instance_updated') as mock_send_booking_updated:
                try:
                    with transaction.atomic():
                        ap.tips = 1
                        ap.save()
                        print(0 / 0)
                except Exception:
                    ap.refresh_from_db()
                    self.assertIsNone(ap.tips)
                    self.assertFalse(mock_send_booking_updated.run.called)
                else:
                    self.assertFalse("Shouldn't get here")

            # Call run the Celery task after save() as there are no rollbacked transactions
            with patch('apps.salesforce.signals.send_instance_updated') as mock_send_booking_updated:
                with transaction.atomic():
                    ap.tips = 1
                    ap.save()
                ap.refresh_from_db()
                self.assertEqual(ap.tips, 1)
                self.assertTrue(mock_send_booking_updated.run.called)

            # Call run the Celery task after save() as there are no transactions at all
            with patch('apps.salesforce.signals.send_instance_updated') as mock_send_booking_updated:
                ap.tips = 1
                ap.save()
                ap.refresh_from_db()
                self.assertEqual(ap.tips, 1)
                self.assertTrue(mock_send_booking_updated.run.called)

            # Don't call run the Celery task after save() as this transaction has nothing to do with Appointment
            with patch('apps.salesforce.signals.send_instance_updated') as mock_send_booking_updated:
                with transaction.atomic():
                    mommy.make(Event)
                self.assertFalse(mock_send_booking_updated.run.called)


class TestCeleryTasks(TestCase):
    def setUp(self):
        if not isinstance(settings.MIGRATION_MODULES, dict):
            raise self.skipTest('Skipping the migration-dependent tests')
        current_app.loader.import_default_modules()
        self.db_periodic_tasks = PeriodicTask.objects.all()
        self.discovered_tasks = [t for t in current_app.tasks.values() if str(t.name).startswith('apps')]
        self.non_periodic_tasks = settings.ONE_TIME_CELERY_TASKS

    def test_in_code_not_registered(self):
        unfilled_tasks = []
        registered_tasks = []
        registered_tasks.extend([t['task'] for t in self.db_periodic_tasks.values('task')])
        registered_tasks.extend(self.non_periodic_tasks)

        for task in self.discovered_tasks:
            if task.name not in registered_tasks:
                unfilled_tasks.append(task.name)
        if len(unfilled_tasks) != 0:
            raise AssertionError(
                'Unfilled tasks found: \n'
                + '\n'.join(unfilled_tasks)
                + '''\nMake sure you added the migration for new periodic tasks or added them to 
                settings.ONE_TIME_CELERY_TASKS'''
            )

    def test_registered_not_in_code(self):
        registered_tasks = []
        registered_tasks.extend([t['task'] for t in self.db_periodic_tasks.values('task')])
        registered_tasks.extend(self.non_periodic_tasks)

        undefined_tasks = set(registered_tasks) - set([t.name for t in self.discovered_tasks])

        if undefined_tasks:
            raise AssertionError(
                'Undefined tasks found: \n'
                + '\n'.join(undefined_tasks)
                + '''\nMake sure you did not forget to unregister task after removing it from code'''
            )


class DateUtilsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.fmt = '%Y-%m-%d %H:%M:%S %Z%z'
        cls.eastern = pytz.timezone('US/Eastern')

    @patch('apps.general.utils.datetime')
    def test_utc_now(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2002, 10, 27, 1, 30)

        in_utc = DateUtils.utc_now()
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')

    @patch('apps.general.utils.datetime')
    def test_tz_now(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2002, 10, 27, 6, 30)

        in_utc = DateUtils.tz_now(pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 06:30:00 UTC+0000')

        in_eastern = DateUtils.tz_now(self.eastern)
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')

    def test_as_utc(self):
        # convert from naive to UTC
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        in_utc = DateUtils.as_utc(naive)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')

        # convert from UTC to UTC (nothing changed)
        in_utc = datetime.datetime(2002, 10, 27, 1, 30, tzinfo=pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')
        in_utc = DateUtils.as_utc(in_utc)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')

        # hard-replace from localized to UTC (simply ignore original tz)
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        in_utc = DateUtils.as_utc(in_eastern)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')

    def test_to_utc(self):
        # convert from naive to UTC
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        with self.assertRaisesMessage(AssertionError, "Can't convert naive datetime. Use DateUtils.as_utc() for that"):
            DateUtils.to_utc(naive)

        # convert from UTC to UTC (nothing changed)
        in_utc = datetime.datetime(2002, 10, 27, 1, 30, tzinfo=pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')
        in_utc = DateUtils.to_utc(in_utc)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')

        # convert from local to UTC
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        in_utc = DateUtils.to_utc(in_eastern)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 06:30:00 UTC+0000')

    def test_as_timezone(self):
        # convert from naive to UTC
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        in_utc = DateUtils.as_timezone(naive, pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')

        # convert from naive to eastern
        in_eastern = DateUtils.as_timezone(naive, self.eastern)
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')

        # convert from eastern to eastern (nothing changed)
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        in_eastern = DateUtils.as_timezone(in_eastern, self.eastern)
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')

    def test_to_timezone(self):
        # convert from naive to eastern
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        with self.assertRaisesMessage(AssertionError, "Can't convert naive datetime. "
                                                      "Use DateUtils.as_timezone() for that"):
            DateUtils.to_timezone(naive, self.eastern)

        # convert from eastern to UTC
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        in_utc = DateUtils.to_timezone(in_eastern, pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 06:30:00 UTC+0000')

        # convert from UTC to eastern
        in_utc = datetime.datetime(2002, 10, 27, 6, 30, tzinfo=pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 06:30:00 UTC+0000')
        in_eastern = DateUtils.to_timezone(in_utc, self.eastern)
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')

        # convert from eastern to eastern (nothing changed)
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        in_eastern = DateUtils.to_timezone(in_eastern, self.eastern)
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')

    def test_date_to_datetime(self):
        date = datetime.date(2002, 10, 27)

        in_utc = DateUtils.date_to_datetime(date, pytz.UTC)
        self.assertEqual(in_utc.strftime(self.fmt), '2002-10-27 00:00:00 UTC+0000')

        in_eastern = DateUtils.date_to_datetime(date, self.eastern)
        self.assertEqual(in_eastern.strftime(self.fmt), '2002-10-27 00:00:00 EDT-0400')

    def test_as_date(self):
        # convert from naive to date
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        date = DateUtils.as_date(naive)
        self.assertEqual(date.strftime(self.fmt), '2002-10-27 00:00:00 ')

        # convert from UTC to date
        in_utc = datetime.datetime(2002, 10, 27, 6, 30, tzinfo=pytz.UTC)
        date = DateUtils.as_date(in_utc)
        self.assertEqual(date.strftime(self.fmt), '2002-10-27 00:00:00 ')

        # convert from eastern to date
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        date = DateUtils.as_date(in_eastern)
        self.assertEqual(date.strftime(self.fmt), '2002-10-27 00:00:00 ')

        # convert from date to date
        date = datetime.date(2002, 10, 27)
        self.assertEqual(date.strftime(self.fmt), '2002-10-27 00:00:00 ')
        date = DateUtils.as_date(date)
        self.assertEqual(date.strftime(self.fmt), '2002-10-27 00:00:00 ')

        # convert from empty to date
        self.assertIsNone(DateUtils.as_date(None))
        # noinspection PyTypeChecker
        self.assertIsNone(DateUtils.as_date(''))

    def test_date_at_time(self):
        date = datetime.date(2002, 10, 27)

        # time is naive
        naive = datetime.datetime(2002, 10, 27, 6, 30)
        date_at_time = DateUtils.date_at_time(date, naive)
        self.assertEqual(date_at_time.strftime(self.fmt), '2002-10-27 06:30:00 ')

        # time in UTC
        in_utc = datetime.datetime(2002, 10, 27, 6, 30, tzinfo=pytz.UTC)
        date_at_time = DateUtils.date_at_time(date, in_utc)
        self.assertEqual(date_at_time.strftime(self.fmt), '2002-10-27 06:30:00 UTC+0000')

        # time in eastern
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        date_at_time = DateUtils.date_at_time(date, in_eastern)
        self.assertEqual(date_at_time.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')

    def test_start_of_day(self):
        # from naive
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        start_of_day = DateUtils.start_of_day(naive)
        self.assertEqual(start_of_day.strftime(self.fmt), '2002-10-27 00:00:00 ')

        # from UTC
        in_utc = datetime.datetime(2002, 10, 27, 6, 30, tzinfo=pytz.UTC)
        start_of_day = DateUtils.start_of_day(in_utc)
        self.assertEqual(start_of_day.strftime(self.fmt), '2002-10-27 00:00:00 UTC+0000')

        # from eastern
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        start_of_day = DateUtils.start_of_day(in_eastern)
        self.assertEqual(start_of_day.strftime(self.fmt), '2002-10-27 00:00:00 EST-0500')

    def test_to_millis(self):
        expect_millis = 1035682200000.0

        # from naive
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        millis = DateUtils.to_millis(naive)
        self.assertEqual(millis, expect_millis)

        # from UTC
        in_utc = datetime.datetime(2002, 10, 27, 1, 30, tzinfo=pytz.UTC)
        millis = DateUtils.to_millis(in_utc)
        self.assertEqual(millis, expect_millis)

        # from eastern
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 26, 21, 30))
        millis = DateUtils.to_millis(in_eastern)
        self.assertEqual(millis, expect_millis)

    def test_is_dst(self):
        # from naive to UTC
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        is_dst = DateUtils.is_dst(naive, pytz.UTC)
        self.assertEqual(is_dst, False)

        # from naive to eastern-summer
        naive = datetime.datetime(2002, 10, 27, 5, 30)
        is_dst = DateUtils.is_dst(naive, self.eastern)
        self.assertEqual(is_dst, True)

        # from naive to eastern-winter
        naive = datetime.datetime(2002, 10, 27, 6, 30)
        is_dst = DateUtils.is_dst(naive, self.eastern)
        self.assertEqual(is_dst, False)

        # from UTC to eastern-summer
        in_utc = datetime.datetime(2002, 10, 27, 5, 30, tzinfo=pytz.UTC)
        is_dst = DateUtils.is_dst(in_utc, self.eastern)
        self.assertEqual(is_dst, True)

        # from UTC to eastern-winter
        in_utc = datetime.datetime(2002, 10, 27, 6, 30, tzinfo=pytz.UTC)
        is_dst = DateUtils.is_dst(in_utc, self.eastern)
        self.assertEqual(is_dst, False)

        # from eastern-summer to eastern-summer
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 0, 30))
        is_dst = DateUtils.is_dst(in_eastern, self.eastern)
        self.assertEqual(is_dst, True)

        # from eastern-winter to eastern-winter
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        is_dst = DateUtils.is_dst(in_eastern, self.eastern)
        self.assertEqual(is_dst, False)

    def test_is_last_day_of_month(self):
        func = DateUtils.is_last_day_of_month
        self.assertEqual(func(datetime.datetime(2002, 1, 1)), False)
        self.assertEqual(func(datetime.datetime(2002, 1, 31)), True)
        self.assertEqual(func(datetime.datetime(2002, 2, 27)), False)
        self.assertEqual(func(datetime.datetime(2002, 2, 28)), True)
        self.assertEqual(func(datetime.datetime(2002, 10, 30)), False)
        self.assertEqual(func(datetime.datetime(2002, 10, 31)), True)
        self.assertEqual(func(datetime.datetime(2002, 11, 1)), False)
        self.assertEqual(func(datetime.datetime(2002, 12, 30)), False)
        self.assertEqual(func(datetime.datetime(2002, 12, 31)), True)

    def test_shift_datetime_to_last_day_of_month(self):
        func = DateUtils.shift_datetime_to_last_day_of_month
        self.assertEqual(func(datetime.datetime(2002, 1, 1)), datetime.datetime(2002, 1, 31))
        self.assertEqual(func(datetime.datetime(2002, 2, 27)), datetime.datetime(2002, 2, 28))
        self.assertEqual(func(datetime.datetime(2002, 2, 28)), datetime.datetime(2002, 2, 28))
        self.assertEqual(func(datetime.datetime(2002, 10, 30)), datetime.datetime(2002, 10, 31))
        self.assertEqual(func(datetime.datetime(2002, 10, 31)), datetime.datetime(2002, 10, 31))
        self.assertEqual(func(datetime.datetime(2002, 11, 1)), datetime.datetime(2002, 11, 30))
        self.assertEqual(func(datetime.datetime(2002, 12, 30)), datetime.datetime(2002, 12, 31))
        self.assertEqual(func(datetime.datetime(2002, 12, 31)), datetime.datetime(2002, 12, 31))

    def test_is_zoned(self):
        self.assertEqual(DateUtils.is_zoned(datetime.datetime(2002, 10, 27)), False)
        self.assertEqual(DateUtils.is_zoned(datetime.datetime(2002, 10, 27, tzinfo=pytz.UTC)), True)
        self.assertEqual(DateUtils.is_zoned(datetime.datetime(2002, 10, 27, tzinfo=pytz.timezone('GMT'))), True)
        self.assertEqual(DateUtils.is_zoned(pytz.timezone('GMT').localize(datetime.datetime(2002, 10, 27))), True)
        self.assertEqual(DateUtils.is_zoned(self.eastern.localize(datetime.datetime(2002, 10, 27))), True)

    def test_to_naive(self):
        # from naive
        naive = datetime.datetime(2002, 10, 27, 1, 30)
        start_of_day = DateUtils.to_naive(naive)
        self.assertEqual(start_of_day.strftime(self.fmt), '2002-10-27 01:30:00 ')

        # from UTC
        in_utc = datetime.datetime(2002, 10, 27, 1, 30, tzinfo=pytz.UTC)
        start_of_day = DateUtils.to_naive(in_utc)
        self.assertEqual(start_of_day.strftime(self.fmt), '2002-10-27 01:30:00 ')

        # from eastern
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30))
        start_of_day = DateUtils.to_naive(in_eastern)
        self.assertEqual(start_of_day.strftime(self.fmt), '2002-10-27 01:30:00 ')

    # noinspection PyTypeChecker
    def test_to_sf_datetime(self):
        self.assertEqual(DateUtils.to_sf_datetime(dt=None, tz=None), None)

        # from naive + from UTC
        for src_dt in (datetime.datetime(2002, 10, 27, 1, 30, 0, 999),
                       datetime.datetime(2002, 10, 27, 1, 30, 0, 999, tzinfo=pytz.UTC)):

            sf_dt = DateUtils.to_sf_datetime(dt=src_dt, tz=None, convert_to_isoformat=False)
            self.assertEqual(sf_dt.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')
            sf_dt = DateUtils.to_sf_datetime(dt=src_dt, tz=None, convert_to_isoformat=True)
            self.assertEqual(sf_dt, '2002-10-27T01:30:00+00:00')

            sf_dt = DateUtils.to_sf_datetime(dt=src_dt, tz=pytz.UTC, convert_to_isoformat=False)
            self.assertEqual(sf_dt.strftime(self.fmt), '2002-10-27 01:30:00 UTC+0000')
            sf_dt = DateUtils.to_sf_datetime(dt=src_dt, tz=pytz.UTC, convert_to_isoformat=True)
            self.assertEqual(sf_dt, '2002-10-27T01:30:00+00:00')

            sf_dt = DateUtils.to_sf_datetime(dt=src_dt, tz=self.eastern, convert_to_isoformat=False)
            self.assertEqual(sf_dt.strftime(self.fmt), '2002-10-26 21:30:00 EDT-0400')
            sf_dt = DateUtils.to_sf_datetime(dt=src_dt, tz=self.eastern, convert_to_isoformat=True)
            self.assertEqual(sf_dt, '2002-10-26T21:30:00-04:00')

        # from eastern
        in_eastern = self.eastern.localize(datetime.datetime(2002, 10, 27, 1, 30, 0, 999))
        sf_dt = DateUtils.to_sf_datetime(dt=in_eastern, tz=None, convert_to_isoformat=False)
        self.assertEqual(sf_dt.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        sf_dt = DateUtils.to_sf_datetime(dt=in_eastern, tz=None, convert_to_isoformat=True)
        self.assertEqual(sf_dt, '2002-10-27T01:30:00-05:00')

        sf_dt = DateUtils.to_sf_datetime(dt=in_eastern, tz=pytz.UTC, convert_to_isoformat=False)
        self.assertEqual(sf_dt.strftime(self.fmt), '2002-10-27 06:30:00 UTC+0000')
        sf_dt = DateUtils.to_sf_datetime(dt=in_eastern, tz=pytz.UTC, convert_to_isoformat=True)
        self.assertEqual(sf_dt, '2002-10-27T06:30:00+00:00')

        sf_dt = DateUtils.to_sf_datetime(dt=in_eastern, tz=self.eastern, convert_to_isoformat=False)
        self.assertEqual(sf_dt.strftime(self.fmt), '2002-10-27 01:30:00 EST-0500')
        sf_dt = DateUtils.to_sf_datetime(dt=in_eastern, tz=self.eastern, convert_to_isoformat=True)
        self.assertEqual(sf_dt, '2002-10-27T01:30:00-05:00')

    def test_get_rrules_byweekday_from_date(self):
        func = DateUtils.get_rrules_byweekday_from_date
        self.assertEqual(func(datetime.date(2002, 1, 1)), '1TU')
        self.assertEqual(func(datetime.date(2002, 1, 7)), '1MO')
        self.assertEqual(func(datetime.date(2002, 1, 8)), '2TU')
        self.assertEqual(func(datetime.date(2002, 1, 14)), '2MO')
        self.assertEqual(func(datetime.date(2002, 1, 21)), '3MO')
        self.assertEqual(func(datetime.date(2002, 1, 28)), '-1MO')
        self.assertEqual(func(datetime.date(2002, 2, 25)), '-1MO')
        self.assertEqual(func(datetime.date(2002, 2, 26)), '-1TU')
        self.assertEqual(func(datetime.date(2002, 2, 27)), '-1WE')
        self.assertEqual(func(datetime.date(2002, 2, 28)), '-1TH')
        self.assertEqual(func(datetime.date(2002, 3, 29)), '-1FR')
        self.assertEqual(func(datetime.date(2002, 3, 30)), '-1SA')
        self.assertEqual(func(datetime.date(2002, 3, 31)), '-1SU')

    @patch.object(DateUtils, 'utc_now', return_value=datetime.datetime(2019, 5, 9, 6, 30))
    def test_weekdays_until(self, _):
        self.assertEqual(DateUtils.weekdays_until(datetime.date(2019, 5, 13)), 2)
        self.assertEqual(DateUtils.weekdays_until(datetime.datetime(2019, 5, 10)), 1)
