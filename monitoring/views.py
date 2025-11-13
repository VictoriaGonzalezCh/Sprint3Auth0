from django.shortcuts import redirect
from django.contrib.auth import logout
from django.conf import settings
import urllib.parse


def index(request):
    return redirect("orders:list")


def logout_view(request):
   
    logout(request)

   
    domain = settings.SOCIAL_AUTH_AUTH0_DOMAIN
    client_id = settings.SOCIAL_AUTH_AUTH0_KEY

    
    return_to = request.build_absolute_uri("/")  

    return_to_encoded = urllib.parse.quote(return_to, safe="")

   
    url = (
        f"https://{domain}/v2/logout?"
        f"client_id={client_id}&returnTo={return_to_encoded}"
    )

    return redirect(url)
