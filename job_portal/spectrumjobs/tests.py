from django.test import TestCase, Client
from .factories import *
from .forms import *
from .views import get_matches, setup_otp
from .utils import *
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.urls import reverse
import time
from datetime import datetime, timedelta
from django.utils import timezone
from unittest.mock import patch
import json
from decimal import Decimal
from io import BytesIO
import base64
from PIL import Image 


#=============================================================================== #
#                                DATABASE MODELS TESTS                           #
# =============================================================================== #
# ====================================== #
#             USER MODEL TESTS           #
# ====================================== #
class UserModelTestCase(TestCase):  
    def setUp(self):
        self.user = UserFactory()
        
    def tearDown(self):
        User.objects.all().delete() 

    # New user registration
    def test_user_registration(self):
        self.assertTrue(self.user.pk) # Pk check
        self.assertTrue(self.user.username) # Username check
        self.assertTrue(self.user.check_password('InsecurePassword')) # Password check

    # Check username string representation
    def test_user_str(self):
        self.assertEqual(str(self.user), self.user.username) 

    # Authentication test
    def test_user_authentication(self):
        user = authenticate(username=self.user.username, password='InsecurePassword') # Authenticate user
        self.assertIsNotNone(user)  # Check authentication
        self.assertEqual(user.username, self.user.username)  # Verify username after authentication
        

# ====================================== #
#           CREATE NEW PROFILE           #
# ====================================== #
class UserProfileCreationTest(TestCase):
    def setUp(self):
        self.profile = UserProfileFactory()

    def tearDown(self):
        UserProfile.objects.all().delete()
        User.objects.all().delete() 

    # Check field types
    def test_fields_type(self):
        self.assertTrue(type(self.profile.user_type) is str)
        self.assertTrue(type(self.profile.first_name) is str)
        self.assertTrue(type(self.profile.last_name) is str)
        self.assertTrue(type(self.profile.address) is str)
        self.assertTrue(type(self.profile.city) is str)
        self.assertTrue(type(self.profile.postcode) is str)
        self.assertTrue(type(self.profile.phone) is str)
        self.assertTrue(type(self.profile.email) is str)
        self.assertTrue(type(self.profile.totp_secret_key) is str)
        self.assertTrue(type(self.profile.is_2fa_enabled) is bool)

    # Check user profile values 
    def test_values(self):
        self.assertEqual(self.profile.first_name, self.profile.first_name)
        self.assertEqual(self.profile.last_name, self.profile.last_name)
        self.assertEqual(self.profile.address, self.profile.address)
        self.assertEqual(self.profile.city, self.profile.city)
        self.assertEqual(self.profile.postcode, self.profile.postcode)
        self.assertEqual(self.profile.phone, self.profile.phone)
        self.assertEqual(self.profile.email, self.profile.email)
        self.assertEqual(self.profile.user_type, self.profile.user_type)

    # Test relationship
    def test_relationships(self):
        self.assertIsInstance(self.profile.user, User)


#====================================== #
#     SENSORY PROFILE MODEL TESTS       #
#====================================== #
class SensoryProfileCreationTest(TestCase):
    def setUp(self):
        self.sense_profile = SensoryProfileFactory()

    def tearDown(self):
        SensoryProfile.objects.all().delete()
        User.objects.all().delete()  

    # Check field types
    def test_fields_type(self):
        self.assertTrue(type(self.sense_profile.auditory) is float)
        self.assertTrue(type(self.sense_profile.visual) is float)
        self.assertTrue(type(self.sense_profile.smell) is float)
        self.assertTrue(type(self.sense_profile.tactile) is float)
        self.assertTrue(type(self.sense_profile.movement) is float)

    # Check each field to ensure it is within the range restriction
    def test_value_range(self):
        fields = ['auditory', 'visual', 'smell', 'tactile', 'movement'] # List of the fields
        for field in fields:
            value = getattr(self.sense_profile, field)
            self.assertTrue(0 <= value <= 5)

    # Test relationship        
    def test_relationships(self):
        self.assertIsInstance(self.sense_profile.user, User)


# ====================================== #
#     CITIZEN PROFILE MODEL TESTS       #
# ====================================== #
class CitizenProfileTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.profile = CitizenProfileFactory(user=self.user)

    def tearDown(self):
        CitizenProfile.objects.all().delete()
        User.objects.all().delete()

    # Check field types
    def test_fields_type(self):
        self.assertTrue(type(self.profile.age) is int)
        self.assertTrue(type(self.profile.experience) is int)
        self.assertTrue(type(self.profile.job_field) is str)
        self.assertTrue(type(self.profile.job_type) is str)
        self.assertTrue(type(self.profile.support_grants) is str)
        self.assertTrue(type(self.profile.employed) is bool)
        self.assertTrue(type(self.profile.employment_date) is datetime)
        self.assertTrue(type(self.profile.employer_feedback) is float)
        self.assertTrue(type(self.profile.citizen_feedback) is float)

    # Check citizen profile values 
    def test_values(self):
        self.assertEqual(self.profile.age, self.profile.age)
        self.assertEqual(self.profile.experience, self.profile.experience)
        self.assertEqual(self.profile.job_field, self.profile.job_field)
        self.assertEqual(self.profile.job_type, self.profile.job_type)
        self.assertEqual(self.profile.support_grants, self.profile.support_grants)
        self.assertEqual(self.profile.education, self.profile.education)
        self.assertTrue(self.profile.employed)
        self.assertIsNotNone(self.profile.employer_feedback)
        self.assertIsNotNone(self.profile.citizen_feedback)

    # Check choice fields 
    def test_choices(self):
        self.assertIn(self.profile.job_field, dict(CitizenProfile.JOB_FIELDS).keys())
        self.assertIn(self.profile.job_type, dict(CitizenProfile.JOB_TYPES).keys())
        self.assertIn(self.profile.support_grants, dict(CitizenProfile.SUPPORT_NEEDS).keys())
        self.assertIn(self.profile.education, dict(CitizenProfile.EDUCATION).keys())

    # Check number fields is within the range restriction (0-5)
    def test_fields_range(self):
        self.assertTrue(0 <= self.profile.age <= 99) # Age must be 0-99 years
        self.assertTrue(0 <= self.profile.experience <= 40)  # Experience must be 0-40 years
        self.assertGreaterEqual(self.profile.employer_feedback, 0)
        self.assertLessEqual(self.profile.employer_feedback, 5)
        self.assertGreaterEqual(self.profile.citizen_feedback, 0)
        self.assertLessEqual(self.profile.citizen_feedback, 5)

    # Test relationships  
    def test_relationships(self):
        self.assertIsInstance(self.profile.user, User)
        self.assertIsInstance(self.profile.employer, User)
        self.assertIsInstance(self.profile.contact_person, User)


# ====================================== #
#     EMPLOYER FACILITY MODEL TESTS      #
#======================================= #
class EmployerFacilitiesTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.facilities = EmployerFacilitiesFactory(employer=self.user)

    def tearDown(self):
        EmployerFacilities.objects.all().delete()
        User.objects.all().delete()

    # Check field types
    def test_fields_type(self):
        self.assertTrue(type(self.facilities.sound_level) is float)
        self.assertTrue(type(self.facilities.team_count) is int)
        self.assertTrue(type(self.facilities.layout) is str)
        self.assertTrue(type(self.facilities.support_service) is bool)
        self.assertTrue(type(self.facilities.field) is str)
    
    # Check employer facility profile values 
    def test_fields_value(self):
        self.assertEqual(self.facilities.sound_level, self.facilities.sound_level)
        self.assertEqual(self.facilities.team_count, self.facilities.team_count)
        self.assertEqual(self.facilities.layout, self.facilities.layout)
        self.assertEqual(self.facilities.support_service, self.facilities.support_service)
        self.assertEqual(self.facilities.field, self.facilities.field)

    # Check field value range restrictions 
    def test_fields_range(self):
        self.assertTrue(0 <= self.facilities.sound_level <= 5)
        self.assertTrue(self.facilities.team_count >= 0)
        self.assertGreaterEqual(self.facilities.sound_level, 0)
        self.assertLessEqual(self.facilities.sound_level, 5)
        self.assertGreaterEqual(self.facilities.team_count, 0)

    # Check choice fields 
    def test_choices(self):
        self.assertIn(self.facilities.layout, dict(EmployerFacilities.LAYOUT).keys())
        self.assertIn(self.facilities.field, dict(EmployerFacilities.COMPANY_FIELDS).keys())

    # Test relationship 
    def test_relationships(self):
        self.assertIsInstance(self.facilities.employer, User)


