import factory
from .models import *
from django.contrib.auth.models import User
import pyotp
import random
from decimal import Decimal
from django.utils import timezone
from factory import django, Faker, LazyAttribute
from datetime import timedelta
from decimal import Decimal

# =============================================================================== #
#                           DEFAULT USER MODEL FACTORY                            #
# =============================================================================== #
# Simple model factory for checking user creation, mainly used to initialise user and related profile 
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', 'InsecurePassword')



# =============================================================================== #
#                           USER PROFILE MODELE FACTORY                           #
# =============================================================================== #
class UserProfileFactory(factory.django.DjangoModelFactory):
    #model
    class Meta:
        model = UserProfile

    #field values
    user = factory.SubFactory(UserFactory) 
    user_type = factory.Faker('random_element', elements=['citizen', 'liaison', 'employer'])
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    address = factory.Faker('address')
    city = factory.Faker('city')
    postcode = factory.Faker('postcode')
    phone = factory.Faker('phone_number')
    email = factory.Faker('email')
    totp_secret_key = factory.LazyAttribute(lambda x: pyotp.random_base32())  # Generate a random TOTP secret key

# =============================================================================== #
#                           SENSORY PROFILE MODEL FACTORY                         #
# =============================================================================== #
class SensoryProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SensoryProfile

    #field values
    user = factory.SubFactory(UserFactory) 
    auditory = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    visual = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    smell = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    tactile = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    movement = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))


# =============================================================================== #
#                          CITIZEN PROFILE MODEL FACTORY                          #
# =============================================================================== #
class CitizenProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CitizenProfile

    #field values
    user = factory.SubFactory(UserFactory)
    age = factory.Faker('random_int', min=18, max=99)
    experience = factory.Faker('random_int', min=0, max=40)
    job_field = factory.Faker('random_element', elements=[choice[0] for choice in CitizenProfile.JOB_FIELDS])
    job_type = factory.Faker('random_element', elements=[choice[0] for choice in CitizenProfile.JOB_TYPES])
    support_grants = factory.Faker('random_element', elements=[choice[0] for choice in CitizenProfile.SUPPORT_NEEDS])
    education = factory.Faker('random_element', elements=[choice[0] for choice in CitizenProfile.EDUCATION])
    employed = True
    employment_date = LazyAttribute(lambda x: timezone.now() - timezone.timedelta(days=random.randint(0, 365)))  
    employer_feedback = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    citizen_feedback = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    employer = factory.SubFactory(UserFactory)
    contact_person = factory.SubFactory(UserFactory)


# =============================================================================== #
#                           EMPLOYER FACILITY MODEL FACTORY                       #
# =============================================================================== #
class EmployerFacilitiesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployerFacilities

    #field values
    employer = factory.SubFactory(UserFactory)
    sound_level = factory.LazyAttribute(lambda x: round(random.uniform(0, 5), 2))
    team_count = factory.LazyAttribute(lambda x: random.randint(0, 100))
    layout = factory.Faker('random_element', elements=[choice[0] for choice in EmployerFacilities.LAYOUT])
    support_service = factory.Faker('boolean')
    field = factory.Faker('random_element', elements=[choice[0] for choice in EmployerFacilities.COMPANY_FIELDS])


# =============================================================================== #
#                                  JOB MODEL FACTORY                              #
# =============================================================================== #
class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    #field values
    employer = factory.SubFactory(UserFactory)
    company_name = factory.Faker('company')
    title = factory.Faker('job')
    location = factory.Faker('address')
    description = factory.Faker('text')
    job_field = factory.Faker('random_element', elements=[choice[0] for choice in Job.JOB_FIELDS])
    job_type = factory.Faker('random_element', elements=[choice[0] for choice in Job.JOB_TYPES])
    education = factory.Faker('random_element', elements=[choice[0] for choice in Job.EDUCATION])


