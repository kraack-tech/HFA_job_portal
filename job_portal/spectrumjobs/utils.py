
from notifications.models import Notification
from .models import * 
from django.http import HttpResponseForbidden
from functools import wraps
import pyotp
import qrcode
import base64
from django.http import HttpResponse
from django.shortcuts import render
from .models import *
from io import BytesIO

# =============================================================================== #
#                          LIAISON AUTHORIZATION FUNCTION                         #
# =============================================================================== #
# References: 
# https://docs.djangoproject.com/en/2.2/_modules/django/contrib/auth/decorators/
# PhoebeB, 25/05/2011, https://stackoverflow.com/questions/5469159/how-to-create-a-custom-decorator-in-django 
# Create custom wrap for views only accessible to liaisons
def liaison_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            user = UserProfile.objects.get(user=request.user) 
            if user.user_type == 'liaison':
                return view_func(request, *args, **kwargs)
        except UserProfile.DoesNotExist:
            pass  

        # Http response for unauthorized access
        return HttpResponseForbidden("You are not allowed to access this page.")
    return _wrapped_view


# =============================================================================== #
#                                JOB SORTING FUNCTION                             #
# =============================================================================== #
# Sorts jobs displayed on the job portal
def sort_jobs(jobs, sort_by, user_type, score ):
    if user_type == "citizen":
        # Sort by user sorting option from the request for citizens
        if sort_by == "newest":
            jobs_sorted = jobs.order_by('-posted_date')  # Sort by newest
        elif sort_by == "oldest":
            jobs_sorted = jobs.order_by('posted_date')  # Sort by oldest
        elif sort_by == "best_match":
            jobs_sorted = sorted(jobs, key=lambda job: score.get(job.id, 0), reverse=True) # Sort by best match
        # Default sort
        else: 
            jobs_sorted = sorted(jobs, key=lambda job: score.get(job.id, 0), reverse=True) # Sort by best match
    else:
        # Sort by user sorting option from the request for other user types
        if sort_by == "newest":
            jobs_sorted = jobs.order_by('-posted_date')  # Sort by newest
        elif sort_by == "oldest":
            jobs_sorted = jobs.order_by('posted_date')  # Sort by oldest
        # Default sort
        else: 
            jobs_sorted = jobs.order_by('-posted_date')  # Sort by newest
    return jobs_sorted


# =============================================================================== #
#                   MITID URL-RESPONSE CODE VALIDATOR FUNCTION                    #
# =============================================================================== #
# Reference used: https://stackoverflow.com/questions/11592261/check-if-a-string-is-hexadecimal
# Validate url code of MitID broker response
def validate_third_party_code(code):
    if len(code) == 32 and all(c in '0123456789abcdefABCDEF' for c in code):
        return True
    else:
        return False

# =============================================================================== #
#                          GENERATE QR CODE IMAGE FUNCTION                        #
# =============================================================================== #
# References:
# https://pypi.org/project/qrcode/
# https://www.geeksforgeeks.org/generate-qr-code-using-qrcode-in-python/
# https://medium.com/@rahulmallah785671/create-qr-code-by-using-python-2370d7bd9b8d
def generate_qr_code(data):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    qr_image.save(buffer)
    qr_code = base64.b64encode(buffer.getvalue()).decode()
    return qr_code