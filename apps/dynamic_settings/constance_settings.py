import datetime
from collections import OrderedDict

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

# That's the main settings dict for the project.
# You don't really have to change anything else in this file.
CONSTANCE_CONFIG = OrderedDict([
    ('HOURS_PAY_BEFORE_APPOINTMENT', (24, 'How many hours before NOW will the appointment be paid?', int)),
    ('FIRST_CHARGING_ATTEMPT_HOURS', (72, 'Hours passed after purchase creating when we make a first charge attempt', int)),
    ('SECOND_CHARGING_ATTEMPT_HOURS', (120, 'Hours passed after purchase creating when we make a second charge attempt', int)),
    ('CONCIERGE_EMAIL', ('concierge@whatsmycut.com', 'Default whatsmycut concierge email', str)),
    ('CONCIERGE_PHONE', ('415-733-0284', 'Default whatsmycut concierge phone', str)),
    ('PM_INTEGRATION_RESIDENT_MODIFICATION_THRESHOLD', (
        0.05, 'Relative threshold for changing of deleted/new residents number', float)),
    ('CELERY_TASK_RESULT_EXPIRES', (604800, 'Expire after [seconds]', int)),  # 604800 secs = 7 days
    ('PROPERTIES_2_WAY_SYNC', (False, 'Enable Property post_save sync from Django to SF?', bool)),
    ('YARDI_API_LICENSE_KEY', ('license key', 'Using to connect YARDI while pm_integration', str)),
    ('ADD_EVENT_TYPEFORM_URL', ('https://whatsmycut.typeform.com/to/gKLDRp',
                                'A TypeForm URL to request for a new event (Event)', str)),
    ('NO_PRICES_NOTIFICATION_RECIPIENTS', ('', 'A comma-separated list of emails', str)),
    ('REDIRECTION_AFTER_AUTHORISE_CONNECT_ACCOUNT', ('https://dashboard.stripe.com',
                                                     'Redirection URL after authorize connect account', str)),
    ('DAYS_AVAILABLE_BOOKING', (3, 'How many days from NOW will the appointment be available to book', int)),
    ('DAYS_BETWEEN_ACTIVATION_EMAILS',
     ('4,4,4',
      'How many days between activation series emails the delay is. A comma-separated list of three integers where '
      'the first one is the amount of days between the 1st email and the 2nd; next one is between the 2nd and the 3rd; '
      'etc..', str)),
    ('ENABLE_ACTIVATION_EMAILS', (False, 'When checked, send resident activation series emails', bool)),
    ('DAYS_UPCOMING_CLEANING_SUBSCRIPTION_NOTIFICATION', (
        2, 'How many days before coming subscription will a notification be sent', int)),
    ('DAYS_UPCOMING_DOG_WALKING_SUBSCRIPTION_NOTIFICATION', (
        2, 'How many days before coming subscription will a notification be sent', int)),
    ('ZAPIER_NEW_SUBSCRIBER_URL', (
        '', 'Zapier url to catch request with new subscriber', str)),
    ('ZAPIER_NEW_REVIEW_URL', (
        '', 'Zapier url to catch request with new review info', str)),
    ('UPCOMING_CLEANING_RESIDENT_TEMPLATE', (
        'upcoming_cleaning_resident', 'Mandrill template for upcoming_cleaning_subscription_notification', str)),
    ('UPCOMING_DOG_WALKING_RESIDENT_TEMPLATE', (
        'upcoming_dog_walking_resident', 'Mandrill template for upcoming_dog_walking_subscription_notification', str)),
    ('UPCOMING_CLEANING_PROPERTY_MANAGER_TEMPLATE', (
        'upcoming_cleaning_property_manager', 'Mandrill template for upcoming_cleaning_subscription_notification', str)),
    ('UPCOMING_DOG_WALKING_PROPERTY_MANAGER_TEMPLATE',
     ('upcoming_dog_walking_property_manager', 'Mandrill template for upcoming_dog_walking_subscription_notification',
      str)),
    ('UPCOMING_CLEANING_SERVICE_PROVIDER_TEMPLATE',
     ('upcoming_cleaning_service_provider', 'Mandrill template for upcoming_cleaning_subscription_notification', str)),
    ('UPCOMING_DOG_WALKING_SERVICE_PROVIDER_TEMPLATE',
     ('upcoming_dog_walking_service_provider', 'Mandrill template for upcoming_cleaning_subscription_notification', str)),
    ('NEW_SUBSCRIBERS_TEMPLATE', (
        'new_subscribers', 'Mandrill template for new subscribers notification', str)),
    ('CLEANING_SUBSCRIPTION_NOTIFICATION_TEMPLATE', (
        'cleaning_subscription_notification', 'Mandrill template for new cleaning subscription to admin', str)),
    ('DOG_WALKING_SUBSCRIPTION_NOTIFICATION_TEMPLATE', (
        'dog_walking_subscription_notification', 'Mandrill template for new dog walking subscription to admin', str)),
    ('PROVIDER_NEW_MEET_AND_GREET_TEMPLATE', (
        'provider_new_meet_and_greet', 'Mandrill template for new meet and greets to providers', str)),
    ('RESIDENT_NEW_MEET_AND_GREET_TEMPLATE', (
        'resident_new_meet_and_greet', 'Mandrill template for new meet and greets to resident', str)),
    ('USER_REPORT_ISSUE_TEMPLATE', ('user_reported_issue', 'Mandrill template for user report issue', str)),
    ('PASSWORD_RESET_TEMPLATE', ('password_reset', 'Mandrill template for password reset', str)),
    ('NO_PRICES_NOTIFICATION_TEMPLATE', ('no_prices_notification', 'Mandrill template for no prices notification', str)),
    ('RESIDENT_ONBOARDING_TEMPLATE', ('Plaint Text Email 1', 'Mandrill template for resident onboarding email', str)),
    ('SUB_PAR_REVIEW_TEMPLATE', ('sub_par_review', 'Mandrill template for subscription review', str)),
    ('MANDRILL_ERROR_NOTIFICATION_TEMPLATE', (
        'error-notification', 'mandrill template name for an error notification', str)),
    ('STORE_INTEGRATION_DATA', (True, 'Enable to store the integration data?', bool)),
    ('ZAPIER_CANCELLED_SUBSCRIPTION_URL', (
        '', 'Zapier url to catch request with cancelled subscriptions info', str)),
    ('ZAPIER_MOVED_IN_RESIDENT_URL', (
        '', 'Zapier url to catch request with moved in resident info', str)),
    ('SUBSCRIBERS_DIGEST_TEMPLATE', (
        'subscribers_digest', 'Mandrill template for subscribers digest', str)),
    ('RESIDENT_SKIPPING_SERVICE_TEMPLATE', (
        'resident_skipping_service', 'Mandrill template for Resident Skipping Service', str)),
    ('RESIDENT_SKIPPING_SERVICE_CC', (
        '', 'Extra emails to send a copy to', str)),
    ('HOURS_PERIOD_SUBSCRIPTION_DIGEST', (168, 'Time period in hours for subscription digest', int)),
    ('LOCAL_SERVICE_REMINDER_TIME', (
        datetime.time(15, 30), 'User local time to get an SMS service reminder. '
                               'If the minutes change, you need to change the task execution time.')),
    ('LOCAL_SERVICE_REVIEW_TIME', ( datetime.time(19, 00),'User local time 7pm to get a push notification to review a booking.')),
    ('SMS_CLEANING_REMINDER_TEXT', (
       'Hi {resident} - This is Maddie with whatsmycut. Yay! Tomorrow is a cleaning day. '
       'Please make sure you’re prepared for {provider}.\nThe cleaners need access to countertops and floors. '
       'Please put away personal belongings.\nClose all doors to rooms you do not wish to be cleaned.'
       '\nPlease ensure pets are safely secured. If left out, we may have to leave your unit before the clean '
       'is completed. \nPlease place trash and recycling in containers. Cleaners will not dispose of anything '
       'not already in the trash.\nPlease put dishes in the dishwasher so the sink is accessible.'
       '\nClick here to see what’s not included: https://bit.ly/2IYzW50', '', str)),
    ('SMS_DOG_WALKING_REMINDER_TEXT', (
       'Hi {resident} - This is Maddie with whatsmycut. Yay! Tomorrow is {dog_name}’s walk. '
       'Please make sure you’re prepared for {provider}.', '', str)),
    ('PUSH_APPOINTMENT_REMINDER_TEXT', (
       'Hi {resident} - This is a reminder of your upcoming {provider} {type} booking tomorrow', '', str)),
    ('PUSH_APPOINTMENT_RATING_TEXT', (
       'Hi {resident} - Tell us how {provider} treated your apartment!', '', str)),
    ('SMS_SERVICE_REMINDER_PHONE_NUMBER', ('+16507508081', 'Outbound Twilio phone number with SMS capabilities', str)),
    ('LOCAL_CLEANING_POST_EVENT_FEEDBACK_TIME', (
        datetime.time(19, 00), 'User local time to get an SMS cleaning feedback invitation. '
                               'If the minutes change, you need to change the task execution time.')),
    ('SMS_CLEANING_POST_EVENT_FEEDBACK_TEXT', (
       'We see you had a cleaning today. Let us know how {provider} did. https://bit.ly/2KGUDWl', '', str)),
    ('SMS_DOG_WALKING_POST_EVENT_FEEDBACK_TEXT', (
       'We see you had a dog walk today. Let us know how {provider} did. Please rate them 0 - 10. :)', '', str)),
    ('SMS_CLEANING_POST_EVENT_FEEDBACK_PHONE_NUMBER',
     ('+16503341449', 'Outbound Twilio phone number with SMS capabilities', str)),
    ('SKIPPING_EVENT_PHONE_NUMBER', ('+16502723798', 'Outbound Twilio phone number with SMS capabilities conntected '
                                                     'to the Skipping Event flow', str)),
    ('SKIPPING_EVENT_FLOW_ID',
     ('FWd34b2948131d94bab85d408424fca3af', '"Skipping Event" Twilio flow id', str)),
    ('STRIPE_DOG_WALKING_SUBSCRIPTION_PRODUCT_CODE',
     ('', 'Stripe product code to set for all DW subscriptions', str)),
    ('STRIPE_30MIN_DOG_WALKING_PRODUCT_CODE',
     ('', 'Stripe product code to set for all 30 min single dog walks', str)),
    ('STRIPE_60MIN_DOG_WALKING_PRODUCT_CODE',
     ('', 'Stripe product code to set for all 60 min single dog walks', str)),
    ('STRIPE_INITIAL_CUSTOMER_BALANCE',
     (0, 'Automatically add $ to every new Stripe customer (unless his email is specified in '
         'STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL) used to pay for whatsmycut services', int)),
    ('STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL',
     ('', 'A list of comma separated {email}={amount$} pairs.\nEXAMPLE: a@a.com=5$, b@b.com=15$\n'
          'This dollar amount will be added to Stripe upon next resident booking. The resident can be either '
          'a new customer or existing one', str)),
])

