

from notifications.signals import notify 
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.utils.translation import gettext_lazy as _
from .models import *
from notifications.models import Notification
from django.contrib import messages

# =============================================================================== #
#                                       SIGNALS                                   #
# =============================================================================== #
# Used for sending notifications when models have new or updated information about the user
# References: 
# https://www.advantch.com/blog/how-to-set-up-user-notifications-for-your-django-app-part-1/
# https://www.advantch.com/blog/how-to-set-up-user-notifications-for-your-django-app-part-2/
# ====================================== #
#               NEW MESSAGE              #
# ====================================== #
@receiver(post_save, sender=Message)
def notification_message(instance, created, **kwargs):
    if created:
        # Retrive recipient
        user = instance.recipient 

        # Send the notification
        notify.send(
            user, 
            recipient=user,
            verb=_("You have recieved a message from: "), 
            target=instance.sender, 
        )


# ====================================== #
#              NEW APPOINTMENT           #
# ====================================== #
@receiver(post_save, sender=Calendar)
def notification_message(instance, created, **kwargs):
    if created:
        # Retrive recipient
        user = instance.user 

        # Send the notification
        notify.send(
            user, 
            recipient=user, #recipient
            verb=_("You have a new appoinment with: "), #prefix
            target=instance.user, #target
        )

# ====================================== #
#           CANDIDATE INTEREST           #
# ====================================== #
# Used for employers to show interest in an applicaiton for a job position. Notification is send the the citizens contact person.
# @receiver(post_save, sender=Job) 
# def notify_liaison(sender, instance, created, **kwargs):
#     if created:
#         return
#     else:
#         # Retrive citizen and employer     
#         citizen = instance.citizen
#         employer = instance.job.employer
#         try:
#              # Get citizen profile and contact person
#             citizen_profile = CitizenProfile.objects.get(user=citizen)
#             liaison = citizen_profile.contact_person

#             # Send notification
#             notify.send(
#                 employer,
#                 recipient=liaison,
#                 verb="is interested in",
#                 action_object=citizen,
#                 description=f"The employer {employer.username} is interested in the citizen {citizen.username}."
#             )
#         except CitizenProfile.DoesNotExist:
#             pass

