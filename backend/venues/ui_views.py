from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Venue, VenueSport
from .ui_extras import (
    BUILDING_LABEL,
    CATALOG_BUILDING,
    COURT_COUNT,
    MAX_PLAYERS,
    SPORT_EMOJI,
    SPORT_IMAGES,
    VENUE_POS,
)

WEEKDAY_SHORT = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]


def _sport_dict(venue_name, sport):
    count = COURT_COUNT.get((venue_name, sport.name))
    if count:
        courts = [f"{sport.name} คอร์ต {i:02d}" for i in range(1, count + 1)]
    else:
        courts = [sport.name]
    return {
        "id": sport.id,
        "name": sport.name,
        "emoji": SPORT_EMOJI.get(sport.name, ""),
        "court_count": count,
        "max_players": MAX_PLAYERS.get(sport.name, 4),
        "book_first": bool(count),
        "courts": courts,
        "image": SPORT_IMAGES.get((venue_name, sport.name)),
    }


def _hours_summary(venue):
    """สรุปเวลาเปิด–ปิดเป็นบรรทัดสั้นๆ เช่น 'จ.–อา. 09:00–21:00'"""
    groups = []
    for h in venue.opening_hours.order_by("weekday", "opens_at"):
        span = (h.opens_at, h.closes_at)
        if groups and groups[-1]["span"] == span and groups[-1]["last"] == h.weekday - 1:
            groups[-1]["last"] = h.weekday
        else:
            groups.append({"first": h.weekday, "last": h.weekday, "span": span})

    lines = []
    for g in groups:
        first, last = WEEKDAY_SHORT[g["first"]], WEEKDAY_SHORT[g["last"]]
        days = first if g["first"] == g["last"] else f"{first}–{last}"
        lines.append(f"{days} {g['span'][0]:%H:%M}–{g['span'][1]:%H:%M}")
    return lines


def _venue_sports(venue):
    links = venue.venue_sports.select_related("sport").order_by("id")
    return [_sport_dict(venue.name, link.sport) for link in links]


def _venue_dict(venue):
    return {
        "id": venue.id,
        "name": venue.name,
        "hours": _hours_summary(venue),
        "sports": _venue_sports(venue),
    }


def _map_buildings():
    """Group active catalog venues into map buildings; venues without a position are skipped."""
    buildings = {}
    for venue in Venue.objects.filter(is_active=True).order_by("id"):
        key = CATALOG_BUILDING.get(venue.name)
        pos = VENUE_POS.get(key)
        if pos is None:
            continue
        building = buildings.setdefault(
            key,
            {"id": venue.id, "name": BUILDING_LABEL.get(key, key), "pos": pos, "sports": []},
        )
        building["sports"] += [{**s, "venue_id": venue.id} for s in _venue_sports(venue)]
    return list(buildings.values())


@require_GET
def venue_map(request):
    return render(request, "venues/venue_map.html", {"venues": _map_buildings()})


@require_GET
def venue_detail(request, venue_id):
    venue = _venue_dict(get_object_or_404(Venue, pk=venue_id, is_active=True))

    # Skip to sport_detail
    if len(venue["sports"]) == 1:
        return redirect(
            "venues:sport_detail", venue_id=venue["id"], sport_id=venue["sports"][0]["id"]
        )
    return render(request, "venues/venue_detail.html", {"venue": venue})


@require_GET
def sport_detail(request, venue_id, sport_id):
    venue_obj = get_object_or_404(Venue, pk=venue_id, is_active=True)
    link = (
        VenueSport.objects.filter(venue=venue_obj, sport_id=sport_id)
        .select_related("sport")
        .first()
    )
    if link is None:
        raise Http404

    venue = _venue_dict(venue_obj)
    sport = _sport_dict(venue_obj.name, link.sport)
    hours = venue_obj.opening_hours.order_by("weekday", "opens_at")

    # Catalog venues have one sport each and skip their venue page, so go back to the map
    back_url = reverse("venues:venue_map")
    return render(
        request,
        "venues/sport_detail.html",
        {"venue": venue, "sport": sport, "back_url": back_url, "hours": hours},
    )
