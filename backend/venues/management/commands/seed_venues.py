from datetime import time

from django.core.management.base import BaseCommand

from venues.models import Sport, Venue, VenueOpeningHour, VenueSport
from venues.ui_extras import VENUE_SPORTS

# TODO: ตัวอย่างสำหรับทดสอบ UI เท่านั้น ต้องเปลี่ยนเป็นเวลาจริงของแต่ละสนาม
SAMPLE_OPEN = time(9, 0)
SAMPLE_CLOSE = time(21, 0)


class Command(BaseCommand):
    help = "ใส่สนาม กีฬา และเวลาเปิด–ปิดตัวอย่าง (รันซ้ำได้)"

    def handle(self, *args, **options):
        for venue_name, sport_names in VENUE_SPORTS.items():
            venue, _ = Venue.objects.get_or_create(
                name=venue_name,
                defaults={"location_text": "TU Rangsit (TODO: ใส่จุดนัดพบจริง)"},
            )
            for sport_name in sport_names:
                sport, _ = Sport.objects.get_or_create(name=sport_name)
                VenueSport.objects.get_or_create(venue=venue, sport=sport)
            for weekday in range(7):
                VenueOpeningHour.objects.get_or_create(
                    venue=venue,
                    weekday=weekday,
                    opens_at=SAMPLE_OPEN,
                    defaults={"closes_at": SAMPLE_CLOSE},
                )
        self.stdout.write("seed done")