# ====================================== #
#            JOB  MODEL TESTS            #
# ====================================== #
class JobTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.citizen1 = UserFactory()
        self.citizen2 = UserFactory()
        self.job = JobFactory(employer=self.user)

    def tearDown(self):
        Job.objects.all().delete()
        User.objects.all().delete()

    # Check field types
    def test_fields_type(self):
        self.assertTrue(type(self.job.company_name) is str)
        self.assertTrue(type(self.job.title) is str)
        self.assertTrue(type(self.job.location) is str)
        self.assertTrue(type(self.job.description) is str)
        self.assertTrue(type(self.job.job_field) is str)
        self.assertTrue(type(self.job.job_type) is str)
        self.assertTrue(type(self.job.education) is str)
        self.assertTrue(type(self.job.posted_date) is datetime)

    # Check job field values 
    def test_fields_value(self):
        self.assertEqual(self.job.company_name, self.job.company_name)
        self.assertEqual(self.job.title, self.job.title)
        self.assertEqual(self.job.location, self.job.location)
        self.assertEqual(self.job.description, self.job.description)
        self.assertEqual(self.job.job_field, self.job.job_field)
        self.assertEqual(self.job.job_type, self.job.job_type)
        self.assertEqual(self.job.education, self.job.education)
        self.assertIsInstance(self.job.posted_date, datetime)

    # Check choice fields 
    def test_choices(self):
        self.assertIn(self.job.job_field, dict(Job.JOB_FIELDS).keys())
        self.assertIn(self.job.job_type, dict(Job.JOB_TYPES).keys())
        self.assertIn(self.job.education, dict(Job.EDUCATION).keys())

    # Check applicant many-op-many field 
    def test_applicants(self):
        # Initial count
        self.assertEqual(self.job.applicants.count(), 0)
        # Check after adding applicants
        self.job.applicants.add(self.citizen1,self.citizen2)
        self.assertIn(self.citizen1, self.job.applicants.all())
        self.assertIn(self.citizen2, self.job.applicants.all())

    # Check job post date
    def test_posted_date(self):
        self.assertTrue((timezone.now()  - self.job.posted_date).total_seconds() < 60)

    # Test relationship 
    def test_relationships(self):
        self.assertIsInstance(self.job.employer, User)


# ======================================= #
#       JOB DESCRIPTION MODEL TESTS       #
#  ====================================== #
class JobDetailTestCase(TestCase):
    def setUp(self):
        self.job = JobFactory()
        self.job_description = JobDescriptionFactory(job=self.job)

    def tearDown(self):
        JobDescription.objects.all().delete()
        Job.objects.all().delete()
        User.objects.all().delete()

    # Check field types 
    def test_fields_type(self):
        self.assertTrue(type(self.job_description.responsibilities) is str)
        self.assertTrue(type(self.job_description.requirements) is str)

    # Check job description field values 
    def test_fields_value(self):
        self.assertEqual(self.job_description.responsibilities, self.job_description.responsibilities)
        self.assertEqual(self.job_description.requirements, self.job_description.requirements)

    # Check job description creation
    def test_job_description_creation(self):
        job_description = JobDescription.objects.create(
            job=self.job,
            responsibilities="Create and maintain backend server",
            requirements="5+ years experience in back-end development"
        )
        # Fetch from the database
        job_description.refresh_from_db()
        # Verify the fields
        self.assertEqual(job_description.responsibilities, "Create and maintain backend server")
        self.assertEqual(job_description.requirements, "5+ years experience in back-end development")
    
    # Test relationships 
    def test_relationship(self):
        self.assertEqual(self.job_description.job, self.job)
        self.assertIn(self.job_description, self.job.job_descriptions.all())


# ====================================== #
#           CALENDAR MODEL TESTS         #
# ====================================== #
class CalendarTestCase(TestCase):
    def setUp(self):
        self.liaison = UserFactory()
        self.user = UserFactory()
        self.calendar = CalendarFactory(liaison=self.liaison, user=self.user)

    def tearDown(self):
        Calendar.objects.all().delete()
        User.objects.all().delete()

    # Check field types 
    def test_fields_type(self):
        self.assertTrue(type(self.calendar.title) is str)
        self.assertTrue(type(self.calendar.description) is str)
        self.assertTrue(type(self.calendar.start_time) is datetime)
        self.assertTrue(type(self.calendar.end_time) is datetime)

    # Check calendar creation
    def test_fields_value(self):
        self.assertEqual(self.calendar.title, self.calendar.title)
        self.assertEqual(self.calendar.description, self.calendar.description)
        self.assertTrue(self.calendar.start_time <= self.calendar.end_time if self.calendar.end_time else True)

    # Check string method
    def test_str_method(self):
        self.assertEqual(str(self.calendar), self.calendar.title)

    # Ensure that the end time is always after the start time
    def test_time(self):
        now = timezone.now()
        calendar = CalendarFactory(start_time=now, end_time=now + timedelta(hours=1))
        self.assertTrue(calendar.start_time < calendar.end_time)

    # Test relationships 
    def test_relationships(self):
        self.assertIsInstance(self.calendar.user, User)
        self.assertIsInstance(self.calendar.liaison, User)


# ====================================== #
#           MESSAGE MODEL TESTS          #
# ====================================== #
class MessageTestCase(TestCase):
    def setUp(self):
        self.sender = UserFactory(username='sender')
        self.recipient = UserFactory(username='recipient')
        self.message = MessageFactory(sender=self.sender, recipient=self.recipient)

    def tearDown(self):
        Message.objects.all().delete()
        User.objects.all().delete()

    # Check field types 
    def test_fields_type(self):
        self.assertTrue(type(self.message.subject) is str)
        self.assertTrue(type(self.message.body) is str)
        self.assertTrue(type(self.message.timestamp) is datetime)
        self.assertTrue(type(self.message.read) is bool)
    
    # Check message values
    def test_fields_value(self):
        self.assertEqual(self.message.sender, self.sender)
        self.assertEqual(self.message.recipient, self.recipient)
        self.assertTrue(self.message.subject)
        self.assertTrue(self.message.body)
        self.assertIsInstance(self.message.timestamp, timezone.datetime)
        self.assertFalse(self.message.read)
        self.assertIsInstance(self.message.read, bool)

    # Verify creation timestamp
    def test_timestamp_auto_now_add(self):
        message = MessageFactory(sender=self.sender, recipient=self.recipient) # Create new message
        self.assertTrue((message.timestamp - timezone.now()).total_seconds() < 60)  # < 60 second difference

    # Check 'read' flag is false by default
    def test_read_field_default(self):
        self.assertFalse( self.message.read)

    # Test relationships 
    def test_message_relationships(self):
        self.assertEqual(self.message.sender, self.sender)
        self.assertEqual(self.message.recipient, self.recipient)
        self.assertIn(self.message, self.sender.sent_messages.all())
        self.assertIn(self.message, self.recipient.received_messages.all())


# ====================================== #
#        CONVERSATION MODEL TESTS        #
# ====================================== #
class ConversationTestCase(TestCase):
    def setUp(self):
        self.conversation = ConversationFactory() 

    def tearDown(self):
        Conversation.objects.all().delete()  

    # Check field types 
    def test_fields_type(self):
        self.assertTrue(type(self.conversation.contact) is str)
        self.assertTrue(type(self.conversation.sender) is str)
        self.assertTrue(type(self.conversation.message) is str)
        self.assertTrue(type(self.conversation.timestamp) is datetime)
        
     # Check conversation values
    def test_field_values(self):
        self.assertTrue(self.conversation.contact)
        self.assertTrue(self.conversation.sender)
        self.assertTrue(self.conversation.message)
        self.assertIsInstance(self.conversation.timestamp, timezone.datetime)

    # Check conversation creation  
    def test_creation(self):
        self.assertTrue(isinstance(self.conversation, Conversation))
        self.assertTrue(self.conversation.message)

    # Verify message timestamp
    def test_timestamp_auto_now_add(self):
        conversation = ConversationFactory()  # Create new conversation message
        self.assertTrue((conversation.timestamp - timezone.now()).total_seconds() < 60)  # < 60 second difference


