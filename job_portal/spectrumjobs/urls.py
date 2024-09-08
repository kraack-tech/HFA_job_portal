from django.urls import path
from .views import *
from django.contrib.auth.views import PasswordChangeView 
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # ============================ #
    #       DASHBOARDS             #
    # ============================ #
    path('', index, name='index'), #citizen & employers
    path('monitor/', monitor, name='monitor'), #liasions

    
    # ============================ #
    #       AUTHENTICATION         #
    # ============================ #
    path('signup/', signup, name='signup'),
    path('signin/', signin, name='signin'),
    path('signout/', signout, name='signout'),
    path('authentication', authentication, name='authentication'),
    path('update_pw/', login_required(login_url='/login/') (
        PasswordChangeView.as_view(template_name='spectrumjobs/auth_pw_update.html', 
                                   success_url='/')), 
                                   name='update_pw'
                                   ), 
    path('auth_settings/', auth_settings, name='auth_settings'),
    path('success/', oauth_success, name='success'),

    # ============================ #
    #   3RD-PARTY AUTHENTICATION   #
    # ============================ #
    #MitId
    path('mitid-login/', mitid_login, name='mitid_login'),
    path('mitid_callback/', mitid_callback, name='mitid_callback'),

    #2FA
    path('enable-2fa/', enable_2fa, name='enable_2fa'),
    path('disable-2fa/', disable_2fa, name='disable_2fa'),
    path('setup-otp/', setup_otp, name='setup_otp'),
    path('verify-2fa/', verify_2fa, name='verify_2fa'),

    # ============================ #
    #         JOB PORTAL           #
    # ============================ #
    path('portal/', portal, name='portal'),
    path('job/<int:job_id>/details/', job_details, name='job_details'),
    path('job/<int:job_id>/apply/', apply_job_view, name='apply_job'),
    path('post-job/', post_job, name='post_job'),
    path('delete-job/<int:job_id>/', delete_job, name='delete_job'),

    # ============================ #
    #         SUGGESTIONS          #
    # ============================ #
    path('get_matches/', get_matches, name='get_matches'),

    # ============================= #
    #   SENSORY/TRAINING PROFILES   #
    # ============================= #
    path('profile_info/', profile_info, name='profile_info'),
    path('profile/<int:user_id>/', profile_data, name='profile_data'), 

    # ============================ #
    #           CALENDAR           #
    # ============================ #
    path('api/calendar/', get_appointments, name='get_appointments'),
    path('api/calendar/add/', add_appointment, name='add_appointment'),
    path('api/calendar/update/<int:appointment_id>/', update_appointment, name='update_appointment'),
    path('api/calendar/delete/<int:appointment_id>/', delete_appointment, name='delete_appointment'),

    # ============================ #
    #            INBOX             #
    # ============================ #
    path('inbox/', inbox, name='inbox'),
    path('message/<int:pk>/', get_message, name='get_message'),
    path('compose/', compose_message, name='compose_message'),
    path('sent/', sent_messages, name='sent'),
    path('drafts/', drafts_messages, name='drafts'),

    # ============================ #
    #        NOTIFICATIONS         #
    # ============================ #
    path('notifications/', notifications, name='notifications'), 
    path('notification_delete/<int:notification_id>/', notification_delete, name='notification_delete'), 
    path('notification_clear/', notification_clear, name='notification_clear'), 
    path('notify_liaison/', notify_liaison, name='notify_liaison'),  # Candidate interest by employer

    # ============================ #
    #           FEEDBACK           #
    # ============================ #
    path('employment_feedback/', employment_feedback, name='employment_feedback'),
]


