import json
import urllib.request
from urllib.error import URLError, HTTPError

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET


@require_GET
def home(request):
    return render(request, "home.html")


@require_GET
 def profile_view(request, id):
     api_url = request.build_absolute_uri(f"/api/v1/users/{id}/profile")

     status_code = 200
     try:
         req = urllib.request.Request(api_url)

         cookie_header = "; ".join([f"{k}={v}" for k, v in request.COOKIES.items()])
         if cookie_header:
             req.add_header("Cookie", cookie_header)

         with urllib.request.urlopen(req, timeout=5) as response:
             data = response.read().decode("utf-8")
             profile = json.loads(data)

     except HTTPError as e:
         profile = None
         status_code = e.code
     except URLError:
         profile = None
         status_code = 500

     return render(request, "profile.html", {"profile": profile}, status=status_code)


@require_GET
def live(request):
    return JsonResponse({"status": "ok"})


@require_GET
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        # Return a stable error without leaking connection details or credentials.
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})