# ====================================== #
#       CITIZEN FEEDBACK MODEL TEST      #
# ====================================== #
class CitizenFeedbackTestCase(TestCase):
    def setUp(self):
        self.citizen = UserFactory()
        self.citizen_feedback = CitizenFeedbackFactory(citizen= self.citizen)

    def tearDown(self):
        CitizenFeedback.objects.all().delete()
        User.objects.all().delete()

    # Check field types 
    def test_fields_type(self):
        self.assertTrue(type(self.citizen_feedback.feedback) is str)
        self.assertTrue(type(self.citizen_feedback.job_satisfaction) is int)
        self.assertTrue(type(self.citizen_feedback.work_hours) is int)
        self.assertTrue(type(self.citizen_feedback.tasks) is int)
        self.assertTrue(type(self.citizen_feedback.social_level) is int)
        self.assertTrue(type(self.citizen_feedback.stress_level) is int)
        self.assertTrue(type(self.citizen_feedback.support_level) is int)
        self.assertTrue(type(self.citizen_feedback.overall_rating) is float)
        self.assertTrue(type(self.citizen_feedback.feedback_date) is datetime)

    # Check feedback creation  
    def test_creation(self):
        feedback = CitizenFeedback.objects.get(id=self.citizen_feedback.id)
        self.assertEqual(feedback.citizen, self.citizen_feedback.citizen)
        self.assertEqual(feedback.feedback, self.citizen_feedback.feedback)
        self.assertTrue(1 <= feedback.job_satisfaction <= 5)
        self.assertTrue(1 <= feedback.work_hours <= 5)
        self.assertTrue(1 <= feedback.tasks <= 5)
        self.assertTrue(1 <= feedback.social_level <= 5)
        self.assertTrue(1 <= feedback.stress_level <= 5)
        self.assertTrue(1 <= feedback.support_level <= 5)

    # Check overall rating calculation  
    def test_feedback_calculation(self):
        feedback = CitizenFeedback.objects.get(id=self.citizen_feedback.id)
        # Calculate expected overall rating
        total_score = (feedback.job_satisfaction + feedback.work_hours + feedback.tasks +
                       feedback.social_level + feedback.stress_level + feedback.support_level)
        expected_rating = (total_score / 30) * 100
        self.assertAlmostEqual(float(feedback.overall_rating), expected_rating, places=2)

    # Check overall rating calculation 
    def test_date(self):
        self.assertTrue((timezone.now() - self.citizen_feedback.feedback_date).total_seconds() < 60)  # < Allow for 60 second difference

    # Test relationship
    def test_relationships(self):
        self.assertIsInstance(self.citizen_feedback.citizen, User)


# ====================================== #
#       EMPLOYER FEEDBACK MODEL TEST     #
# ====================================== #
class CitizenFeedbackTestCase(TestCase):
    def setUp(self):
        self.employer = UserFactory()
        self.citizen = UserFactory()
        self.employer_feedback = EmployerFeedbackFactory(employer =self.employer, citizen = self.citizen)

    def tearDown(self):
        EmployerFeedback.objects.all().delete()
        User.objects.all().delete()

    # Check field types 
    def test_fields_type(self):
        self.assertTrue(type(self.employer_feedback.feedback) is str)
        self.assertTrue(type(self.employer_feedback.punctuality) is int)
        self.assertTrue(type(self.employer_feedback.attendance) is int)
        self.assertTrue(type(self.employer_feedback.dependability) is int)
        self.assertTrue(type(self.employer_feedback.work_quality) is int)
        self.assertTrue(type(self.employer_feedback.communication) is int)
        self.assertTrue(type(self.employer_feedback.attitude) is int)
        self.assertTrue(type(self.employer_feedback.overall_rating) is float)
        self.assertTrue(type(self.employer_feedback.feedback_date) is datetime)

    # Check feedback creation  
    def test_creation(self):
        feedback = EmployerFeedback.objects.get(id=self.employer_feedback.id)
        self.assertEqual(feedback.employer, self.employer_feedback.employer)
        self.assertEqual(feedback.feedback, self.employer_feedback.feedback)
        self.assertTrue(1 <= feedback.punctuality <= 5)
        self.assertTrue(1 <= feedback.attendance <= 5)
        self.assertTrue(1 <= feedback.dependability <= 5)
        self.assertTrue(1 <= feedback.work_quality <= 5)
        self.assertTrue(1 <= feedback.communication <= 5)
        self.assertTrue(1 <= feedback.attitude <= 5)

    def test_feedback_calculation(self):
        feedback = EmployerFeedback.objects.get(id=self.employer_feedback.id)
        # Calculate expected overall rating
        total_score = (feedback.punctuality + feedback.attendance + feedback.dependability +
                       feedback.work_quality + feedback.communication + feedback.attitude)
        expected_rating = (total_score / 30) * 100
        self.assertAlmostEqual(float(feedback.overall_rating), expected_rating, places=2)

    def test_date(self):
        self.assertTrue((timezone.now() - self.employer_feedback.feedback_date).total_seconds() < 60) # < Allow for 60 second difference

    # Test relationships
    def test_relationships(self):
        self.assertIsInstance(self.employer_feedback.employer, User)
        self.assertIsInstance(self.employer_feedback.citizen, User )


# ====================================== #
#     CUSTOM NOTIFICATION MODEL TEST     #
# ====================================== #
class CustomNotificationTestCase(TestCase):
    def setUp(self):
        self.custom_notification = CustomNotificationFactory()

    def tearDown(self):
        CustomNotification.objects.all().delete()
        Notification.objects.all().delete()

    # Check custom notification creation and extra fields ( URL and info)
    def test_custom_notification_creation(self):
        custom_notification = CustomNotification.objects.get(id=self.custom_notification.id)
        self.assertEqual(custom_notification.url, {"path": "/test-url/"})
        self.assertEqual(custom_notification.extra, {"info": "additional data"})

    # Test updates to the additional data fields
    def test_custom_notification_updates(self):
        # Update data and save
        self.custom_notification.url = {"path": "/new-url/"}
        self.custom_notification.extra = {"info": "new data"}
        self.custom_notification.save()

        # Retrive the updated custom notification
        updated_custom_notification = CustomNotification.objects.get(id=self.custom_notification.id)
        
        # Ensure that the data has been updated correctly
        self.assertEqual(updated_custom_notification.url, {"path": "/new-url/"})
        self.assertEqual(updated_custom_notification.extra, {"info": "new data"})

    # Test relationship
    def test_custom_notification_creation(self):
        custom_notification = CustomNotification.objects.get(id=self.custom_notification.id)
        self.assertEqual(custom_notification.notification, self.custom_notification.notification)



# =============================================================================== #
#                                   FORM TESTS                                    #
# =============================================================================== #
# ====================================== #
#        REGISTRATION FORM TESTS         #
# ====================================== #
class RegisterFormTestCase(TestCase):
    def tearDown(self):
        User.objects.all().delete()

    # Test form with valid input data
    def test_form_valid_data(self):
        form_data = {
            'username': 'user1',
            'password1': 'InsecurePassword2',
            'password2': 'InsecurePassword2'
        }
        form = SignUpForm(data=form_data)

        # Check if form is valid: Expect success
        self.assertTrue(form.is_valid())

        # Save the user and verify new user registration success
        user = form.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, form_data['username'])
        self.assertTrue(user.check_password(form_data['password1']))

    # Test form with invalid input data
    def test_form_invalid_data(self):
        form_data = {
            'username': 'user2',
            'password1': 'InsecurePassword2',
            'password2': 'InsecurePassword33'
        }
        form = SignUpForm(data=form_data)

        # Check if form is valid: Expect password failure
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    # Test form with no input data
    def test_form_no_data(self):
        form = SignUpForm(data={})

        # Check if form is valid: Expect failures
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password1', form.errors)
        self.assertIn('password2', form.errors)


# ====================================== #
#        USER PROFILE FORM TESTS         #
# ====================================== #
class UserProfileFormTestCase(TestCase):
    def setUp(self):
        self.user_profile = UserProfileFactory()
        self.form_data = {
            'email': 'sherlock@test.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '8855664477',
            'address': '221B Baker Street',
            'city': 'London',
            'postcode': '8200',
        }

    def tearDown(self):
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    # Test form with valid input data
    def test_form_valid_data(self):

        form = UserProfileForm(data=self.form_data, instance=self.user_profile)
        
        # Check if form is valid: Expect success
        self.assertTrue(form.is_valid())

    # Test form with invalid input data
    def test_form_invalid_data(self):
        invalid_form_data = {
            'email': 'sherlock.com', 
            'first_name': '',
            'last_name': '',
            'phone': '',
            'address': '',
            'city': '',
            'postcode': '',
        }
        form = UserProfileForm(data=invalid_form_data, instance=self.user_profile)

        # Check if form is valid: Expect success
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 7)  # Expects 7 errors (i.e. error in all fields)

    # Test form cleaning
    def test_form_cleaning(self):
        form = UserProfileForm(data=self.form_data)
        self.assertTrue(form.is_valid())
        
        # Ensure the form cleans the data correctly
        cleaned_data = form.clean()
        for field, value in self.form_data.items():
            self.assertEqual(cleaned_data[field], value)

    # Test form submission
    def test_form_submission(self):

        form = UserProfileForm(instance=self.user_profile, data=self.form_data)
        self.assertTrue(form.is_valid())
        
        # Save the form and check if the profile is updated correctly
        user_profile = form.save(commit=False)
        user_profile.user = self.user_profile.user
        user_profile.save()

        # Verify that the user profile has been updated
        for field, value in self.form_data.items():
            self.assertEqual(getattr(user_profile, field), value)