CONSTANCE_EXPOSED_SETTINGS = (  # settings that are publicly visible in the API call
    'FEATURE_CLEANING_ENABLED', 'FEATURE_RECURRENT_SCHEDULING_ENABLED', 'HOURS_PAY_BEFORE_APPOINTMENT',
    'PAYMENT_STRIPE_PUBLIC_KEY', 'SPA_PAYMENT_URL',
    'FEATURE_GYM_ENABLED', 'FEATURE_DOG_WALKING_ENABLED', 'FEATURE_MASSAGE_ENABLED',
    'FEATURE_TRANSPORTATION_ENABLED', 'CONCIERGE_EMAIL', 'CONCIERGE_PHONE',
    'ADD_EVENT_TYPEFORM_URL',
)

CONSTANCE_CONFIG_FIELDSETS = {
    'General Options': (
        'FEATURE_CLEANING_ENABLED', 'FEATURE_RECURRENT_SCHEDULING_ENABLED', 'HOURS_PAY_BEFORE_APPOINTMENT',
        'FEATURE_GYM_ENABLED', 'FEATURE_DOG_WALKING_ENABLED', 'FEATURE_MASSAGE_ENABLED',
        'FEATURE_TRANSPORTATION_ENABLED', 'SPA_PAYMENT_URL', 'FIRST_CHARGING_ATTEMPT_HOURS',
        'SECOND_CHARGING_ATTEMPT_HOURS', 'CONCIERGE_EMAIL', 'CONCIERGE_PHONE',
        'PM_INTEGRATION_RESIDENT_MODIFICATION_THRESHOLD', 'CELERY_TASK_RESULT_EXPIRES', 'PROPERTIES_2_WAY_SYNC',
        'YARDI_API_LICENSE_KEY', 'ADD_EVENT_TYPEFORM_URL',
        'NO_PRICES_NOTIFICATION_RECIPIENTS',
        'REDIRECTION_AFTER_AUTHORISE_CONNECT_ACCOUNT', 'DAYS_AVAILABLE_BOOKING', 'DAYS_BETWEEN_ACTIVATION_EMAILS',
        'DAYS_UPCOMING_CLEANING_SUBSCRIPTION_NOTIFICATION', 'DAYS_UPCOMING_DOG_WALKING_SUBSCRIPTION_NOTIFICATION',
        'STORE_INTEGRATION_DATA', 'HOURS_PERIOD_SUBSCRIPTION_DIGEST', 'PUSH_APPOINTMENT_REMINDER_TEXT',
    ),
    'Mandrill Options': (
        'PASSWORD_RESET_TEMPLATE', 'USER_REPORT_ISSUE_TEMPLATE', 'NO_PRICES_NOTIFICATION_TEMPLATE',
        'SUB_PAR_REVIEW_TEMPLATE', 'RESIDENT_ONBOARDING_TEMPLATE',
        'UPCOMING_CLEANING_RESIDENT_TEMPLATE', 'UPCOMING_DOG_WALKING_RESIDENT_TEMPLATE',
        'UPCOMING_CLEANING_PROPERTY_MANAGER_TEMPLATE', 'UPCOMING_DOG_WALKING_PROPERTY_MANAGER_TEMPLATE',
        'UPCOMING_CLEANING_SERVICE_PROVIDER_TEMPLATE', 'UPCOMING_DOG_WALKING_SERVICE_PROVIDER_TEMPLATE',
        'CLEANING_SUBSCRIPTION_NOTIFICATION_TEMPLATE',
        'NEW_SUBSCRIBERS_TEMPLATE', 'MANDRILL_ERROR_NOTIFICATION_TEMPLATE', 'SUBSCRIBERS_DIGEST_TEMPLATE',
        'RESIDENT_SKIPPING_SERVICE_TEMPLATE', 'RESIDENT_SKIPPING_SERVICE_CC',
        'DOG_WALKING_SUBSCRIPTION_NOTIFICATION_TEMPLATE', 'ENABLE_ACTIVATION_EMAILS',
        'PROVIDER_NEW_MEET_AND_GREET_TEMPLATE', 'RESIDENT_NEW_MEET_AND_GREET_TEMPLATE',
    ),
    'Zapier Options': (
        'ZAPIER_NEW_SUBSCRIBER_URL', 'ZAPIER_NEW_REVIEW_URL', 'ZAPIER_CANCELLED_SUBSCRIPTION_URL',
        'ZAPIER_MOVED_IN_RESIDENT_URL',
    ),
    'Twilio Options': (
        'LOCAL_SERVICE_REMINDER_TIME', 'SMS_CLEANING_REMINDER_TEXT', 'SMS_DOG_WALKING_REMINDER_TEXT',
        'SMS_SERVICE_REMINDER_PHONE_NUMBER',
        'LOCAL_CLEANING_POST_EVENT_FEEDBACK_TIME', 'SMS_CLEANING_POST_EVENT_FEEDBACK_TEXT',
        'SMS_DOG_WALKING_POST_EVENT_FEEDBACK_TEXT',
        'SMS_CLEANING_POST_EVENT_FEEDBACK_PHONE_NUMBER', 'SKIPPING_EVENT_FLOW_ID', 'SKIPPING_EVENT_PHONE_NUMBER',
    ),
    'Stripe Options': (
        'STRIPE_60MIN_DOG_WALKING_PRODUCT_CODE', 'STRIPE_30MIN_DOG_WALKING_PRODUCT_CODE',
        'STRIPE_DOG_WALKING_SUBSCRIPTION_PRODUCT_CODE', 'REDIRECTION_AFTER_AUTHORISE_CONNECT_ACCOUNT',
        'STRIPE_INITIAL_CUSTOMER_BALANCE', 'STRIPE_EXTRA_CUSTOMER_BALANCE_PER_EMAIL',
    ),
}
