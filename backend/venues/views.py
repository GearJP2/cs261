# from django.shortcuts import render

# Create your views here.
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from . import ui_data


@require_GET
def venue_map(request):
    return render(request, "venues/venue_map.html", {"venues": ui_data.get_venues()})


@require_GET
def venue_detail(request, venue_id):
    venue = ui_data.get_venue(venue_id)
    if venue is None:
        raise Http404

    # Skip to sport_detail
    if len(venue["sports"]) == 1:
        return redirect(
            "venues:sport_detail", venue_id=venue["id"], sport_id=venue["sports"][0]["id"]
        )
    return render(request, "venues/venue_detail.html", {"venue": venue})


@require_GET
def sport_detail(request, venue_id, sport_id):
    venue, sport = ui_data.get_sport(venue_id, sport_id)
    if sport is None:
        raise Http404
    # A single-sport venue skips its venue page, so go back to the map
    if len(venue["sports"]) > 1:
        back_url = reverse("venues:venue_detail", args=[venue_id])
    else:
        back_url = reverse("venues:venue_map")
    return render(
        request,
        "venues/sport_detail.html",
        {"venue": venue, "sport": sport, "back_url": back_url},
    )
