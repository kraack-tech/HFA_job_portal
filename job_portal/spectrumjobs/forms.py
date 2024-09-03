from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *

# =============================================================================== #
#                                  SIGNUP FORM                                    #
# =============================================================================== #
# Form for new user creation
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')


# =============================================================================== #
#                                  SIGNIN FORM                                    #
# =============================================================================== #
# Form for logins
class UserLoginForm(forms.Form):
    username = forms.CharField(label='Username')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


# =============================================================================== #
#                             ONE-TIME PASSWORD FORM                              #
# =============================================================================== #
# Form for one-time passwords
class OTPForm(forms.Form):
    otp = forms.CharField(label='OTP', max_length=6)


# =============================================================================== #
#                              USER PROFILE FORM                                  #
# =============================================================================== #
# Form for creating or updating user profile information
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['email', 'first_name','last_name', 'phone', 'address', 'city', 'postcode' ]

# =============================================================================== #
#                             CITIZEN PROFILE FORM                                #
# =============================================================================== #
# Form used for citizen experience information and work capabilities. 
class CitizenProfileForm(forms.ModelForm):
    class Meta:
        model = CitizenProfile
        fields = ['job_field', 'job_type', 'support_grants', 'education', 'employed', 'employer', 'experience']

    # Ensure only employed citizens are listed:    
    def __init__(self, *args, **kwargs):
            super(CitizenProfileForm, self).__init__(*args, **kwargs)
            self.fields['employer'].queryset = User.objects.filter(userprofile__user_type='employer')

# =============================================================================== #
#                          CONTACT PERSON PROFILE FORM                            #
# =============================================================================== #
# Not currently in use
class ContactPersonForm(forms.ModelForm):
    class Meta:
        model = CitizenProfile
        fields = ['contact_person']

# =============================================================================== #
#                         SENSORY PROFILE/TRAINING FORM                           #
# =============================================================================== #
# Form used for creating or updating citizen sensory profile values or employers sensory training level
class SensoryProfileForm(forms.ModelForm):
    class Meta:
        model = SensoryProfile
        fields = ['auditory', 'visual', 'smell', 'tactile', 'movement']

# =============================================================================== #
#                             EMPLOYER FACILITY FORM                              #
# =============================================================================== #
# Form used for creating or updating employer work-place information
class EmployerFacilitiesForm(forms.ModelForm):
    class Meta:
        model = EmployerFacilities
        fields = ['sound_level', 'team_count', 'layout', 'support_service', 'field']


# =============================================================================== #
#                                 JOB POST FORM                                   #
# =============================================================================== #
# Form used for creating or updating job posts
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'company_name', 'location', 'description', 'job_type', 'job_field', 'education']


# =============================================================================== #
#                               CALENDAR FORM                                     #
# =============================================================================== #
# Form for creating or updating calendar appointments
class CalendarForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['liaison', 'title', 'description', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        

# =============================================================================== #
#                            EMPLOYER FEEDBACK FORM                               #
# =============================================================================== #
# Form for updating monthly employment feedback for employers
class EmployerFeedbackForm(forms.ModelForm):
    citizen = forms.ModelChoiceField(
        queryset=User.objects.none(),  
        widget=forms.Select
    )
    class Meta:
        model = EmployerFeedback
        fields = [
            'citizen',
            'feedback',
            'punctuality',
            'dependability',
            'work_quality',
            'communication',
            'attitude',
        ]

        widgets = {
            'feedback': forms.Textarea(attrs={'placeholder': 'Enter your feedback here...'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(EmployerFeedbackForm, self).__init__(*args, **kwargs)
        if user:
            self.fields['citizen'].queryset = User.objects.filter(citizenprofile__employer=user)
            self.fields['citizen'].label_from_instance = lambda obj: obj.username

# =============================================================================== #
#                             CITIZEN FEEDBACK FORM                               #
# =============================================================================== #
# Form for updating monthly employment feedback for citizens
class CitizenFeedbackForm(forms.ModelForm):
    class Meta:
        model = CitizenFeedback
        fields = [
            'feedback', 
            'job_satisfaction', 
            'work_hours', 
            'tasks', 
            'social_level', 
            'stress_level',
            'support_level',
            'stress_level',
        ]
        widgets = {
            'feedback': forms.Textarea(attrs={'placeholder': 'Enter your feedback here...'}),
        }
