from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("venues/", include("venues.urls")),
    path("", include("core.urls")),
]
