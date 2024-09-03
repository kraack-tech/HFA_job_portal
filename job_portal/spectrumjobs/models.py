from django.db import models
from django.contrib.auth.models import User
import pyotp
from django.core.validators import MaxValueValidator, MinValueValidator
from notifications.models import Notification

# =============================================================================== #
#                               CUSTOM USER MODEL                                 #
# =============================================================================== #
class UserProfile(models.Model):
    # User type choices
    USER_TYPES = (
        ('citizen', 'Citizen'),
        ('liaison', 'Liaison'),
        ('employer', 'Employer'),
        ('none', 'None'),
    )

    # User nationality choices
    DANISH_USER = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    # User fields
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='none')
    DK_user = models.CharField(max_length=3, choices=DANISH_USER, default='')
    contact_person = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=150, default='')
    last_name = models.CharField(max_length=150, default='')
    email = models.EmailField() 
    phone = models.CharField(max_length=20, default='')
    address = models.CharField(max_length=150, default='')
    city = models.CharField(max_length=150, default='')
    postcode = models.CharField(max_length=5, default='')
    totp_secret_key = models.CharField(max_length=64, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False) #2FA control flag

    # Funtion for verifying the one-time password
    def verify_otp(self, otp):
        if self.totp_secret_key:
            # Temporary otp object
            totp = pyotp.TOTP(self.totp_secret_key)
            # Verify user provided otp
            return totp.verify(otp)
        return False

    def __str__(self):
        return self.user.username


# =============================================================================== #
#                         CITIZEN EMPLOYMENT PROFILE MODEL                        #
# =============================================================================== #
# Model used for citizen job market experience and work capabilities
class CitizenProfile(models.Model):
    # Job type capabilities choices
    JOB_TYPES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
        ('other', 'Other'),
    ]
    
    # Job field experience choices
    JOB_FIELDS = [
        ('it', 'IT'),
        ('engineering', 'Engineering'),
        ('management ', 'Management '),
        ('teaching', 'Teaching'),
        ('social/health', 'Social/Health'),
        ('trade/service', 'Trade/Service'),
        ('sales', 'Sales'),
        ('law', 'Law'),
        ('industry', 'Industry'),
        ('craft', 'Craft'),
        ('office', 'Office'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]
    
    # Support level choices
    SUPPORT_NEEDS = [
        ('none', 'None'),
        ('10%', '10%'),
        ('20%', '20%'),     
        ('30%', '30%'),      
        ('40%', '40%'),      
        ('50%', '50%'),      
        ('60%', '60%'),
        ('70%', '70%'),
        ('80%', '80%'),     
        ('90%', '90%'),      
        ('100%', '100%'),      
        ('other', 'Other'),
    ]
    
    # Educational level choices
    EDUCATION = [
        ('none', 'None'),
        ('primary', 'Primary'),
        ('lower secondary', 'Lower Secondary'),
        ('upper secondary', 'Upper Secondary'),
        ('short tertiary', 'Short Tertiary'),
        ('bachelor', 'Bachelor'),
        ('master', ' Master'),
        ('phd', 'PhD'),
        ('doctoral', 'Doctoral'),
        ('other', 'Other'),
    ]

    # Citizen employment fields
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    age = models.IntegerField(default=0)
    experience = models.IntegerField(default=0)
    job_field = models.CharField(max_length=20, choices=JOB_FIELDS, default='other')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='other')
    support_grants = models.CharField(max_length=7, choices=SUPPORT_NEEDS, default='other')
    education = models.CharField(max_length=20, choices=EDUCATION, default='other')
    employed = models.BooleanField(default='False')
    employment_date = models.DateTimeField(null=True, blank=True)
    employer_feedback = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)],null=True, blank=True)
    citizen_feedback = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)],null=True, blank=True)
    employer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='employer'
    )
    contact_person = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='contact_person'
    )

# =============================================================================== #
#                          EMPLOYER FACILITY PROFILE MODEL                        #
# =============================================================================== #
# Model used for employer work-place details, such as layout design, noise level, domain, no. of team members, and supportive services
class EmployerFacilities(models.Model):
    # Work-plan layout design choices
    LAYOUT = [
        ('traditional ', 'Traditional'),
        ('open plan', 'Open Plan'),
        ('cubicle', 'Cubicle'),
        ('team-based', 'Team-based'),
        ('hot desking', 'Hot Desking'),
        ('individual', 'Individual'),
        ('abw', 'ABW'),
        ('other', 'Other'),
    ]

    # Domain choices
    COMPANY_FIELDS = [
        ('it', 'IT'),
        ('engineering', 'Engineering'),
        ('management ', 'Management '),
        ('teaching', 'Teaching'),
        ('social/health', 'Social/Health'),
        ('trade/service', 'Trade/Service'),
        ('sales', 'Sales'),
        ('law', 'Law'),
        ('industry', 'Industry'),
        ('craft', 'Craft'),
        ('office', 'Office'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]

    # Employer facility fields
    employer = models.ForeignKey(User, on_delete=models.CASCADE)
    sound_level = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    team_count = models.IntegerField(default=0)
    layout = models.CharField(max_length=20, choices=LAYOUT, default='other')
    support_service = models.BooleanField(default=False)
    field = models.CharField(max_length=20, choices=COMPANY_FIELDS, default='other')


# =============================================================================== #
#                          CONTACT PERSON PROFILE MODEL                           #
# =============================================================================== #
class ContactProfile(models.Model):
    contact = models.ForeignKey(User, on_delete=models.CASCADE)


# =============================================================================== #
#                           SENSORY PROFILE/TRAINING MODEL                        #
# =============================================================================== #
# Model used for sensory profiles of citizens and sensory training of employers
# Designed to mimick Dunn's (1997a) Model of Sensory Processing
class SensoryProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    auditory = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    visual = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    smell = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    tactile = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])
    movement = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)])



