from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from rest_framework.parsers import JSONParser
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.middleware.csrf import rotate_token
from notifications.signals import notify
from django.db.models import Q
import pyotp
from .forms import *
from .utils import * 
from .models import *
from .serializers import *

# =============================================================================== #
#                               APPLICATION ACCESS                                #
# =============================================================================== #
# ====================================== #
#           REGISTER NEW USER            #
# ====================================== #
def signup(request):
    if request.method == 'POST':
        #user and profile forms
        signup_form = SignUpForm(request.POST)
        user_info = UserProfileForm(request.POST, request.FILES)
        if signup_form.is_valid() and user_info.is_valid():
            #save forms
            user = signup_form.save()
            profile = user_info.save(commit=False)
            profile.user = user
            profile.save()
            #redirect to signin endpoint
            return redirect('signin')
    else:
        signup_form = SignUpForm()
        user_info = UserProfileForm()

    return render(request, 'spectrumjobs/signup.html', {'signup_form': signup_form,'user_info': user_info})


# ====================================== #
#               USER LOGIN               #
# ====================================== #
def signin(request):
    # Retrieve username from request for manual logins
    user_name = request.GET.get('user_name', '')
    # Initialise 2FA flag variable
    enable_2fa = False

    if request.method == 'POST':
        # Fetch body and action parameter
        try:
            body = json.loads(request.body)
            action = body.get('action')
        except json.JSONDecodeError:
            action = None

        # Check if user is Danish and send response to template (signin.html)
        if action == 'check_user':
            username = body.get('username')
            try:
                # Retrieve user and corresponding profile
                user = User.objects.get(username=username)
                user_profile = UserProfile.objects.get(user=user)
                # Check is DK_user attribute is set to "Yes", i.e. a Danish user type
                is_dk_user = user_profile.DK_user == "yes"
            except User.DoesNotExist:
                # User does not exist in the User model
                is_dk_user = False
            except UserProfile.DoesNotExist:
                # User does not exist in the UserProfile model
                is_dk_user = False
                print("User is not danish")
            
            # Send 'is_dk_user' flag variable to template: If true, template redirects to MitID authentication process
            return JsonResponse({'is_dk_user': is_dk_user})
        
        # Login for non-Danish user types
        form = UserLoginForm(request.POST)
        if form.is_valid():
            # Retrieve User and Profile objects
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = User.objects.get(username=username)
            user_profile = UserProfile.objects.get(user=user)
            
            # Nationality check
            if user_profile.DK_user == "yes":
                # Ensures Danish users cannot bypass the MitID authentication
                return render(request, 'spectrumjobs/mitid_login.html', {'username': username})
            else:
                # Authenticate and login non-Danish users
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    # Check if user has enabled 2FA
                    if hasattr(user, 'userprofile') and user.userprofile.is_2fa_enabled:
                        # Update 2FA flag and redirect to OTP authentication process
                        enable_2fa = True
                        request.session['user_id'] = user.id
                        return redirect('verify_2fa')
                    else:
                        # Login users without 2FA enabled
                        login(request, user)
                        # Regenate session ID to enhance session security
                        rotate_token(request)
                        # Redirect successfull authentication to the index endpoint
                        return redirect('index')
    else:
        form = UserLoginForm(initial={'username': user_name})

    return render(request, 'spectrumjobs/signin.html', {'form': form, 'enable_2fa': enable_2fa})


# ====================================== #
#              USER LOGOUT               #
# ====================================== #
def signout(request):
    # Flush stored session
    request.session.flush()
    # Redirect to authentication option endpoint
    return render(request, 'spectrumjobs/authentication.html')