# ====================================== #
#      EMPLOYER FACILITY FORM TESTS      #
# ====================================== #
class EmployerFacilitiesFormTestCase(TestCase):
    def setUp(self):
        self.test_user = UserFactory()
        self.valid_data = {
            'sound_level': '3.50', 
            'team_count': 10,
            'layout': 'open plan',
            'support_service': True,
            'field': 'engineering'
        }
        self.employer_facility = EmployerFacilities.objects.create(
            employer=self.test_user,
            sound_level=self.valid_data['sound_level'],
            team_count=self.valid_data['team_count'],
            layout=self.valid_data['layout'],
            support_service=self.valid_data['support_service'],
            field=self.valid_data['field']
        )

    def tearDown(self):
        EmployerFacilities.objects.all().delete()
        User.objects.all().delete()

    # Test form with valid input data
    def test_form_valid_data(self):
        form = EmployerFacilitiesForm(data=self.valid_data)
        
        # Check that the form is valid
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")
    
    # Test form submission 
    def test_form_submission(self):
        form = EmployerFacilitiesForm(data=self.valid_data)

        # Save form
        saved_facility = form.save(commit=False)
        saved_facility.employer = self.test_user
        saved_facility.save()
        
        # Retrieve the saved EmployerFacilities object from the database
        facility = EmployerFacilities.objects.get(pk=saved_facility.pk)
        
        # Check if the fields match 
        self.assertEqual(facility.sound_level, float(self.valid_data['sound_level']))
        self.assertEqual(facility.team_count, self.valid_data['team_count'])
        self.assertEqual(facility.layout, self.valid_data['layout'])
        self.assertEqual(facility.support_service, self.valid_data['support_service'])
        self.assertEqual(facility.field, self.valid_data['field'])


# ====================================== #
#              JOB FORM TESTS            #
# ====================================== #
class JobFormTestCase(TestCase):

    def setUp(self):
        # Initialize a JobForm instance
        self.form = JobForm()
        self.valid_data  = {
            'title': 'IT Specialist',
            'company_name': 'ITCompany',
            'location': 'Denmark',
            'description': 'Tech company in Denmark',
            'job_type': 'part-time',
            'job_field': 'it',
            'education': 'other',
        }

    def tearDown(self):
        User.objects.all().delete()
        Job.objects.all().delete()

    # Test form with valid input data
    def test_form_valid_data(self):
        form = JobForm(data=self.valid_data)
        
        # Check that the form is valid
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    # Test form with invalid input data
    def test_form_invalid_data(self):
        invalid_form_data = {
            'title': '',
            'company_name': '',
            'location': '',
            'description': '',
            'job_type': 'on-time',
            'job_field': 'oth.',
            'education': 'high',
        }
        form = JobForm(data=invalid_form_data)

        # Check if form is valid: Expect success
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 7)  # Expects 7 errors (i.e. error in all fields)

    # Test form field type expectations
    def test_form_fields_type(self):
        expected_fields = {
            'title': forms.TextInput,
            'company_name': forms.TextInput,
            'location': forms.TextInput,
            'description': forms.Textarea,
            'job_type': forms.Select,
            'job_field': forms.Select,
            'education': forms.Select,
        }
        for field, widget in expected_fields.items():
            self.assertIn(field, self.form.fields)
            self.assertIsInstance(self.form.fields[field].widget, widget)


# ====================================== #
#           CALENDAR FORM TESTS          #
# ====================================== #
class CalendarFormTestCase(TestCase):
    def setUp(self):
        self.form = CalendarForm()

    def tearDown(self):
        Calendar.objects.all().delete()
        User.objects.all().delete()

    # Test form field type expectations
    def test_form_fields_type(self):
        expected_fields = {
            'liaison': forms.Select,
            'title': forms.TextInput,
            'description': forms.Textarea,
            'start_time': forms.DateTimeInput,
            'end_time': forms.DateTimeInput,
        }
        for field, widget in expected_fields.items():
            self.assertIn(field, self.form.fields)
            self.assertIsInstance(self.form.fields[field].widget, widget)

    # Test form widgets
    def test_field_widgets(self):
        expected_widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

        for field, widget in expected_widgets.items():
            self.assertEqual(self.form.fields[field].widget.attrs, widget.attrs)


# ====================================== #
#      EMPLOYER FEEDBACK FORM TESTS      #
# ====================================== #
class EmployerFeedbackFormTestCase(TestCase):
    def setUp(self):
        self.employer = UserFactory(username='employer')
        self.citizen = UserFactory(username='citizen')
        self.citizen_profile = CitizenProfileFactory(user=self.citizen, employer=self.employer)
        self.form = EmployerFeedbackForm(user=self.employer)

    def tearDown(self):
        User.objects.all().delete()
        EmployerFacilities.objects.all().delete()
        CitizenProfile.objects.all().delete()

    # Test form field type expectations
    def test_form_fields_type(self):
            expected_fields = {
                'citizen': forms.Select,
                'feedback': forms.Textarea,
                'punctuality': forms.Select, 
                'dependability': forms.Select,  
                'work_quality': forms.Select,  
                'communication': forms.Select, 
                'attitude': forms.Select,  
            }
            for field, widget in expected_fields.items():
                self.assertIn(field, self.form.fields)
                self.assertEqual(type(self.form.fields[field].widget), widget)

    # Test form widgets
    def test_field_widgets(self):
        self.assertEqual(
            self.form.fields['feedback'].widget.attrs.get('placeholder'),
            'Enter your feedback here...'
        )

    # Test citizen queryset filter (i.e. only include users with a CitizenProfile where the employer matches the employer of the feecback form)
    def test_form_initialization_with_user(self):
        self.assertEqual(
            list(self.form.fields['citizen'].queryset),
            [self.citizen] 
        )


# ====================================== #
#       CITIZEN FEEDBACK FORM TESTS      #
# ====================================== #
class CitizenFeedbackFormTestCase(TestCase):
    def setUp(self):
        self.user = UserFactory()  
        self.citizen_feedback = CitizenFeedbackFactory(citizen=self.user) 
        self.form = CitizenFeedbackForm(instance=self.citizen_feedback)

    def tearDown(self):
        User.objects.all().delete()
        CitizenFeedback.objects.all().delete()

    # Test form field type expectations
    def test_form_fields(self):
        expected_fields = {
            'feedback': forms.Textarea,
            'job_satisfaction': forms.Select,
            'work_hours': forms.Select,
            'tasks': forms.Select,
            'social_level': forms.Select,
            'stress_level': forms.Select,
            'support_level': forms.Select,
        }
        for field, widget in expected_fields.items():
            self.assertIn(field, self.form.fields)
            self.assertIsInstance(self.form.fields[field].widget, widget)
    
    # Test form widgets
    def test_field_widgets(self):
        self.assertEqual(
            self.form.fields['feedback'].widget.attrs.get('placeholder'),
            'Enter your feedback here...'
        )



# =============================================================================== #
#                               AUTHENTICATION TESTS                              #
# =============================================================================== #
# ====================================== #
#    TWO FACTOR AUTHENTICATION TESTS     #
# ====================================== #
class TOTPTestCase(TestCase):
    def setUp(self):
        self.user_profile = UserProfileFactory()
        self.totp = pyotp.TOTP(self.user_profile.totp_secret_key)

    def tearDown(self):
        UserProfile.objects.all().delete() 
            
    #Check the users 2FA status
    def test_2FA_status(self):
        user = UserProfileFactory(is_2fa_enabled=True)
        self.assertTrue(user.is_2fa_enabled, True)

    # Check if TOTP is generated and validate
    def test_totp_generation_and_validation(self):
        otp = self.totp.now()  # Generate TOTP
        self.assertTrue(self.totp.verify(otp))  # Validate TOTP

    # Check if TOTP expiration 
    def test_totp_expiry(self):
        otp = self.totp.now()
        time.sleep(35)  # Simulate timeperiod of 35 seconds
        
        # Validate the expired TOTP code: Should be false as the expiration time is set to 30 seconds
        self.assertFalse(self.totp.verify(otp))  


