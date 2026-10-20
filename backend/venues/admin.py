from django.contrib import admin

from .models import Sport, Venue, VenueOpeningHour, VenueSport

admin.site.register([Sport, Venue, VenueSport, VenueOpeningHour])
