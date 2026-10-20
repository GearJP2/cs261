"""TU Rangsit reference data with explicit REAL/MOCK schedule labels."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from venues.models import Sport, Venue, VenueOpeningHour, VenueSport
from venues.venue_catalog import MARKER, VENUES, location_label


class Command(BaseCommand):
    help = "Seed TU Rangsit venues with REAL/MOCK hours labels (DEBUG=true only)."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_venues requires DEBUG=true and a development database.")
        with transaction.atomic():
            for record in VENUES:
                name = record["name"]
                matches = list(Venue.objects.filter(name=name))
                if len(matches) > 1 or (
                    matches and not matches[0].location_text.startswith(f"มธ. ศูนย์รังสิต | {MARKER} ")
                ):
                    raise CommandError(f"Reserved US9 venue name collision: {name}")
                sport, _ = Sport.objects.get_or_create(name=record["sport"])
                venue, _ = Venue.objects.update_or_create(
                    name=name,
                    defaults={"location_text": location_label(record), "is_active": True},
                )
                # Reset only marked catalog configuration; never change Party data.
                venue.venue_sports.all().delete()
                VenueSport.objects.create(venue=venue, sport=sport)
                venue.opening_hours.all().delete()
                VenueOpeningHour.objects.bulk_create(
                    [
                        VenueOpeningHour(venue=venue, weekday=day, opens_at=start, closes_at=end)
                        for day, start, end in record["intervals"]
                    ]
                )
                self.stdout.write(
                    f"{name}: venue_id={venue.pk}, venue={record['venue_kind']}, hours={record['hours_kind']}"
                )
        self.stdout.write(
            self.style.SUCCESS(
                f"TU Rangsit ready: {len(VENUES)} venues, "
                f"{len({record['sport'] for record in VENUES})} sports. "
                "Some venues and schedules are MOCK for the app demo."
            )
        )