# =============================================================================== #
#                           JOB DESCRIPTION MODEL FACTORY                         #
# =============================================================================== #
class JobDescriptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobDescription

    #field values
    job = factory.SubFactory(JobFactory)
    responsibilities = factory.Faker('text')
    requirements = factory.Faker('text')


# =============================================================================== #
#                                CALENDAR MODEL FACTORY                           #
# =============================================================================== #
class CalendarFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Calendar

    #field values
    title = factory.Faker('sentence', nb_words=6)
    description = factory.Faker('text', max_nb_chars=200)
    start_time = factory.LazyFunction(lambda: timezone.now())
    end_time = factory.LazyAttribute(lambda o: o.start_time + timedelta(hours=1))
    user = factory.SubFactory(UserFactory)
    liaison = factory.SubFactory(UserFactory)



# =============================================================================== #
#                               MESSSAGE MODEL FACTORY                            #
# =============================================================================== #
class MessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Message

    #field values
    sender = factory.SubFactory(UserFactory)
    recipient = factory.SubFactory(UserFactory)
    subject = factory.Faker('sentence', nb_words=6)
    body = factory.Faker('text', max_nb_chars=200)
    timestamp = factory.LazyFunction(timezone.now)
    read = False



# =============================================================================== #
#                            CONVERSATION MODEL FACTORY                           #
# =============================================================================== #
class ConversationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Conversation
        
    #field values
    contact = factory.Faker('name')  # Generate a random name for contact
    sender = factory.Faker('name')   # Generate a random name for sender
    message = factory.Faker('text')  # Generate random text for the message
    timestamp = factory.LazyFunction(timezone.now)  # Use current time for timestamp


# =============================================================================== #
#                           CITIZEN FEEDBACK MODEL FACTORY                        #
# =============================================================================== #
class CitizenFeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CitizenFeedback

    #field values
    citizen = factory.SubFactory(UserFactory)
    feedback = factory.Faker('text', max_nb_chars=200)
    job_satisfaction = factory.Faker('random_int', min=1, max=5)
    work_hours = factory.Faker('random_int', min=1, max=5)
    tasks = factory.Faker('random_int', min=1, max=5)
    social_level = factory.Faker('random_int', min=1, max=5)
    stress_level = factory.Faker('random_int', min=1, max=5)
    support_level = factory.Faker('random_int', min=1, max=5)
    feedback_date = factory.LazyFunction(timezone.now)


# =============================================================================== #
#                           EMPLOYER FEEDBACK MODEL FACTORY                       #
# =============================================================================== #
class EmployerFeedbackFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EmployerFeedback

    #field values
    employer = factory.SubFactory(UserFactory)
    citizen = factory.SubFactory(UserFactory)
    feedback = factory.Faker('text', max_nb_chars=200)
    punctuality = factory.Faker('random_int', min=1, max=5)
    attendance = factory.Faker('random_int', min=1, max=5)
    dependability = factory.Faker('random_int', min=1, max=5)
    work_quality = factory.Faker('random_int', min=1, max=5)
    communication = factory.Faker('random_int', min=1, max=5)
    attitude = factory.Faker('random_int', min=1, max=5)
    overall_rating = factory.LazyAttribute(lambda o: (o.punctuality + o.attendance + o.dependability +
                                                        o.work_quality + o.communication + o.attitude) / 6)
    feedback_date = factory.LazyFunction(timezone.now)
    citizen = factory.SubFactory(UserFactory)


# =============================================================================== #
#                             NOTIFCATION MODEL FACTORY                           #
# =============================================================================== #
class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    #field values
    recipient = factory.SubFactory(UserFactory)
    actor = factory.SubFactory(UserFactory)
    verb = factory.Faker('word')
    public = factory.Faker('boolean')



# =============================================================================== #
#                        CUSTOM NOTIFCATION MODEL FACTORY                         #
# =============================================================================== #
class CustomNotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomNotification

    #field values
    notification = factory.SubFactory(NotificationFactory)
    url = factory.LazyAttribute(lambda _: {"path": "/test-url/"})
    extra = factory.LazyAttribute(lambda _: {"info": "additional data"})