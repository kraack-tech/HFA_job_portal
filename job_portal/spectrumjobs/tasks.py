from celery import shared_task
from django.utils import timezone
from notifications.signals import notify
from .models import User, UserProfile, CitizenProfile, EmployerFeedback, CitizenFeedback, CustomNotification
from django.urls import reverse

@shared_task
#funciton for sending monthly feedback notifications to citizen and employers
def send_monthly_feedback_notifications():
    #current date and start of month variables
    today = timezone.now()
    #today = timezone.datetime(2024, 9, 12, 0, 0) #testing the notification
    start_of_month = today.replace(day=1)

    #retrieve all users
    users = User.objects.all()

    #reminder flag 
    reminder = None #initial value

    #loop all users and check if a citizen or employer has submitted the required monthly feedback 
    for user in users:
        #ensure that the user is has a profile
        try:
            app_user = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            #skip: user don't have an profile
            continue

        #for employers
        if app_user.role == 'employer':
            #retrieve all employees for current employer
            try:
                company = CitizenProfile.objects.filter(employer=user).first()
            except CitizenProfile.DoesNotExist:
            #skip: company has no employees in collabortion with the application yet
                continue

            #check if active employers has submitted feedback this month
            if company:
                #search for feedback this month
                feedback_exists = EmployerFeedback.objects.filter(
                    employer=user,
                    feedback_date__gte=start_of_month,
                ).exists()
                if feedback_exists:
                    reminder = False
                else:
                    reminder = True
        
        #for citizens
        elif app_user.role == 'citizen':
            #retrieve all citizens profiles
            try:
                citizen = CitizenProfile.objects.get(user=user)
            except CitizenProfile.DoesNotExist:
           #skip: citizen has does not have an employment profile yet
                continue

            #check if citizen is currently employed and has submitted feedback this month
            if citizen.employed == True:
                feedback_exists = CitizenFeedback.objects.filter(
                    citizen=user,
                    feedback_date__gte=start_of_month,
                ).exists()
                if feedback_exists:
                    reminder = False
                else:
                    reminder = True
        else:
            feedback_exists = None
            reminder = False

        #if current employer or citizen in the iteratin has not submitted the required monthly feedback
        if reminder == True and feedback_exists != None:
    
            #create notifcation instance
            notification_tuple = notify.send(
                user,
                recipient=user,
                verb="Reminder: Please provide your monthly feedback.",
                action_object=None,
                target=None
            )

            #retrieve first notification instance
            notification = notification_tuple[0][1][0] 
            
            #add addiotnal data to the notificaiton by using the CustomNotification model (i.e., the url for the feedback response)
            CustomNotification.objects.create(
                notification=notification,
                url={'url': reverse('employment_feedback')}
            )