# =============================================================================== #
#                                    DASHBOARDS                                   #
# =============================================================================== #
@login_required(login_url='authentication')  # Redirect unauthorized users to authentication options
def index(request):
    contact = None # Initalize contact flag variable as None
    employer_profile = None
    # Get inbox messages 
    messages = Message.objects.filter(recipient=request.user).order_by('-timestamp')[:10]

    # Count unread notifications for bell icon in navbar
    notifications_count = Notification.objects.filter(recipient=request.user, unread=True).count()

    # Dashboard for citizens
    if request.user.userprofile.user_type == "citizen":
        # Get assigned contact person from the profile
        contact = request.user.userprofile.contact_person 

        # Retrieve best job matches
        jobs = Job.objects.all()
        job_matches = get_matches(jobs, request.user, request.user.userprofile.user_type)
        job_matches.sort(key=lambda x: x['overall_match_score'], reverse=True)
        
        # Render citizen dashboard
        return render(request, 'spectrumjobs/index.html', {
                'user_profile':request.user.userprofile, 
                'messages': messages,
                'unread_notifications': notifications_count,
                'job_matches': job_matches[:4],
                'selected_citizen': request.user,
                'user_type': request.user.userprofile.user_type,
                'contact': contact
            })
    
        # Dashboard for employers
    elif request.user.userprofile.user_type == "employer":
        jobs = Job.objects.filter(employer=request.user) # Jobs posted by employer
        selected_job_id = request.GET.get('job_posting') # Selected job from dropdown menu

        # If a job is selected from dropdown menu on page (match_employer.html)
        if selected_job_id:
            try:
                # Retrieve jobs from Job model by id
                selected_job_id = int(selected_job_id)
                selected_job = Job.objects.get(id=selected_job_id)
            except (ValueError, Job.DoesNotExist):
                selected_job = None
        else:
            selected_job = None

        # Iterate over job posts by employer and retrieve best candidate matches for the applicants
        job_matches = []
        for job in jobs:
            # Try to retrieve sensory training profile of employer logged in
            try:
                employer_profile = SensoryProfile.objects.filter(user=request.user).first()
            except SensoryProfile.DoesNotExist:
                employer_profile = None

            # If a sensory training profile exist for the employer: Get best candidates for job posts
            if employer_profile:
                # Calculate candidate against job posts
                matches = get_matches(job, employer_profile, request.user.userprofile.user_type)

                # Only display candidates who  have applied for the job
                job_applicants = [match for match in matches if match['citizen'] in job.applicants.all()]

                # Append to list
                job_matches.append({
                    'job': job,
                    'top_matches': job_applicants[:10],
                    'selected_job_id': selected_job_id,
                    'selected_employer': request.user
                })

        # Render employer dashboard
        return render(request, 'spectrumjobs/index.html', {
            'user_profile': request.user.userprofile,
            'messages': messages,
            'unread_notifications': notifications_count,
            'job_matches': job_matches[:4],
            'selected_job_id': selected_job_id,
            'selected_job': selected_job,
            'selected_employer': request.user,
            'user_type': request.user.userprofile.user_type,
            "employer_profile":employer_profile
        })
    
        # Dashboard for contact persons
    elif request.user.userprofile.user_type == "liaison":
        citizens = CitizenProfile.objects.filter(contact_person=request.user) # Retrive all appointed citizens
        citizen_data = [] # Initialise citizen list 

        # Support needs dictionary 
        support_dict = {
            "Urgent": 0,
            "High": 1,
            "Neutral": 2,
            "Low": 3,
            "None": 4
        }
        # Support needs rating list (indexed by calculated ranges)
        rating = [
            "Urgent",  # 0-19
            "High",    # 20-39
            "Neutral", # 40-59
            "Low",     # 60-79
            "None"     # 80-100
        ]

        # Iterate over all appointed citizens to identify current support needs
        for citizen in citizens:
            user_id = citizen.user.id # Citizen id
            status = "Employed" if citizen.employed else "Not Employed" # Employment status

            # Feedback objects 
            citizen_feedback = CitizenFeedback.objects.filter(citizen=citizen.user).first() # Citizen feedback object
            employer_feedback = EmployerFeedback.objects.filter(citizen=citizen.user).first() # employer feedback object
            
            # Citizen current month overall feedback rating
            if citizen_feedback:
                citizen_feedback_rating = citizen_feedback.overall_rating
            else: 
                citizen_feedback_rating = 0
            
            # Employer current month overall feedback rating
            if employer_feedback:
                employer_feedback_rating = employer_feedback.overall_rating
            else: 
                employer_feedback_rating = 0 

            # Calculate the current support need for the citizen
            if citizen_feedback_rating and employer_feedback_rating:
                support_need = int((citizen_feedback_rating + employer_feedback_rating) / 2) # Support need score
                support_need = rating[min(support_need // 20, 4)] # Determine support needs based on the index of the rating list

            else:
                # If no feedback is available, the support need is set to urgent: Also set to urgent if citizen is not employed as employment status relies on the feedback models
                support_need = "Urgent"

            # Append results to citizen_data list
            citizen_data.append({
                'user': citizen.user.username,
                'user_id':user_id,
                'employed': status,
                'progress_1': citizen_feedback_rating,
                'progress_2': employer_feedback_rating,
                'results_3': support_need,
                'priority': support_dict.get(support_need, 5)
            })

        citizen_data = sorted(citizen_data, key=lambda x: x['priority']) # Sort list based on the priority dictionary

        # Render copntact person dashboard
        return render(request, 'spectrumjobs/monitor.html', {
            'user_profile':request.user.userprofile, 
            'user_type':request.user.userprofile.user_type,  
            'citizens': citizens,  
            'citizen_data': citizen_data,        
            'messages': messages,
            'unread_notifications': notifications_count, 
        })

    # Redirect users without a profile type assigned yet
    else:
        return render(request, 'spectrumjobs/index.html', {
            #'user_profile':request.user.userprofile, 
            'user_type':request.user.userprofile.user_type,  
            'messages': messages,
            'unread_notifications': notifications_count, 
        })

# Render monitor template for liaisons
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
@liaison_only
def monitor(request):
    return render(request, 'spectrumjobs/monitor.html', {'user':request.user.userprofile})



# =============================================================================== #
#                 CITIZEN/EMPLOYER SENSORY/FACILITY INFORMATION                   #
# =============================================================================== #
# ====================================== #
#         PERSONAL INFORMATION           #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def profile_info(request):
    # Render profile information endpoint
    return render(request, 'spectrumjobs/profile_info.html', {'user_profile': request.user.userprofile})


# ====================================== #
#        CITIZEN/EMPLOYER PROFILE        #
#    Individual monitoring for liaisons  #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
@liaison_only
def profile_data(request, user_id):
    # Initialize forms
    sensory_form = SensoryProfileForm(request.POST or None)
    citizen_form = CitizenProfileForm(request.POST or None)
    employer_form = EmployerFacilitiesForm(request.POST or None)

    # Control variables: check usage=?
    visited_app_user_user_type = False
    jobs = None
    support_level = None
    job_type_recommendation = None
    job_arr = None
    job_matches = None 
    support_level = None
    job_type_recommendation = None
    assigned = None 
    # Retrieve user and profile objects
    try:
        visited_user = User.objects.get(id=user_id) # user from User model by id from the request 
        try:
            visited_app_user = UserProfile.objects.get(user=visited_user) # profile from UserProfile model by User object 
            job_arr = [] # List for best job matches for citizens 
            training_recommendations = [] # List for best job matches for employers
            support_recommendation = False # Support recommendation variable
            visited_app_user_user_type = visited_app_user.user_type

            # The visited profile is an employer
            if visited_app_user.user_type == "employer":
                # Retrive all active job posts by the employer and append to job_arr list
                jobs = Job.objects.filter(employer=visited_user)
                for job in jobs:
                    job_arr.append({
                        'job': job,
                        'job_id': job.id,
                        'job_title':job.title,
                        'job_type':job.job_type,
                        'job_field':job.job_field,
                        'job_location':job.location,
                        'job_date':job.posted_date,
                        'job_education':job.education,
                    })

                # Provide training and supportive service recommendation
                employer_sense = SensoryProfile.objects.filter(user=visited_user).first() # Sensory training of the employer
                employer_profile = EmployerFacilities.objects.filter(employer=visited_user).first() # Employer facilities

                if employer_profile and employer_sense:  # Ensure employer has both sensory and facility evaluations conducted
                    # Retrieve sensory profiles for citizens in the same field/domain
                    sensory_profiles = SensoryProfile.objects.filter(user__citizenprofile__job_field=employer_profile.field)
                    # If we have citizens in the same field: use their sensory profile scores against employers to provide recommendations
                    if sensory_profiles.exists(): 
                        # Dictionary for storing the sum of sensory values of citizens in same field 
                        sensory_totals = {
                            'auditory': 0,
                            'visual': 0,
                            'smell': 0,
                            'tactile': 0,
                            'movement': 0,
                        }

                        # Sum of sensory scores for all citizens
                        for profile in sensory_profiles:
                            sensory_totals['auditory'] += profile.auditory
                            sensory_totals['visual'] += profile.visual
                            sensory_totals['smell'] += profile.smell
                            sensory_totals['tactile'] += profile.tactile
                            sensory_totals['movement'] += profile.movement
                        
                        # Calculate average sensory scores
                        sensory_averages = {key: value / sensory_profiles.count() for key, value in sensory_totals.items()}
                        total_average_sum = sum(sensory_averages.values())

                        # Compare with employer's sensory profile
                        comparison_results = {}
                        for key, avg_value in sensory_averages.items():
                            employer_value = getattr(employer_sense, key)
                            comparison_results[key] = {
                                'average_citizen_value': avg_value,
                                'employer_value': employer_value,
                                'difference': employer_value - avg_value
                            }
                        
                        # Provide recommendation based on the comparison results
                        for sense, values in comparison_results.items():
                            # Sensory training and facility recommendations
                            if values['difference'] < -1.5:
                                training_recommendations.append(sense.capitalize())

                            # Supportive service recommendation
                            if total_average_sum < 3:
                                support_recommendation = True
                    else: 
                        # No citizens in the same field
                        training_recommendations = None
                        support_recommendation = None
            
            # The visited profile is a citizen
            elif visited_app_user.user_type == "citizen":
                # Calculate best job matches for the visited citizen
                jobs = Job.objects.all() # Get all jobs
                job_matches = get_matches(jobs, visited_user, request.user.userprofile.user_type) # calculate best matches
                #job_matches.sort(key=lambda x: x['top_matches'][0]['overall_match_score'], reverse=True) # Sort based on overall score
                job_matches.sort(key=lambda x: x['overall_match_score'], reverse=True)

                # Retrieve job-type and support level recommendation
                if job_matches:
                    first_match = job_matches[0]
                    support_level = first_match.get('support_score', 'NA')  # Support level recommendation
                    job_type_recommendation = first_match.get('job_type_recommendation', 'N/A')  # Job-type level recommendation

        except UserProfile.DoesNotExist:
            # Profile does not exist
            jobs = "None"
    except User.DoesNotExist:
        # Redirect back to monitoring page if user does not exist
        return redirect('index')

    # Retrive sensory profile of visited user for citizens and employers
    try:
        senseProfile = SensoryProfile.objects.get(user=visited_user)
    except SensoryProfile.DoesNotExist:
        senseProfile = None

    # Retrive citizen profile of visited user
    try:
        citizen_profile = CitizenProfile.objects.get(user=visited_user)
        contact_person = citizen_profile.contact_person
        employer = citizen_profile.employer
        # Check is citizens has an assigned contact person
        if str(request.user.userprofile) == str(contact_person):
            assigned = True
    except CitizenProfile.DoesNotExist:
        citizen_profile = None
        contact_person = None
        employer = None
        assigned = False

    # Retrive employer facility profile of visited user
    try:
        employer_profile = EmployerFacilities.objects.get(employer=visited_user)
    except EmployerFacilities.DoesNotExist:
        employer_profile = None
    
    # POST request for updating profile or sensory scores
    if request.method == 'POST':
        # Handle sensory profile updates
        if 'sensory_profile' in request.POST:
            print('sensory_profile')  # Debugging
            if senseProfile:
                sensory_form = SensoryProfileForm(request.POST, instance=senseProfile) # SensoryProfileForm of forms.py
            else:
                sensory_form = SensoryProfileForm(request.POST)
            # Check if inputs are valid and save
            if sensory_form.is_valid():
                sensory_profile = sensory_form.save(commit=False)
                sensory_profile.user = visited_user
                sensory_profile.save()
                return redirect('profile_data', user_id=user_id)
            
        # Handle employer facility profile updates
        elif 'employer_profile' in request.POST:
            print('employer_profile')  # Debugging
            employer_form = EmployerFacilitiesForm(request.POST, instance=employer_profile) # EmployerFacilitiesForm of forms.py
            # Check if inputs are valid and save
            if employer_form.is_valid():
                employer_profile = employer_form.save(commit=False)
                employer_profile.employer = visited_user
                employer_profile.save()
                return redirect('profile_data', user_id=user_id)
            
        # Handle citizen profile updates    
        elif 'citizen_profile' in request.POST:
            print('citizen_profile')  # Debugging

            citizen_form = CitizenProfileForm(request.POST, instance=citizen_profile) # CitizenProfileForm of forms.py
            # Check if inputs are valid and save
            if citizen_form.is_valid():
                citizen_profile = citizen_form.save(commit=False)
                citizen_profile.user = visited_user
                citizen_profile.save()
                return redirect('profile_data', user_id=user_id)
            
        # Handle contact person assign request
        elif 'contact_form' in request.POST:

            print('contact_form')  # Debugging
            # Assign user as contact person and save 
            if request.user.userprofile.user_type == 'liaison':
                contact = request.user
                citizen_profile.contact_person = contact  
                citizen_profile.save() 
                return redirect('profile_data', user_id=user_id)
            
        # Handle user type assigning requests
        elif 'user-type-form' in request.POST:
            # Get current user type from request
            selected_user_type = request.POST.get('user_type')
            # Update user type and save to UserProfile object
            if selected_user_type:
                visited_app_user.user_type = selected_user_type
                visited_app_user.save()

                # Reload user profile apge
                return redirect('profile_data', user_id=user_id)

                    
    # Load forms with current values
    else:
        sensory_form = SensoryProfileForm(instance=senseProfile)
        citizen_form = CitizenProfileForm(instance=citizen_profile)
        employer_form = EmployerFacilitiesForm(instance=employer_profile)

    #print('visited_user',visited_user.username)
    #print('visited_app_user',visited_app_user)
    #print('visited_app_user user_type',visited_app_user.user_type)


    # Render individual user monitoring endpoint
    return render(request, 'spectrumjobs/profile_data.html', {
        'visited_user': visited_user,
        'visited_app_user':visited_app_user,
        'sensory_form': sensory_form,
        'visited_app_user_user_type':visited_app_user_user_type,
        'senseProfile':senseProfile,
        'citizen_profile': citizen_profile,
        "citizen_form":citizen_form,
        "employer_profile":employer_profile,
        'employer_form':employer_form,
        'contact_person':contact_person,
        'employer':employer,
        'assigned':assigned,
        'job_matches': job_matches,
        "jobs":jobs,
        "job_arr":job_arr,
        'support_level':support_level,
        'job_type_recommendation':job_type_recommendation,
        'training_recommendations':training_recommendations,
        'support_recommendation':support_recommendation,
        'user_type': [field[0] for field in UserProfile.USER_TYPES]
    })


# =============================================================================== #
#                                     JOBS                                        #
# =============================================================================== #
# ====================================== #
#                 PORTAL                 #
# ====================================== #
def portal(request):
    # Retrieve user profile: Ensure guests can also access the job post portal
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user) # Profile object
        user_type = request.user.userprofile.user_type
    else: 
        # Guest user: Also allow access 
        user_profile =  None
        user_type = "guest",
    
    # Initialise suggestion and form variables
    best_match_sort = None # Variable used for best job suggestion sort option
    form = None # Job post form (Only initialised for employers)

    # Job posts search queries and sort variables retrieved from request
    query_title = request.GET.get('title_description') # Title and description search field
    query_location = request.GET.get('location') # Location search field
    query_field = request.GET.get('job_field') # Job field option
    query_type = request.GET.get('job_type')  # Job type option
    query_education = request.GET.get('education_level')  # Minimum education level option
    sort_by = request.GET.get('sort_by')  # Selected sort option by user

    # Retrive relevant job posts from Job model db based on the user type: allow access for unauthorised user
    if request.user.is_authenticated:
        if request.user.is_authenticated and request.user.userprofile.user_type == "citizen" or request.user.userprofile.user_type == "liaison":
            jobs = Job.objects.all()  # Fetch all jobs for display
        elif request.user.userprofile.user_type == "employer":
            try:
                jobs = Job.objects.filter(employer=request.user)  # Fetch all jobs by employer
            except Job.DoesNotExist:
                jobs = Job.objects.all()
        else: 
            jobs = Job.objects.all()
    else:
        jobs = Job.objects.all()

    # Queries retrieved from request
    # Title and description query filter
    if query_title: 
        jobs = jobs.filter(Q(title__icontains=query_title) | Q(description__icontains=query_title))
    # Location query filter
    if query_location: 
        jobs = jobs.filter(location__icontains=query_location)
    # Field query filter
    if query_field: 
        jobs = jobs.filter(job_field=query_field)
    # Type query filter
    if query_type: 
        jobs = jobs.filter(job_type=query_type)
    # Education level query filter
    if query_education: 
        jobs = jobs.filter(education=query_education)

    # Get best job matches and sort for citizen users
    if request.user.is_authenticated:
        if request.user.userprofile.user_type == "citizen":
            selected_citizen = request.user 
            best_match_sort = get_matches(jobs, selected_citizen, request.user.userprofile.user_type)
            # Create a mapping of job ids to their scores
            job_scores = {match['job'].id: match['overall_match_score'] for match in best_match_sort if match['overall_match_score']}
            # Sort using the sort_jobs utility function
            jobs_sorted = sort_jobs(jobs, sort_by, user_type, job_scores)

        # Get all jobs by the employer
        elif request.user.userprofile.user_type == "employer":
            # Post new job form
            form = JobForm()
            if request.method == 'POST':
                form = JobForm(request.POST)
                if form.is_valid():
                    form.save()
                    return redirect('portal') 
                
            # Sort using the sort_jobs utility function
            jobs_sorted = sort_jobs(jobs, sort_by, request.user.userprofile.user_type, None)
            jobs = [] # List of sorted jobs
            # Append jobs to sorted list
            for job in jobs_sorted:
                jobs.append({
                    'id': job.id,
                    'title': job.title,
                    'job': jobs,
                    'job_title':job.title,
                    'company_name': job.company_name,
                    'location': job.location,
                    'job_type':job.job_type,
                    'job_field':job.job_field,
                    'job_location':job.location,
                    'posted_date': job.posted_date,
                    'education': job.education,
                })
        else: 
            # Guest visitors sorted using the sort_jobs utility function
            jobs_sorted = sort_jobs(jobs, sort_by, request.user.userprofile.user_type, None)
    else:
        jobs_sorted = sort_jobs(jobs, sort_by, user_type, None)

    # Define context variables and render job portal
    context = {
        'jobs': jobs_sorted,
        'form': form,
        'user_profile':user_profile, 
        'user_type':user_type,
        'job_fields': [field[0] for field in Job.JOB_FIELDS],
        'job_types': [type[0] for type in Job.JOB_TYPES], 
        'education_levels': [level[0] for level in Job.EDUCATION], 
        'job_matches':best_match_sort,
    }
    return render(request, 'spectrumjobs/job_portal.html', context)


# ====================================== #
#             JOB POST DETAILS           #
# ====================================== #
def job_details(request, job_id):
    # Retrieve job by ID for job details
    job = get_object_or_404(Job, pk=job_id)
    return render(request, 'spectrumjobs/job_details.html', {'job': job})


# ====================================== #
#                POST JOB                #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if user is not logged in
def post_job(request):
    # Handle job post request: Only available for employers
    if request.user.userprofile.user_type == "employer":
        if request.method == 'POST':
            form = JobForm(request.POST) # Job form of forms.py
            # Check if the form is valid
            if form.is_valid():
                job = form.save(commit=False)
                job.employer = request.user   # Set employer to job post creator
                job.save()
                return redirect('portal')  # Redirect to the portal
        else:
            form = JobForm()
    else: 
        return redirect('portal') 

    return render(request, 'spectrumjobs/post_job.html', {'form': form})

# ====================================== #
#               DELETE JOB               #
# ====================================== #
def delete_job(request, job_id):
    # Only allow employers (own job posts) and contact persons (all job posts) to delete jobs
    if request.user.userprofile.user_type == "employer" or "liaison":
        job = get_object_or_404(Job, id=job_id) # Get job by ID 
        job.delete()
    else:
        redirect('portal')
    return redirect('portal')

# ====================================== #
#                APPLY JOB               #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if user is not logged in
def apply_job_view(request, job_id):
    # Job application request: Only possible for citizen user types
    if request.user.userprofile.user_type == "citizen":
        job = get_object_or_404(Job, pk=job_id) # Get job by ID
        
        if request.method == 'POST':
            # Add the citizen to the Job models applicants field
            job.applicants.add(request.user)
            job.save()
            return redirect('portal')  # Redirect back to the job portal
    else: 
        return redirect('portal')
    return redirect('portal') 



# =============================================================================== #
#                                     SUGGESTIONS                                 #
#      Matching and recommendations based of citizen and employer statistics      #
# =============================================================================== #
# ====================================== #
#               GET MATCHES              #
# ====================================== #
# Function in charge of identifying and calling calculation functions to get matches and recommendations
# Return list of ranked matches and recommendations for all user types
def get_matches(jobs, user, user_type):
    # Defined iterator based on the input user type
    # Set iterator to jobs for citizens and contact persons
    if user_type == "citizen" or user_type == "liaison":
        sense_profile = SensoryProfile.objects.filter(user=user).first()
        x = jobs
    # Set iterator to sensory profiles for employers   
    elif user_type == "employer":
        sense_profile = SensoryProfile.objects.exclude(user=jobs.employer)
        x = sense_profile
    else: 
        sense_profile = None

    # Initialise lists for matches
    match_score_lst = [] # List for matching scores, e.g. match citizen sensory profile against employer sensory triaining and other recommendations
    matches_lst = [] # List for appending the results

    # If input user has a sensory profile, we start calculating matches
    if sense_profile != None:
        # Loop for iterating over the defined iterator x based on the input user type (sensory profile for employers and jobs for citizens and contact persons)
        for i in x:
            # Initial score variables
            job_type_match = 1
            job_field_match = 1
            job_education_match = 1
            support_grants = 0
            facility_noise = 0
            facility_team = 0
            facility_layout = 0
            facility_support = 0

            # Retrive and match citizen sensory profile against employers training skills
            if user_type == "citizen" or user_type == "liaison":
                try:
                    employer_profile = SensoryProfile.objects.get(user=i.employer) # Get sensory profile of input citizen
                except SensoryProfile.DoesNotExist:
                    employer_profile = None
                if employer_profile:
                    auditory_score = calculate_sensory_match(employer_profile.auditory, sense_profile.auditory, 5) # Auditory score of sensory profile of input citizen
                    visual_score = calculate_sensory_match(employer_profile.visual, sense_profile.visual, 5) # Visual score of sensory profile of input citizen
                    smell_score = calculate_sensory_match(employer_profile.smell, sense_profile.smell, 5) # Smell score of sensory profile of input citizen
                    tactile_score = calculate_sensory_match(employer_profile.tactile, sense_profile.tactile, 5) # Tactile score of sensory profile of input citizen
                    movement_score = calculate_sensory_match(employer_profile.movement, sense_profile.movement, 5) # Movement score of sensory profile of input citizen
                    citizen = sense_profile.user # Citizen sensory profile
                    employer = i.employer # Employer of current job
                    job_field = i.job_field # Job field of current job
                    job_type = i.job_type # Job type of current job
                    education = i.education # Min. required educational level of current job

            # Match employer training against citizen sensory profiles
            elif user_type == "employer":
                auditory_score = calculate_sensory_match(user.auditory, i.auditory, 5) # Auditory score of sensory profile of input citizen
                visual_score = calculate_sensory_match(user.visual, i.visual, 5) # Visual score of sensory profile of input citizen
                smell_score = calculate_sensory_match(user.smell, i.smell, 5) # Smell score of sensory profile of input citizen
                tactile_score = calculate_sensory_match(user.tactile, i.tactile, 5) # Tactile score of sensory profile of input citizen
                movement_score = calculate_sensory_match(user.movement, i.movement, 5) # Movement score of sensory profile of input citizen
                citizen = i.user # Citizen from corresponding sensory profile
                citizen_id = i.user_id # Citizen sensory profile ID 
                employer = jobs.employer # Employer retrieved from the input jobs
                job_field = jobs.job_field # Job field retrieved from the input jobs
                job_type = jobs.job_type # Job type retrieved from the input jobs
                education = jobs.education # Min. required educational level retrieved from the input jobs
                applicants = Job.objects.filter(applicants=citizen) # Check to see if the current iterated citizen has applied for a job posts by input employer
            
            # Match citizen profiles against employer facilities
            try:
                # Try to retrieve citizen profile from CitizenProfile model using citizen variable specified based on the input user type above
                citizen_profile_obj = CitizenProfile.objects.get(user=citizen) # Citizen object
                support_grants = citizen_profile_obj.support_grants # Support grants determined for the citizen retriev from 'support_grants' field of CitizenProfile
                experience = citizen_profile_obj.experience # Years of experience of citizen retriev from 'experience' field of CitizenProfile
                education_level = citizen_profile_obj.education # Educational level for citizen retriev from 'education' field of CitizenProfile
                
                # Match field, job.type, and educational level of the citizen against the job
                if citizen_profile_obj.job_field == job_field:
                    job_field_match = 100

                if citizen_profile_obj.job_type == job_type:
                    job_type_match = 100

                if citizen_profile_obj.education == education:
                    job_education_match = 100
                    

                # Try to retrieve employer facility from EmployerFacilities model
                try:
                    employer_facility = EmployerFacilities.objects.get(employer=employer) # Facility information of the input employer
                    facility_noise = employer_facility.sound_level # Noise level for input employer
                    facility_team = employer_facility.team_count # Team size level of input employer facility
                    facility_layout = employer_facility.layout # Office-plan layout of input employer facility
                    facility_support = employer_facility.support_service # Support services options of the input employer
                except EmployerFacilities.DoesNotExist:
                    employer_facility = None
            except CitizenProfile.DoesNotExist:
                citizen_profile_obj = None
                employer_facility = None

            # Calculate average sensory score with the matching scores retrieve using the calculate_sensory_match function as inputs
            sense_score = calculate_sense_avg(auditory_score, visual_score, smell_score, tactile_score, movement_score) # Using the calculate_sense_avg function 
            
            #print("citizen:",i.title, ":", job_education_match)
            # Match citizens field, job-type, and eduction against the job post requirements
            candidate_score = calculate_candidate_match(job_field_match, job_type_match, job_education_match) # Using the calculate_candidate_match function 
            #print("candidate_score:",i.title, ":", candidate_score)
            # Match employer facility against support needs and relevant sensory scores of citizens
            if user_type == "employer":
                # Facility match score
                facility_score = calculate_facility_match(facility_team, facility_layout, facility_support, i.auditory, 
                                    i.tactile, i.visual, support_grants)
            elif user_type == "citizen" or user_type == "liaison":
                # Facility match score
                facility_score = calculate_facility_match(facility_team, facility_layout, facility_support, sense_profile.auditory, 
                                                        sense_profile.tactile, sense_profile.visual, support_grants)
                # Get citizens support and job-type recommendation
                support_score = calculate_support_needs(auditory_score, visual_score, smell_score, tactile_score, movement_score, experience,education_level)
                job_type_recommendation = calculate_job_type_recommendation(support_score)

            # Calculate overall matching score
            overall_match_score = round((sense_score + candidate_score + facility_score) / 3, 2)

            # Append scores and sort for citizens and contact persons
            if user_type == "citizen" or user_type == "liaison":
                # Append scores and recommendations
                matches_lst.append({
                    'job': i,
                    'employer' : i.employer,
                    'title' : i.title,
                    'job_field' : i.job_field,
                    'job_type' : i.job_type,
                    'education' : i.education,
                    'location': i.location,
                    'employer_profile': employer_profile,
                    'auditory_score': auditory_score,
                    'visual_score': visual_score,
                    'smell_score': smell_score,
                    'tactile_score': tactile_score,
                    'sense_score':sense_score,
                    'candidate_score':candidate_score,
                    'facility_score':facility_score,
                    'movement_score': movement_score,
                    'overall_match_score': overall_match_score,
                    'support_score':support_score,
                    "job_type_recommendation": job_type_recommendation,
                    'job_field_match': job_field_match,
                    'job_type_match': job_type_match,
                    'job_education_match': job_education_match,
                    'citizen_profile': sense_profile,
                    'job_field': job_field,
                    'job_type': job_type,
                    'education':education,
                })

                # # Sort matches (descending order)
                # match_score_lst.sort(key=lambda x: x['overall_match_score'], reverse=True)

                # # Append to matches list
                # matches_lst.append({
                #     'job': i,
                #     'top_matches': match_score_lst[:6],  # Top 6 job matches 
                # })
            
            # Append scores and sort for citizens and contact persons
            elif user_type == "employer":
                # Append and applicants 
                matches_lst.append({
                    'citizen_profile': x,
                    'employer_profile': user,
                    'match_score': sense_score,
                    'auditory_score': auditory_score,
                    'visual_score': visual_score,
                    'smell_score': smell_score,
                    'tactile_score': tactile_score,
                    'movement_score': movement_score,
                    'overall_match_score': overall_match_score,
                    'job_field_match': job_field_match,
                    'job_type_match': job_type_match,
                    'job_education_match': job_education_match,
                    'citizen': citizen,
                    'citizen_id':citizen_id,
                    'job_field': jobs.job_field,
                    'job_type': jobs.job_type,
                    'applicants': [applicant for applicant in applicants] # Only show citizens that have applied for the job
                })

                # Sort matches (descending order)
                matches_lst.sort(key=lambda x: x['overall_match_score'], reverse=True)
    else: 
        # Handle errors
        print("No sensory profile")

    return matches_lst


# ====================================== #
#     MATCH SENSORY PROFILE/TRAINING     #
# ====================================== #
# Mathces the employer training against citizens sensory profile values
def calculate_sensory_match(employer_value, citizen_value, divisor):
    difference = employer_value - citizen_value # Difference in citizen sensory value and employer training value

    # If employer has higher training value: Return 100 as the employer training level is capable to cope with the sensory score of the citizen
    if employer_value > citizen_value:
        return 100.0 

    # Normalize to a scale of 0-100 and rounded to two decimal places
    score_normalized_rounded = round(max(1 - (abs(difference) / divisor), 0) * 100)  # Use abs(difference) for normalization

    # Return float of normalized and rounded score
    return float(score_normalized_rounded)  


# ====================================== #
#     AVERAGE SENSORY PROFILE/TRAINING   #
# ====================================== #
# Calculates average sensory (citizen and contact persons) or training score (employers)
def calculate_sense_avg(auditory_score, visual_score, smell_score, tactile_score, movement_score):
    # List with sensory values
    scores = [auditory_score, visual_score, smell_score, tactile_score, movement_score]

    # Calculate average of list 
    sens_score = sum(scores) / len(scores)

    # Return average as float
    return float(sens_score)


# ====================================== #
#             CANDIDATE MATCH            #
# ====================================== #
# Matches citizens against job requirements
def calculate_candidate_match(field, type, education):

    # Dictionary with defined weights, i.e. importance of the attributes
    job_requirement_weights = {
        'field': 0.5,
        'type': 1.5,
        'education': 1
    }
    # print ('field:',field )
     #print ('type:',type )
     #print ('education:',education )
    # Calculate requirements score using defined weights
    score = (job_requirement_weights['field'] * field + job_requirement_weights['type'] * type + job_requirement_weights['education'] * education) / 3
    # print ('score:',score )

    # Return candicate match score
    return score


# ====================================== #
#              FACILITY MATCH            #
# ====================================== #
# Matches citizens profiles against the employers facility and supportive services
def calculate_facility_match(facility_team, facility_layout, facility_support, auditory, tactile, visual, support_grants):

    # Obtain the support string value based on the grants allocated for the input citizen
    if isinstance(support_grants, str):
        # Convert the grants string input to integeer
        grants_str = support_grants[:-1]    
        grants_int = int(grants_str)

        # Specify support value based on the support needs of the citizens and if employer offers supportive services
        if grants_int > 0 and grants_int <= 30:
            if facility_support == True:
                support = 100
            else:
                support = 60
        elif grants_int >= 40 and grants_int <= 60:
            if facility_support == True:
                support = 100
            else:
                support = 40
        elif grants_int >= 70:
            if facility_support == True:
                support = 100
            else:
                support = 1
        else: 
            support = -1
    else: 
        support = 100

    # Define the social load level based on the citizens auditory/tactile scores and the no. of team members of the job post
    if auditory+tactile >= 5:
        if facility_team <= 5:
            social_load = 100
        elif facility_team <= 10:
            social_load = 75
        elif facility_team <= 15:
            social_load = 55
        elif facility_team <= 20:
            social_load = 30
        else: 
            social_load = 1
    else: 
        social_load = 100

    # Define the layout score by matching auditory/tactile scores of the citizen against the employers work-plan design choice (i.e. the room/office layout)
    if auditory+visual >= 5:
        if facility_layout == 'individual':
            layout = 100
        elif facility_layout == 'team-based' and facility_team <= 5 :
            layout = 90
        elif facility_layout == 'team-based' and facility_team < 10 and facility_team > 5:
            layout = 80
        elif facility_layout == 'team-based' and facility_team < 20 and facility_team > 10:
            layout = 65
        elif facility_layout == 'team-based' and facility_team > 20:
            layout = 10
        elif facility_layout == 'cubicle':
            layout = 60
        elif facility_layout == 'traditional':
            layout = 45
        elif facility_layout == 'abw':
            layout = 1
        elif facility_layout == 'hot desking':
            layout = 1
        elif facility_layout == 'open plan':
            layout = 1
        else: 
            layout = 1
    else: 
        layout = 100

    # Dictionary with defined weights, i.e. importance of the attributes
    req_weights = {
        'support': 1,
        'social_load': 1,
        'layout': 1
    }
    
    # Calculate facility score using the support, social_load, and layout values and weights defined
    score = round((req_weights['support'] * support + req_weights['social_load'] * social_load + req_weights['layout'] * layout) / 3,4)
    
    # Return result
    return score

# ====================================== #
#         JOB-TYPE RECOMMENDATION        #
# ====================================== #
# Simple function for defining a job-type recommendation for an citizen
def calculate_job_type_recommendation(support_score):
    if support_score > 90:
        recommendation = "temporary"
    elif support_score >= 80 and support_score < 90:
        recommendation = "internship"
    elif support_score >= 70 and support_score < 80:
        recommendation = "contract"
    elif support_score >= 60 and support_score > 40:
        recommendation = "part-time"
    else: 
        recommendation = "full-time"

    # Return the recommendation
    return recommendation


# ====================================== #
#       SUPPORT LEVEL RECOMMENDATION     #
# ====================================== #
# Function that calculates the level of support recommendation for a citizen 
def calculate_support_needs(auditory_score, visual_score, smell_score, tactile_score, movement_score, experience, education_level):
    # Dictionary with eduction mapping
    education_rating = {
        "none": 0,  
        "primary": 1,
        "lower secondary": 2,
        "upper secondary": 3,
        "other": 4,
        "short tertiary": 5,
        "bachelor": 6,  
        "master": 7,
        "phd": 8,
        "doctoral": 8,
    }

    # Map the educational level against the dictionary
    educational_score = education_rating.get(education_level)
    
    # Calculate sensory score
    sens_score = sum([auditory_score, visual_score, smell_score, tactile_score, movement_score]) / 5

    # Decide the support level recomendation based on the educational level, experience, and the average sensory profile score
    if sens_score > 4:
        if educational_score < 2:
            suport_needs =  100 - min(experience * 20, 80)
        elif educational_score < 5:
            suport_needs = 70 - min(experience * 10, 60)
        else:
            suport_needs = 50 - min(experience * 10, 40)
    elif sens_score > 3:
        if educational_score < 2:
            suport_needs = 90 - min(experience * 20, 80)
        elif educational_score < 5:
            suport_needs = 60 - min(experience * 10, 50)
        else:
            suport_needs = 40 - min(experience * 10, 30)
    elif sens_score > 2:
        if educational_score < 2:
            suport_needs = 80 - min(experience * 20, 60)
        elif educational_score < 5:
            suport_needs = 50 - min(experience * 10, 40)
        else:
            suport_needs = 30 - min(experience * 10, 20)
    else:
        if educational_score < 2:
            suport_needs = 60 - min(experience * 20, 40)
        elif educational_score < 5:
            suport_needs = 30 - min(experience * 10, 20)
        else:
            suport_needs = 10 - min(experience * 10, 10)

    # Return the derived support need for the citizen
    return suport_needs


# =============================================================================== #
#                                     CALENDAR                                    #
# =============================================================================== #
# References:
# https://fullcalendar.io/docs
# https://medium.com/@azzouzhamza13/django-fullcalendar6-1-11-rrule-8a4e63100d0b
# ====================================== #
#       GET CALENDAR APPPOINTMENTS       #
# ====================================== #
# Get all calendar appointments for citizens and contact persons user types
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def get_appointments(request):
    # Get appointments: Accesible for both the citizen and appointment creator (contact person) 
    appointments = Calendar.objects.filter(Q(user=request.user) | Q(liaison=request.user)) 
    serializer = CalendarSerializer(appointments, many=True)
    return JsonResponse(serializer.data, safe=False)


# ====================================== #
#       ADD CALENDAR APPPOINTMENTS       #
# ====================================== #
@csrf_exempt
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def add_appointment(request):
    if request.method == 'POST':
        data = json.loads(request.body) # Get appointment data from request

        # Serializer instance with request context
        serializer = CalendarSerializer(data=data, context={'request': request})
        
        # Validate serializer and save appointment
        if serializer.is_valid():
            appointment = serializer.save()
            return JsonResponse({'status': 'success', 'appointment_id': appointment.id})
        
        # Return validation errors
        return JsonResponse({'error': serializer.errors}, status=400)  


# ====================================== #
#      UPDATE CALENDAR APPPOINTMENTS     #
# ====================================== #
@csrf_exempt
@login_required(login_url='authentication')  # redirects to authentication.html if not logged in
def update_appointment(request, appointment_id):
    # Get appointment by ID
    appointment = get_object_or_404(Calendar, id=appointment_id )
    print( appointment_id,appointment_id)
    
    # Get data from request and validate against the serializer: Save if validated
    if request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = CalendarSerializer(appointment, data=data, partial=True) #use update functionality of CalendarSerializer
        if serializer.is_valid():
            serializer.save()
            return JsonResponse({'status': 'success'})
        
        # Return validation errors
        return JsonResponse(serializer.errors, status=400)


# ====================================== #
#      DELETE CALENDAR APPPOINTMENTS     #
# ====================================== #
@csrf_exempt
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def delete_appointment(request, appointment_id):
    # Get appointment by ID
    appointment = get_object_or_404(Calendar, id=appointment_id)

    # Initialise serializer and delete appointments if validated
    if request.method == 'POST':
        serializer = CalendarSerializer(appointment, data={}, partial=True) #use delete validation functionality of CalendarSerializer
        if serializer.is_valid():
            result = serializer.delete() # Delete
            return JsonResponse(result, status=200)
        else:
            # Return validation errors
            return JsonResponse(serializer.errors, status=400)



# =============================================================================== #
#                                  MESSAGING SYSTEM                               #
# =============================================================================== #
# ====================================== #
#                  INBOX                 #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def inbox(request):
    # Retrive messages for the user logged in
    messages = Message.objects.filter(recipient=request.user) # Recieved messages
    messages_sent = Message.objects.filter(sender=request.user) # Sent messages

    # Render inbox with message context
    return render(request, 'spectrumjobs/message_inbox.html', {
        'messages': messages, 
        'messages_sent': messages_sent, 
        'user_type': request.user.userprofile.user_type, # Enables live-chat in footer for citizens on inbox page
    })


# ====================================== #
#              GET MESSAGE               #
# ====================================== #
# Retrive selected message from inbox
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def get_message(request, pk):
    # Fetch message by primary key
    message = get_object_or_404(Message, pk=pk)
    return render(request, 'spectrumjobs/message_body.html', {'message': message})


# ====================================== #
#            GET SENT MESSAGE            #
# ====================================== #
def sent_messages(request):
    # Get all sent messages by the user
    messages_sent = Message.objects.filter(sender=request.user)

    # Render inbox with message context
    return render(request, 'spectrumjobs/message_inbox.html', {
        'messages_sent': messages_sent, 
        'user_type': request.user.userprofile.user_type, # Enables live-chat in footer for citizens on inbox page
    })


def drafts_messages(request):
    # Get all drafts for the user
    messages = Message.objects.filter(sender=request.user, read = True)

    # Render inbox with message context
    return render(request, 'spectrumjobs/message_inbox.html', {
        'messages': messages, 
        'user_type': request.user.userprofile.user_type, # Enables live-chat in footer for citizens on inbox page
    })


# ====================================== #
#             COMPOSE MESSAGE            #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def compose_message(request):
    # Handle post request: User sends newmessage 
    if request.method == 'POST':
        # Get message meta data from request
        recipient_username = request.POST.get('recipient')
        subject = request.POST.get('subject')
        body = request.POST.get('body')

        # If the recipient is a user in the User model, send message.
        try:
            # Get recipient in User model
            recipient = get_user_model().objects.get(username=recipient_username)
            message = Message(sender=request.user, recipient=recipient, subject=subject, body=body)
            message.save()

        # If recipient does not exist
        except User.DoesNotExist: 
            return HttpResponse('User does not exists.')
        
        # Redirects back to the inbox for success response
        return redirect('inbox')
    
    # Render message composer
    return render(request, 'spectrumjobs/message_compose.html')


# =============================================================================== #
#                                NOTIFICATION SYSTEM                              #
# =============================================================================== #
# Reference: #https://pypi.org/project/django-notifications-hq/
# Reference: Advanced Web Development[CM3035], Kris Kraack(self), "eLearn", "Build an eLearning application[002]", 10/03/2024, https://www.coursera.org/learn/uol-cm3035-advanced-web-development/assignment-submission/AUtna/build-an-elearning-application-002
# ====================================== #
#              NOTIFICATIONS             #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def notifications(request):
    # Get all notifications for the user logged in
    notifications = Notification.objects.filter(recipient=request.user) 
    notifications_count = notifications.count() if notifications.count() > 0 else 0 #count all notifications

    # Redirect url for feedback notifications
    feedback_url = reverse('employment_feedback')

    # Mark all notifications as read
    for notification in notifications:
        notification.mark_as_read()
    
    # Render Notification central
    return render(request, 'spectrumjobs/notifications.html', {
        'notifications': notifications, 
        'notifications_count':notifications_count,
        'feedback_url':feedback_url,
        'user_type': request.user.userprofile.user_type, # Enables live-chat in footer for citizens on notifications page
        })


# ====================================== #
#           DELETE NOTIFICATIONS         #
# ====================================== #
# Delete notification by id
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def notification_delete(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id) # Get notification by ID
    notification.delete() # Delete notification

    # Redirect to notification page
    return redirect('notifications')


# ====================================== #
#            CLEAR NOTIFICATIONS         #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def notification_clear(request):
    # Clear all notificaitons
    if request.method == 'POST':
        Notification.objects.all().delete() # Delete all notifications for the user

    # Redirect to notification page
    return redirect('notifications')


# ====================================== #
#            CANDIDATE INQUIRE           #
# ====================================== #
# Used for employers to show interest in matched applicaitons: The notification is send to the assigned contact person
@csrf_exempt
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def notify_liaison(request):
    # Inquire about a potential candidate
    if request.method == "POST":
        # Retrieve data from request
        data = json.loads(request.body)
        citizen_id = data.get("citizen_id")
        job_id = data.get("job_id")  # Ensure you get the job ID as well

        # Get the citizen user by the citizen ID obtained via the request
        try:
            citizen = User.objects.get(id=citizen_id) # Get citizen user 
            citizen_profile = CitizenProfile.objects.get(user=citizen) # Get citizen profile 
            liaison = citizen_profile.contact_person # Extract the assigned contact person for the citizen of interest
            job = Job.objects.get(id=job_id) # Get the job by the job_id from the request

            # Notify the liaison about the interest in the citizen for the job position
            # Create notifcation instance
            notification_tuple = notify.send(
                request.user,  
                recipient=liaison,  
                verb="is interested in",
                action_object=citizen,  
                target=citizen,  
                description=f"The employer {request.user.username} is interested in the citizen {citizen.username} for the job '{job.title}' at '{job.company_name}'."
            )

            notification = notification_tuple[0][1][0] # Retrieve first notification instance
            user = str(request.user.username) # Convert username to string for the notificaiton

            # Create a custom notification using the CustomNotification model to add additional notification data
            CustomNotification.objects.create(
                notification=notification,
                extra={
                    'job_title': job.title,
                    'company_name': job.company_name,
                    'user': user,
                }  
            )

            # Send success JSON response: Promp employer with success message
            return JsonResponse({"success": True})
        
        # Send failure JSON response: Promp employer with failure messages
        except User.DoesNotExist:
            return JsonResponse({"success": False, "error": "Citizen not found."})
        except CitizenProfile.DoesNotExist:
            return JsonResponse({"success": False, "error": "Citizen profile not found."})
        except Job.DoesNotExist:
            return JsonResponse({"success": False, "error": "Job not found."})
        
    # Error handling
    return JsonResponse({"success": False, "error": "Invalid request."})


# =============================================================================== #
#                               EMPLOYMENT FEEDBACK                               #
# =============================================================================== #
def employment_feedback(request):

    if request.user.userprofile.user_type == "citizen":
        citizen_profile = CitizenProfile.objects.get(user=request.user)
        employer = citizen_profile.employer
    else:
        employer = None

    if request.method == 'POST':
        if request.user.userprofile.user_type == 'employer':
            form = EmployerFeedbackForm(request.POST, user=request.user)
            if form.is_valid():
                employer_feedback = form.save(commit=False)
                employer_feedback.employer = request.user
                employer_feedback.save()
                return redirect('index')
        elif request.user.userprofile.user_type == 'citizen':
            form = CitizenFeedbackForm(request.POST)
            if form.is_valid():
                citizen_feedback = form.save(commit=False)
                citizen_feedback.citizen = request.user
                citizen_feedback.save()
                return redirect('index')
    else:
        if request.user.userprofile.user_type == 'employer':
            form = EmployerFeedbackForm(user=request.user)
        elif request.user.userprofile.user_type == 'citizen':
            form = CitizenFeedbackForm()
        else:
            form = None

    return render(request, 'spectrumjobs/employment_feedback.html', {
        'form': form,
        'user_type': request.user.userprofile.user_type,
        'employer':employer,
    })




# =============================================================================== #
#                                  AUTHENTICATION                                 #
# =============================================================================== #
# ====================================== #
#         AUTHENTICATION OPTIONS         #
#   Landing page for unathorized users   #
# ====================================== #
def authentication(request):
    return render(request, 'spectrumjobs/authentication.html')


# ====================================== #
#         AUTHENTICATION SETTINGS        #
#           Enable/disable 2FA           #
# ====================================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def auth_settings(request):
    # Render authentication option template 
    return render(request, 'spectrumjobs/auth_settings.html', {'user_type': request.user.userprofile.user_type}) # Enables live-chat in footer for citizens on auth settings page


# ====================================== #
#       TWO-FACTOR AUTHENTICATION        #
#           Enable/disable 2FA           #
# ====================================== #
# ======================== #
#         VERIFY 2FA       #
# ======================== #
def verify_2fa(request):
    # Check for user_id in request
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    # Retrieve corresponding User object based on user_id
    user = User.objects.get(pk=user_id)

    # User one-time password verification: Verify otp provided by user from their authenticator application
    if request.method == 'POST':
        form = OTPForm(request.POST) # OTPForm from forms.py
        if form.is_valid():
            # Retrieve OTP user input
            otp = form.cleaned_data['otp']
            # Verify OTP
            if user.userprofile.verify_otp(otp):
                # OTP is correct: Sign the user in
                user.backend = 'django.contrib.auth.backends.ModelBackend' # Authentication backend
                login(request, user) # Sign in
                del request.session['user_id'] # Delete the user_id from session to enhance the security
                # Redirect to the user dashboard
                return redirect('index')
            else:
                # OTP input not correct
                form.add_error('otp', 'Invalid OTP. Please try again.')
    else:
        form = OTPForm()

    # Render verification template
    return render(request, 'spectrumjobs/auth_2fa_verify.html', {'form': form})


# ======================== #
#         ENABLE 2FA       #
# ======================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def enable_2fa(request):
    if request.method == 'POST':
        # Enable 2FA and save to corresponding Profile object
        request.user.userprofile.is_2fa_enabled = True
        request.user.userprofile.save()
        # Redirect to QR code generation
        return redirect('setup_otp')  
    return render(request, 'spectrumjobs/auth_2FA_enable.html')


# ======================== #
#        DISABLE 2FA       #
# ======================== #
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def disable_2fa(request):
    if request.method == 'POST':
        # Disable 2FA and save to corresponding Profile object
        request.user.userprofile.is_2fa_enabled = False
        request.user.userprofile.totp_secret_key = None  # Clear field for the temporary secret key 
        request.user.userprofile.save()
        # Redirect to index
        return redirect('index')
    return render(request, 'spectrumjobs/auth_2fa_disable.html')


# ======================== #
#         SETUP 2FA        #
# ======================== #
# Reference: https://pyauth.github.io/pyotp/
@login_required(login_url='authentication')  #redirects to authentication.html if not logged in
def setup_otp(request):
    # Retrieve User and Profile objects
    user = request.user
    
    # Generate random secret key with pyotp library
    secret_key = pyotp.random_base32()

    # Save secret key for the userprofile
    request.user.userprofile.totp_secret_key = secret_key
    request.user.userprofile.save()

    # Generate QR code and image data with the secret key
    totp = pyotp.TOTP(secret_key) # Time-based one-time password
    provisioning_uri = totp.provisioning_uri(user.username, issuer_name=request.META['HTTP_HOST']) # Provisioning URI for the OTP
    qr_code = generate_qr_code(provisioning_uri) # QR code image generation using generate_qr_code function from utils.py

    # Render the QR code image
    return render(request, 'spectrumjobs/auth_2fa_qrcode.html', {'qr_code': qr_code})



# ====================================== #
#          MitID  AUTHENTICATION         #
#         Required for Danish user       #
# ====================================== #
# ======================== #
#       MITID LOGIN        #
# ======================== #
def mitid_login(request):
    return render(request, 'spectrumjobs/mitid_login.html')


# ======================== #
#      MITID CALLBACK      #
# ======================== #
def mitid_callback(request):
    userName = None
    userID = None
    # Handle post request
    if request.method == 'POST':
        # Get username and unique name identifier returned from the broker authentication process
        userName = request.POST.get('userName') # citizen full name 
        userIdentifier = request.POST.get('userIdentifier') # Unique full name identifier 
        # Ensure userName and userIdentifier is captured correctly in the template (mitid_callback.html)
        if userName and userIdentifier:
            # Concatenated username (i.e. the full name of citizen) by replacing spaces with underscore: Enables saving in the User model:
            user_con = userName.replace(" ", "_")

            # Check if user has an profile on the platform by using the concatenated username and suffix iteration
            # Authenticate using the concatenated username and the Unique full name identifier
            while User.objects.filter(username=user_con).exists():
                num_suffix = 0 # Suffix for identical citizen names
                try:
                    # Authenticate without using the suffix
                    user = authenticate(username=user_con, password=userIdentifier)
                    # Successfull authentication: Full name and unique name identifer match
                    if user is not None:
                        user.backend = f'{ModelBackend.__module__}.{ModelBackend.__qualname__}' # Authentication backend to use (settings.py)
                        # Login and redirect to index
                        login(request, user)
                        return redirect('index')  
                    else:
                        # Authenticate using suffix iteration (i.e. unique name identifier did not match the first user with that full name)
                        user_con = f"{user_con}_{num_suffix}"
                        user = authenticate(username=user_con, password=userIdentifier)
                        # Successfull authentication: Full name with a suffix and unique name identifer match
                        if user is not None:
                            user.backend = f'{ModelBackend.__module__}.{ModelBackend.__qualname__}' # Authentication backend to use (settings.py)
                             # Login and redirect to index
                            login(request, user)
                            return redirect('index') 
                except User.DoesNotExist:
                        # The user does not exists in the database.
                        print("User does not exist with mathing identifier!")
            else:
                # If user succesfully authenticates via the MitID broker process but has not a profile yet: Create new user
                user = User.objects.create_user(username=user_con, password=userIdentifier)
                if user is not None:
                        user.backend = f'{ModelBackend.__module__}.{ModelBackend.__qualname__}' # Authentication backend to use (settings.py)
                        # Create Profile instance
                        UserProfile.objects.create(
                        user=user,
                        user_type="citizen", 
                        DK_user="yes")
                        # Login and redirect to index
                        login(request, user)
                        return redirect('index') 
                else:
                    # Handle user creation errors
                    return HttpResponse('Failed to authenticate user.')
        else:
            return HttpResponse('Missing userName or userIdentifier.')
        
    # Render MitID callback response endpoint
    return render(request, 'spectrumjobs/mitid_callback.html', {'user': userName, 'id': userID})