# =============================================================================== #
#                                JOBS POST MODEL                                  #
# =============================================================================== #
class Job(models.Model):
    # Job type choices
    JOB_TYPES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
        ('other', 'Other'),
    ]

    # Job field choices
    JOB_FIELDS = [
        ('it', 'IT'),
        ('engineering', 'Engineering'),
        ('management ', 'Management '),
        ('teaching', 'Teaching'),
        ('social/health', 'Social/Health'),
        ('trade/service', 'Trade/Service'),
        ('sales', 'Sales'),
        ('law', 'Law'),
        ('industry', 'Industry'),
        ('craft', 'Craft'),
        ('office', 'Office'),
        ('finance', 'Finance'),
        ('other', 'Other'),
    ]

    # Education level choices
    EDUCATION = [
        ('none', 'None'),
        ('primary ', 'Primary '),
        ('lower secondary', 'Lower Secondary'),
        ('upper secondary', 'Upper Secondary'),
        ('short tertiary', 'Short Tertiary'),
        ('bachelor', 'Bachelor'),
        ('master', ' Master'),
        ('phd', 'PhD'),
        ('doctoral', 'Doctoral'),
        ('other', 'Other'),
    ]

    # Job fields
    employer = models.ForeignKey(User, on_delete=models.CASCADE)
    applicants = models.ManyToManyField(User, related_name='applied_jobs', blank=True)
    company_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    description = models.TextField()
    job_field = models.CharField(max_length=20, choices=JOB_FIELDS, default='other')
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='full-time')
    education = models.CharField(max_length=20, choices=EDUCATION, default='other')
    posted_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# =============================================================================== #
#                             JOBS DESCRIPTION MODEL                              #
# =============================================================================== #
class JobDescription(models.Model):
    # Job description fields
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_descriptions')
    responsibilities = models.TextField()
    requirements = models.TextField()

    def __str__(self):
        return self.title

# =============================================================================== #
#                                 CALENDAR MODEL                                  #
# =============================================================================== #
# Used for storing appointments created with the FullCalendar library
class Calendar(models.Model):
    # Fields for apppointments
    title = models.CharField(max_length=200)
    description = models.TextField(default='') 
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user')
    liaison = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liaison', default='')

    def __str__(self):
        return self.title
    

# =============================================================================== #
#                                 MESSAGE MODEL                                   #
# =============================================================================== #
# Used for sending and recieving messages 
class Message(models.Model):
    # Fields for messages
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return self.subject
    

# =============================================================================== #
#                                LIVE-CHAT MODEL                                  #
# =============================================================================== #
# Used for real-time chat between citizen and their assigned contact person
# Reference: Advanced Web Development[CM3035] - week 12, 6.407 Implement a consumer 
class Conversation(models.Model):
    contact = models.CharField(max_length=42)
    sender = models.CharField(max_length=100)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


# =============================================================================== #
#                             CUSTOM NOTIFICATION MODEL                           #
# =============================================================================== #
# Used for extending the standard Notification model
class CustomNotification(models.Model):
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='custom_notification')
    url = models.JSONField(default=dict)
    extra = models.JSONField(default=dict)


# =============================================================================== #
#                        CITIZEN EMPLOYMENT FEEDBACK MODEL                        #
# =============================================================================== #
# Used for the monthly feedback of employed citizens
class CitizenFeedback(models.Model):
    # Feedback fields
    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField(blank=True, null=True)
    job_satisfaction = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    work_hours = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    tasks = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    social_level = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    stress_level = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    support_level = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    overall_rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  
    feedback_date = models.DateTimeField(auto_now_add=True)  
    
    # Calculate overall rating
    def save(self, *args, **kwargs):
       
        total_score = (self.job_satisfaction + self.work_hours + self.tasks +
                       self.social_level + self.stress_level + self.support_level)

        # Normalize score to a scale of 0 to 100
        max_score = 30  
        self.overall_rating = (total_score / max_score) * 100 if max_score > 0 else 0

        super().save(*args, **kwargs) 

    def __str__(self):
        return f"Feedback from {self.citizen.username} on {self.feedback_date.strftime('%Y-%m-%d')}"
    

# =============================================================================== #
#                        EMPLOYER EMPLOYMENT FEEDBACK MODEL                       #
# =============================================================================== #
# Used for the monthly feedback for employers with active employments via the portal
class EmployerFeedback(models.Model):
    # Feedback fields
    employer = models.ForeignKey(User, on_delete=models.CASCADE) 
    feedback = models.TextField(blank=True, null=True)  
    punctuality = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    attendance = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    dependability = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    work_quality = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    communication = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    attitude = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=1)
    overall_rating = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  
    feedback_date = models.DateTimeField(auto_now_add=True) 
    citizen = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='citizen'
    )

    # Calculate overall rating
    def save(self, *args, **kwargs):
        total_score = (self.punctuality + self.attendance + self.dependability +
                    self.work_quality + self.communication+ self.attitude)

        # Normalize score to a scale of 0 to 100
        max_score = 30 
        self.overall_rating = (total_score / max_score) * 100 if max_score > 0 else 0

        super().save(*args, **kwargs)  

    def __str__(self):
        return f"Feedback from {self.employer.username} on {self.feedback_date.strftime('%Y-%m-%d')}"