# ====================================== #
#              QR CODE TESTS             #
# ====================================== #
class TwoFATestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create user and profile
        self.user = User.objects.create_user(username='user', password='password123')
        self.user_profile = UserProfile.objects.create(user=self.user, user_type='citizen') 
        
        # Sign in user
        self.client.login(username='user', password='password123')
        
        # Define URL 
        self.url_2fa = reverse('setup_otp')

    def tearDown(self):
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    # Test response code
    def test_view_status_code_and_template(self):
        response = self.client.get(self.url_2fa, HTTP_HOST='localhost')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/auth_2fa_qrcode.html')

    # Check QR code in response
    def test_qr_code_in_context(self):
        response = self.client.get(self.url_2fa, HTTP_HOST='localhost')
        self.assertIn('qr_code', response.context)
        qr_code_base64 = response.context['qr_code']
        
        self.assert_valid_image(qr_code_base64)

    # Check if TOTP is saved
    def test_secret_key_saved(self):
        response = self.client.get(self.url_2fa, HTTP_HOST='localhost')
        self.user_profile.refresh_from_db()
        self.assertIsNotNone(self.user_profile.totp_secret_key)

    # Check QR code
    def assert_valid_image(self, qr_code_base64):
        qr_code_bytes = base64.b64decode(qr_code_base64)
        with BytesIO(qr_code_bytes) as buffer:
            try:
                img = Image.open(buffer)
                img.verify()  # Verify that it's a valid image
            except Exception as e:
                self.fail(f"QR Code is not a valid image: {e}")

        # Optionally, check if the QR code matches the expected format (not specific value)
        self.assertTrue(qr_code_base64.startswith('iVBORw0KGgo'), "QR Code is not in PNG format.")


# =============================================================================== #
#                                LOGIN HANDLING TESTS                             #
# =============================================================================== #
# ====================================== #
#               SIGNIN TESTS             #
# ====================================== #
class SigninViewTests(TestCase):
    def setUp(self):
        self.client = Client()  

    def tearDown(self):
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    # Test redirects to MitID broker authentication for Danish users
    def test_redirects_DK(self):
        # Initialise Danish citizen user
        user = UserFactory(username='danish_user')
        user.set_password('password')
        user.save()
        profile = UserProfileFactory(user=user, DK_user='yes', user_type="citizen")
        profile.save()

        # login POST request 
        response = self.client.post(reverse('signin'), {
            'username': 'danish_user',
            'password': 'password'
        })

        # Redirection checks
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/mitid_login.html') 

    # Test redirects to regular login method for non-Danish users
    def test_redirects_others(self):
        # Initialise non-Danish citizen user
        user = UserFactory(username='non_danish_user')
        user.set_password('password')
        user.save()
        UserProfileFactory(user=user, DK_user='no')
        SensoryProfileFactory(user=user)

        # login POST request 
        response = self.client.post(reverse('signin'), {
            'username': 'non_danish_user',
            'password': 'password'
        })

        # Redirection checks
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index')) 

    # Test redirects to 2FA authenticationchecks 
    def test_signin_2fa_redirect(self):
        # Initialise citizen user with 2FA enabled
        user = UserFactory(username='user_with_2fa')
        user.set_password('password')
        user.save()
        profile = UserProfileFactory(user=user, DK_user='no', is_2fa_enabled=True) # Create profile with is_2fa_enabled set to true for the user

        # Print user
        print(f"User: {user.username}")
        print(f"Profile 2FA Enabled: {profile.is_2fa_enabled}")

        # login POST request 
        response = self.client.post(reverse('signin'), {
            'username': 'user_with_2fa',
            'password': 'password'
        })

        # Redirection checks
        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, reverse('verify_2fa'))  


# ====================================== #
#               SIGNUP TESTS             #
# ====================================== #
class SignUpViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.signin_url = reverse('signin')

    def tearDown(self):
        User.objects.all().delete()
        UserProfile.objects.all().delete()

    # Check view, template and forms retrieval
    def test_signup(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/signup.html')
        self.assertIsInstance(response.context['signup_form'], SignUpForm)
        self.assertIsInstance(response.context['user_info'], UserProfileForm)

    # Check registration post
    def test_signup_post(self):
        signup_data = {
            'username': 'sherlockh',
            'password1': 'InsecurePassword1',
            'password2': 'InsecurePassword1',
        }

        user_info_data = {
            'email': 'johndoe@example.com',
            'first_name': 'Sherlock',
            'last_name': 'Holmes',
            'phone': '1234567890',
            'address': '221B Baker Street',
            'city': 'London',
            'postcode': '8000',
        }

        # Registration POST request 
        response = self.client.post(self.signup_url, data={**signup_data, **user_info_data})

        # Redirection checks
        self.assertEqual(response.status_code, 302) 
        self.assertRedirects(response, self.signin_url)

        # Check if the created user is present in the User and UserProfile database models
        self.assertTrue(User.objects.filter(username='sherlockh').exists())
        self.assertTrue(UserProfile.objects.filter(user__username='sherlockh').exists())


# ====================================== #
#              SIGNOUT TESTS             #
# ====================================== #
class SignOutTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.signout_url = reverse('signout')

        # Create user
        self.user = User.objects.create_user(username='testuser', password='password123')

        # Create Site entry
        Site.objects.create(domain='localhost', name='localhost')

    def tearDown(self):
        User.objects.all().delete()

    @patch('django.contrib.sites.models.Site.objects.get')
    def test_signout_view(self, mock_get_site):
        # Set up the mock site
        # Reference: https://stackoverflow.com/questions/52957381/patch-a-variable-inside-a-method-of-a-class-instance 
        mock_site = Site(id=1, domain='localhost', name='localhost')
        mock_get_site.return_value = mock_site
        
        # Log in user
        self.client.login(username='testuser', password='password123')

        # Call the signout view and ensure session is flushed
        response = self.client.get(self.signout_url)
        self.assertIsNone(self.client.session.get('_auth_user_id'))

        # Check response status code 
        self.assertEqual(response.status_code, 200)

        # Check the template
        self.assertTemplateUsed(response, 'spectrumjobs/authentication.html')
        

# =============================================================================== #
#                                  INDEX VIEW TESTS                               #
# =============================================================================== #
class IndexViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')

        # Create users
        self.citizen_user = User.objects.create_user(username='citizen_user', password='password')
        self.employer_user = User.objects.create_user(username='employer_user', password='password')
        self.liaison_user = User.objects.create_user(username='liaison_user', password='password')

        # Create user profiles
        UserProfile.objects.create(user=self.citizen_user, user_type='citizen')
        UserProfile.objects.create(user=self.employer_user, user_type='employer')
        UserProfile.objects.create(user=self.liaison_user, user_type='liaison')

    def tearDown(self):
        User.objects.all().delete()
        UserProfile.objects.all().delete()
    
    # Test redirection and template for citizen users
    def test_index_citizen(self):
        self.client.login(username='citizen_user', password='password')
        response = self.client.get(self.index_url)
        self.assertTemplateUsed(response, 'spectrumjobs/index.html')

    # Test redirection and template for employer users
    def test_index_template_for_employer(self):
        self.client.login(username='employer_user', password='password')
        response = self.client.get(self.index_url)
        self.assertTemplateUsed(response, 'spectrumjobs/index.html')

    # Test redirection and template for liaison users
    def test_index_template_for_liaison(self):
        self.client.login(username='liaison_user', password='password')
        response = self.client.get(self.index_url)
        self.assertTemplateUsed(response, 'spectrumjobs/monitor.html')

# =============================================================================== #
#                                MONITOR VIEW TESTS                               #
# =============================================================================== #
class MonitorViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.monitor_url = reverse('monitor')

        # Create user
        self.liaison_user = User.objects.create_user(username='liaison_user', password='password123')
        self.citizen_user = User.objects.create_user(username='citizen_user', password='password123')
        self.employer_user = User.objects.create_user(username='employer_user', password='password123')

        # Create user profiles
        UserProfile.objects.create(user=self.liaison_user, user_type='liaison')
        UserProfile.objects.create(user=self.citizen_user, user_type='citizen')
        UserProfile.objects.create(user=self.employer_user, user_type='employer')

    def tearDown(self):
        User.objects.all().delete()
        UserProfile.objects.all().delete()
    
    # Test redirection and template for authorised users (liaisons)
    def test_monitor_for_liaison(self):
        self.client.login(username='liaison_user', password='password123')
        response = self.client.get(self.monitor_url)
        self.assertTemplateUsed(response, 'spectrumjobs/monitor.html')

    # Test redirection and template for unauthorised users (citizen)
    def test_monitor_for_employer(self):
        self.client.login(username='employer_user', password='password123')
        response = self.client.get(self.monitor_url)
        # Check if access is correctly denied
        self.assertEqual(response.status_code, 403)

    # Test redirection and template for liaison users
    def test_monitor_for_citizens(self):
        self.client.login(username='citizen_user', password='password123')
        response = self.client.get(self.monitor_url)
        # Check if access is correctly denied
        self.assertEqual(response.status_code, 403)


# =============================================================================== #
#                             PROFILE INFO VIEW TESTS                             #
# =============================================================================== #
class ProfileInfoViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.profile_info_url = reverse('profile_info')

        # Create user and user profile 
        self.test_user = UserFactory()
        self.test_user_profile = UserProfileFactory(user=self.test_user)

        # Set up the mock site
        # Reference: https://stackoverflow.com/questions/52957381/patch-a-variable-inside-a-method-of-a-class-instance 
        self.patcher = patch('django.contrib.sites.models.Site.objects.get_or_create')
        self.mock_site = self.patcher.start()
        self.mock_site.return_value = (Site(id=1, domain='localhost', name='localhost'), True)

    def tearDown(self):
        self.patcher.stop()
        User.objects.all().delete()
        UserProfile.objects.all().delete()

    # Check response and profile data 
    def test_profile_info(self):
        # Authentication
        logged_in = self.client.login(username=self.test_user.username, password='InsecurePassword')
        self.assertTrue(logged_in, "Failed to log in the test user")

        # Check response template
        response = self.client.get(self.profile_info_url)
        self.assertTemplateUsed(response, 'spectrumjobs/profile_info.html')
        
        # Check the reponse contains the correct profile data
        self.assertContains(response, self.test_user.username)

# =============================================================================== #
#              PROFILE DATA VIEW TESTS (LIASION USER DASHBOARD)                   #
# =============================================================================== #
class ProfileDataViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create liaison user and profile
        self.liaison_user = UserFactory(username='liaison', password='defaultpassword')
        self.liaison_user_profile = UserProfileFactory(user=self.liaison_user, user_type='liaison')

        # Create citizen user, profile, sensory, and citizen profile 
        self.citizen_user = UserFactory(username='citizen', password='defaultpassword')
        self.citizen_user_profile = UserProfileFactory(user=self.citizen_user, user_type='citizen')
        self.citizen_profile = CitizenProfileFactory(user=self.citizen_user)
        self.sensory_profile = SensoryProfileFactory(user=self.citizen_user)

        # Create employer user, profile, and employer facility  
        self.employer_user = UserFactory(username='employer', password='defaultpassword')
        self.employer_user_profile = UserProfileFactory(user=self.employer_user, user_type='employer')
        self.employer_profile = EmployerFacilitiesFactory(employer=self.employer_user)

        # Sign the liaison user in
        self.client.login(username='liaison', password='defaultpassword')

        # URLs for citizen and employer (using their user_id)
        self.profile_data_url_citizen = reverse('profile_data', kwargs={'user_id': self.citizen_user.id})
        self.profile_data_url_employer = reverse('profile_data', kwargs={'user_id': self.employer_user.id})

        # Set up the mock site
        # Reference: https://stackoverflow.com/questions/52957381/patch-a-variable-inside-a-method-of-a-class-instance 
        self.patcher = patch('django.contrib.sites.models.Site.objects.get_or_create')
        self.mock_site = self.patcher.start()
        self.mock_site.return_value = (Site(id=1, domain='localhost', name='localhost'), True)

    def tearDown(self):
        self.patcher.stop()
        User.objects.all().delete()
        UserProfile.objects.all().delete()
        SensoryProfile.objects.all().delete()
        CitizenProfile.objects.all().delete()
        EmployerFacilities.objects.all().delete()
        Job.objects.all().delete()
        
    # Test view for citizen users
    def test_profile_data_citizen(self):
        # Check response template
        response = self.client.get(self.profile_data_url_citizen)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/profile_data.html')
        
        # Check the reponse contains the correct data
        self.assertContains(response, self.citizen_user.username)
        self.assertContains(response, self.citizen_user_profile.first_name)
        self.assertContains(response, self.citizen_user_profile.last_name)
        self.assertContains(response, self.citizen_user_profile.user_type)
        self.assertContains(response, self.citizen_profile.contact_person)
        self.assertContains(response, self.citizen_profile.experience)
        self.assertContains(response, self.citizen_profile.job_field)
        self.assertContains(response, self.citizen_profile.job_type)
        self.assertContains(response, self.citizen_profile.support_grants)
        self.assertContains(response, self.citizen_profile.education)
        self.assertContains(response, self.citizen_profile.employed)
        self.assertContains(response, self.citizen_profile.education)
        self.assertContains(response, self.sensory_profile.auditory) 
        self.assertContains(response, self.sensory_profile.visual)  
        self.assertContains(response, self.sensory_profile.smell)  
        self.assertContains(response, self.sensory_profile.tactile)  
        self.assertContains(response, self.sensory_profile.movement)  

    # Test view for employer users
    def test_profile_data_employer(self):
        # Check response template
        response = self.client.get(self.profile_data_url_employer)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/profile_data.html')
        
        # Verify that context data is loaded
        self.assertContains(response, self.employer_user.username)
        self.assertContains(response, self.employer_user_profile.user_type)  
        self.assertContains(response, self.employer_profile.sound_level)  
        self.assertContains(response, self.employer_profile.team_count)  
        self.assertContains(response, self.employer_profile.layout)  
        self.assertContains(response, self.employer_profile.support_service)  
        self.assertContains(response, self.employer_profile.field)  

        

# =============================================================================== #
#                               JOB PORTAL VIEW TESTS                             #
# =============================================================================== #
class PortalViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create citizen user
        self.citizen_user = UserFactory(username='citizen', password='password1')
        self.citizen_user_profile = UserProfileFactory(user=self.citizen_user, user_type='citizen')

        # Create employer user
        self.employer_user = UserFactory(username='employer', password='password2')
        self.employer_user_profile = UserProfileFactory(user=self.employer_user, user_type='employer')

        # Create jobs instances
        self.job1 = JobFactory(title='Software Engineer', description='Develop software', employer=self.employer_user)
        self.job2 = JobFactory(title='Data Scientist', description='Analyze data', employer=self.employer_user)
        self.job3 = JobFactory(
            title='Software Engineer',
                location='New York',
                job_field='it',
                job_type='full-time',
                education='bachelor',
                description='A great opportunity to work as a Software Engineer in New York'
            )
        
        # Define URL
        self.portal_url = reverse('portal')

    def tearDown(self):
        Job.objects.all().delete()
        User.objects.all().delete()
        UserProfile.objects.all().delete()

    # Test view for citizen users
    def test_portal_citizen(self):
        # Authenticate 
        self.client.login(username='citizen', password='password1')
        response = self.client.get(self.portal_url)

        # Check response template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/job_portal.html')

        # Check the reponse contains the jobs
        self.assertIn('jobs', response.context)
        self.assertIn(self.job1, response.context['jobs'])
        self.assertIn(self.job2, response.context['jobs'])

    # Test view for citizen users
    def test_portal_employer(self):
        # Authenticate 
        self.client.login(username='employer', password='password2')
        response = self.client.get(self.portal_url)
        
        # Check response template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/job_portal.html')

        # Check if the job post form present
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'])

    # Test view for guest users
    def test_portal_guest(self):
        # Check response template
        response = self.client.get(self.portal_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/job_portal.html')

        # Check if the reponse contains the jobs
        self.assertIn('jobs', response.context)
        self.assertIn(self.job1, response.context['jobs'])
        self.assertIn(self.job2, response.context['jobs'])

    # Test the job search functionality
    def test_portal_query_parameters(self):
        # Define query parameters
        query_params = {
            'title_description': 'Software Engineer',
            'location': 'New York',
            'job_field': 'it',
            'job_type': 'full-time',
            'education_level': 'bachelor',
            'sort_by': ''
        }
        response = self.client.get(self.portal_url, data=query_params)

        # Get jobs from response context and cinvert to list of dictionaries 
        jobs = response.context.get('jobs', [])
        job_info_list = [
            {
                'title': job.title,
                'location': job.location,
                'job_type': job.job_type,
                'description': job.description
            }
            for job in jobs
        ]

        # Check if the query parameters find the mathing job3 
        job_titles = [job['title'] for job in job_info_list]
        self.assertIn(self.job3.title, job_titles)
        self.assertIn(self.job3.location, [job['location'] for job in job_info_list])
        self.assertIn(self.job3.job_type, [job['job_type'] for job in job_info_list])
        self.assertTrue(any(self.job3.description in job['description'] for job in job_info_list))



# =============================================================================== #
#                               JOB DETAIL VIEW TESTS                             #
# =============================================================================== #
class JobDetailsViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Job instance
        self.job = JobFactory(
            title='Software Engineer',
            location='New York',
            job_field='it',
            job_type='full-time',
            education='bachelor',
            description='A great opportunity to work as a Software Engineer in New York'
        )

        # Define job URL
        self.job_details_url = reverse('job_details', kwargs={'job_id': self.job.id})

    def tearDown(self):
        Job.objects.all().delete()

    def test_job_details_view_retrieves_correct_job(self):
        # Check response template
        response = self.client.get(self.job_details_url)
        self.assertEqual(response.status_code, 200)

        # Check if context job matches the job ID of  the URL
        job = response.context.get('job')
        self.assertEqual(job.id, self.job.id)
        self.assertEqual(job.pk, self.job.id)


# =============================================================================== #
#                             JOB POST/DELETE VIEW TESTS                          #
# =============================================================================== #
class JobAddandDeleteTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.post_job_url = reverse('post_job')

        # Create user and profile
        self.employer_user = User.objects.create_user(username='employer', password='defaultpassword')
        self.employer_profile = UserProfile.objects.create(user=self.employer_user, user_type='employer')

        # Create job
        self.job = Job.objects.create(
            title='Software Engineer In Overalls',
            description='A great job for software engineers',
            location='New York',
            job_field='IT',
            job_type='Full-time',
            education='Bachelor',
            employer=self.employer_user
        )

        # Ensure employer user is logged in
        self.client.login(username='employer', password='defaultpassword')

        # Define the post URL 
        self.portal_url = reverse('portal')

        # Define the delete URL 
        self.delete_job_url = reverse('delete_job', kwargs={'job_id': self.job.id})

    def tearDown(self):
        Job.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    def test_view_response(self):
        response = self.client.get(self.post_job_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/post_job.html')
        self.assertIsInstance(response.context['form'], JobForm)

    # Check to see if the job is created
    def test_job_add(self):
        self.assertTrue(Job.objects.filter(description='A great job for software engineers').exists())

    # Check to see if the job is deleted
    def test_delete_job(self):
        # Check response redirect (delete post)
        response = self.client.post(self.delete_job_url)
        self.assertEqual(response.status_code, 302)

        # Verify the job was deleted
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())


# =============================================================================== #
#                             JOB APPLICATION VIEW TESTS                          #
# =============================================================================== #
class JobApplicationTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create users
        self.citizen_user = User.objects.create_user(username='citizen', password='password123')
        self.employer_user = User.objects.create_user(username='employer', password='password123')
        self.liaision_user = User.objects.create_user(username='liaison', password='password123')

        # Create profiles
        self.citizen_profile = UserProfile.objects.create(user=self.citizen_user, user_type='citizen')
        self.employer_profile = UserProfile.objects.create(user=self.employer_user, user_type='employer')
        self.liaision_user = UserProfile.objects.create(user=self.liaision_user, user_type='liaison')

        # Create a job
        self.job = Job.objects.create(
            title='Software Engineer',
            description='A great job for software engineers',
            location='New York',
            job_field='IT',
            job_type='Full-time',
            education='Bachelor',
            employer=self.employer_user
        )

        # Define URLs 
        self.apply_job_url = reverse('apply_job', kwargs={'job_id': self.job.id})
        print("id:",self.job.id)
        self.portal_url = reverse('portal')

    def tearDown(self):
        Job.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    # Test apply_job_view as a citizen user
    def test_apply_job_as_citizen(self):
        # Sign in
        self.client.login(username='citizen', password='password123')

        # Apply and check response
        response = self.client.post(self.apply_job_url)
        self.assertEqual(response.status_code, 302)  
        self.assertRedirects(response, self.portal_url)

        # Check if applicaiton is added in database
        self.job.refresh_from_db()
        self.assertIn(self.citizen_user, self.job.applicants.all())

    # Test apply_job_view as a employer user
    def test_apply_job_as_employer(self):
        # Sign in
        self.client.login(username='employer', password='password123')

        # Apply and check response
        response = self.client.post(self.apply_job_url)
        self.assertEqual(response.status_code, 302) 
        self.assertRedirects(response, self.portal_url)

        # Check if applicaiton is not added in database
        self.job.refresh_from_db()
        self.assertNotIn(self.citizen_user, self.job.applicants.all())

    # Test apply_job_view as a liaison user
    def test_apply_job_as_liaison(self):
        # Sign in
        self.client.login(username='liaison', password='password123')

        # Apply and check response
        response = self.client.post(self.apply_job_url)
        self.assertEqual(response.status_code, 302) 
        self.assertRedirects(response, self.portal_url)

        # Check if applicaiton is not added in database
        self.job.refresh_from_db()
        self.assertNotIn(self.citizen_user, self.job.applicants.all())



# =============================================================================== #
#                                 CALENDAR VIEW TESTS                             #
# =============================================================================== #
class CalendarViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create user and profile
        self.user = User.objects.create_user(username='liaisonuser', password='password123')
        UserProfile.objects.create(user=self.user, user_type='liaison') 
        
        # Sign in the liaison user
        self.client.login(username='liaisonuser', password='password123')
        
        # Create appointment
        self.appointment = Calendar.objects.create(
            title='Test Appointment',
            description='Test Description',
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            user=self.user,
            liaison=self.user
        )
        
        # Define URLs 
        self.get_appointments_url = reverse('get_appointments')
        self.add_appointment_url = reverse('add_appointment')
        self.update_appointment_url = reverse('update_appointment', args=[self.appointment.id])
        self.delete_appointment_url = reverse('delete_appointment', args=[self.appointment.id])

    def tearDown(self):
        Calendar.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    # Check appointment retrieval
    def test_get_appointments(self):
        # Check response 
        response = self.client.get(self.get_appointments_url)
        self.assertEqual(response.status_code, 200)

        # Ensure the appointment data is included
        self.assertContains(response, 'Test Appointment') 

    # Check appointment updates
    def test_update_appointment(self):
        updated_data = {
            'title': 'Updated Appointment',
            'description': 'Updated Description',
        }
        # Check response 
        response = self.client.post(self.update_appointment_url, json.dumps(updated_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Reload database and ensure the appointment data is uopdated
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.title, 'Updated Appointment')

    # Check appointment deletion
    def test_delete_appointment(self):
        # Check response 
        response = self.client.post(self.delete_appointment_url, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # Check if corresponding appointment has been deleted
        self.assertFalse(Calendar.objects.filter(id=self.appointment.id).exists())


# =============================================================================== #
#                                 MESSAGES VIEW TESTS                             #
# =============================================================================== #
class MessageViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Create users
        self.sender_user = UserFactory.create(username='sender', password='password123')
        self.recipient_user = UserFactory.create(username='recipient', password='password123')

        # Create user profiles
        UserProfile.objects.create(user=self.sender_user, user_type='citizen')
        UserProfile.objects.create(user=self.recipient_user, user_type='citizen')

        # Create messages using MessageFactory
        self.message_received = MessageFactory.create(sender=self.sender_user, recipient=self.recipient_user, read=False)
        self.message_sent = MessageFactory.create(sender=self.sender_user, recipient=self.recipient_user, read=True)
        self.message_draft = MessageFactory.create(sender=self.sender_user, recipient=self.recipient_user, read=False, subject='Draft Message', body='This is a draft message.', timestamp=timezone.now())

        # Define URLs
        self.inbox_url = reverse('inbox')
        self.get_message_url = lambda pk: reverse('get_message', kwargs={'pk': pk})
        self.sent_messages_url = reverse('sent')
        self.drafts_messages_url = reverse('drafts')
        self.compose_message_url = reverse('compose_message')

    def tearDown(self):
        Message.objects.all().delete()
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    def test_inbox_view(self):
        # Sign in
        self.client.login(username='recipient', password='password123')

        # Get URL response and check
        response = self.client.get(self.inbox_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/message_inbox.html')
        self.assertIn('messages', response.context)
        self.assertIn(self.message_received, response.context['messages'])
        self.assertEqual(response.context['user_type'], 'citizen')

    def test_get_message_view(self):
        # Sign in
        self.client.login(username='recipient', password='password123')
        
        # Get URL response and check
        response = self.client.get(self.get_message_url(self.message_received.id))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/message_body.html')
        self.assertIn('message', response.context)
        self.assertEqual(response.context['message'], self.message_received)

    def test_sent_messages_view(self):
        # Sign in
        self.client.login(username='sender', password='password123')

        # Get URL response and check
        response = self.client.get(self.sent_messages_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/message_inbox.html')
        self.assertIn('messages_sent', response.context)
        self.assertIn(self.message_sent, response.context['messages_sent'])

    def test_drafts_messages_view(self):
        # Sign in
        self.client.login(username='sender', password='password123')

        # Get URL response and check
        response = self.client.get(self.drafts_messages_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spectrumjobs/message_inbox.html')

    def test_compose_message_view(self):
         # Sign in
        self.client.login(username='sender', password='password123')

        # Create message response and check
        response = self.client.post(self.compose_message_url, {
            'recipient': 'recipient',
            'subject': 'Test Subject',
            'body': 'Test Body'
        })
        self.assertEqual(response.status_code, 302) 
        self.assertRedirects(response, self.inbox_url)

        # Check that the message was created
        self.assertTrue(Message.objects.filter(subject='Test Subject', body='Test Body').exists())



# =============================================================================== #
#                                SUGGESTIONS VIEW TESTS                           #
# =============================================================================== #
class GetMatchesTestCase(TestCase):
    def setUp(self):
        # Create users
        self.citizen_user = User.objects.create_user(username='citizen_user', password='password')
        self.employer_user = User.objects.create_user(username='employer_user', password='password')
        self.liaison_user = User.objects.create_user(username='liaison_user', password='password')

        # Create profiles
        UserProfile.objects.create(user=self.citizen_user, user_type='citizen')
        UserProfile.objects.create(user=self.employer_user, user_type='employer')
        UserProfile.objects.create(user=self.liaison_user, user_type='liaison')

        # Create sensory profiles
        self.sensory_profile_citizen = SensoryProfile.objects.create(
            user=self.citizen_user, auditory=Decimal('4.50'), visual=Decimal('3.25'), smell=Decimal('2.00'),
            tactile=Decimal('5.00'), movement=Decimal('1.75')
        )
        self.sensory_profile_employer = SensoryProfile.objects.create(
            user=self.employer_user, auditory=Decimal('3.00'), visual=Decimal('4.00'), smell=Decimal('2.50'),
            tactile=Decimal('3.50'), movement=Decimal('4.25')
        )

        # Create Jobs 
        self.job1 = Job.objects.create(employer=self.employer_user, job_field='it', job_type='contract', education='bachelor')
        self.job2 = Job.objects.create(employer=self.employer_user, job_field='office', job_type='part-time', education='master')

        # Create citizen profile 
        self.citizen_profile = CitizenProfile.objects.create(user=self.citizen_user, job_field='it', job_type='contract', education='bachelor', support_grants='50%')

    # Test suggestions for citizen
    def test_get_matches_for_citizen(self):
        # Get all jobs
        jobs = Job.objects.all()

        # Use get_matches functions to get suggestions
        matches = get_matches(jobs, self.citizen_user, 'citizen')

        # Check suggestion results
        self.assertTrue(matches)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]['job'], self.job1) 

    # Test suggestions for employers
    def test_get_matches_for_employer(self):
        # Get employer job
        job = self.job1

        # Use get_matches functions to get suggestions
        matches = get_matches(job, self.sensory_profile_employer, 'employer')
        
        # Check suggestion results
        self.assertTrue(matches)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['citizen'], self.citizen_user)  # Verify matched citizen
    
    # Test suggestions for liaisons
    def test_get_matches_for_liaison(self):
        # Get all jobs
        jobs = Job.objects.all()

        # Use get_matches functions to get suggestions
        matches = get_matches(jobs, self.liaison_user, 'liaison')

        # Check suggestion results: Expect to be empty for liaisons
        self.assertEqual(matches, [])  

    # Test suggestions with no sensory profile: Expect empty list
    def test_no_sensory_profiles(self):
        # Create user with no sensory profile
        user_no_profile = User.objects.create_user(username='no_profile_user', password='password')
        UserProfile.objects.create(user=user_no_profile, user_type='citizen')

        # Get all jobs
        jobs = Job.objects.all()

        # Use get_matches functions to get suggestions
        matches = get_matches(jobs, user_no_profile, 'citizen')

        # Check suggestion results: Expect to be empty as a sensory profile is required
        self.assertEqual(matches, [])  

    # Test suggestions with no jobs: Expect empty list
    def test_no_jobs(self):
        # Remove jobs
        Job.objects.all().delete()  

        # Check suggestion results: Expect to be empty as jobs is required
        matches = get_matches(Job.objects.all(), self.citizen_user, 'citizen')
        self.assertEqual(matches, [])  



# =============================================================================== #
#                             UTILITY FUNCTIONS TESTS                             #
# =============================================================================== #
# ====================================== #
#       MITID REPONSODE CODE TESTS       #
# ====================================== #
class MitIDCodeValidatorTestCase(TestCase):
    
    # Check  32-character valid hex code
    def test_valid_code(self):
        valid_code = '1234567890abcdefABCDEF1234567890'
        result = validate_third_party_code(valid_code)
        self.assertTrue(result)

    # Check 32-character valid hex code in lowercase
    def test_valid_code_with_lowercase(self):
        valid_code = 'abcdefabcdefabcdefabcdefabcdefab' 
        result = validate_third_party_code(valid_code)
        self.assertTrue(result)

    # Check invalid lenght hex code 
    def test_invalid_code_length(self):
        invalid_code = '1234567890abcdef' 
        result = validate_third_party_code(invalid_code)
        self.assertFalse(result)

    # Check invalid characters hex code 
    def test_invalid_code_characters(self):
        invalid_code = '1234567890abcdefXYZ1234567890'
        result = validate_third_party_code(invalid_code)
        self.assertFalse(result)

    # Check invalid characters and length hex code 
    def test_invalid_code_length_and_characters(self):
        invalid_code = '1234567890abcdXYZ1234567890'
        result = validate_third_party_code(invalid_code)
        self.assertFalse(result)

    # Check empty hex code 
    def test_empty_code(self):
        empty_code = ''
        result = validate_third_party_code(empty_code)
        self.assertFalse(result)


# ====================================== #
#          CUSTOM DECORATOR TESTS        #
# ====================================== #
class LiaisonOnlyDecoratorTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.liaison_user = User.objects.create_user(username='liaisonuser', password='password123')
        self.citizen_user = User.objects.create_user(username='citizen', password='password123')

        # Create user profiles
        UserProfile.objects.create(user=self.liaison_user, user_type='liaison')
        UserProfile.objects.create(user=self.citizen_user, user_type='citizen')

        # Define URL
        self.url_protected = reverse('profile_data', kwargs={'user_id': self.citizen_user.id})

    def tearDown(self):
        UserProfile.objects.all().delete()
        User.objects.all().delete()

    @patch('spectrumjobs.utils.liaison_only')  
    def test_liaison_access(self, mock_liaison_only):
        mock_liaison_only.side_effect = lambda view_func: view_func
        
        # Sign in and go to protected endpoint
        self.client.login(username='liaisonuser', password='password123')
        response = self.client.get(self.url_protected)
        
        # Check if access is correctly granted 
        self.assertEqual(response.status_code, 200)

    @patch('spectrumjobs.utils.liaison_only') 
    def test_non_liaison_access(self, mock_liaison_only):
        mock_liaison_only.side_effect = lambda view_func: view_func
        
        # Sign in and go to protected endpoint
        self.client.login(username='citizen', password='password123')
        response = self.client.get(self.url_protected)
        
        # Check if access is correctly denied
        self.assertEqual(response.status_code, 403)

    @patch('spectrumjobs.utils.liaison_only')
    def test_user_profile_does_not_exist(self, mock_liaison_only):
        mock_liaison_only.side_effect = lambda view_func: view_func
        
        # Aceess the protected endpoint without a user type defined by the extended User model
        user_without_profile = User.objects.create_user(username='nouserprofile', password='password123')
        self.client.login(username='nouserprofile', password='password123')
        response = self.client.get(self.url_protected)
        
        # Check if access is correctly denied
        self.assertEqual(response.status_code, 403)

    @patch('spectrumjobs.utils.liaison_only')
    def test_guest_user(self, mock_liaison_only):
        mock_liaison_only.side_effect = lambda view_func: view_func
        
        # Aceess the protected endpoint as guest user
        response = self.client.get(self.url_protected)
        
        # Check if access is correctly denied (i.e., redirected to the authentication page)
        self.assertEqual(response.status_code, 302)
