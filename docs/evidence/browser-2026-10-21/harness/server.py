"""Disposable browser-test server: mocks only the external TU provider.

Lives outside the repository and is used only with the isolated evidence DB.
Normal Django login, sessions, CSRF, views, services and templates stay real.
"""
import json
import os
import sys
from datetime import time, timedelta

sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from accounts import views
from accounts.models import UserProfile, UserSportInterest
from accounts.services import get_or_create_university_user, UniversityLoginRejected
from parties.models import Party, PartyMembership
from venues.models import Sport, Venue, VenueSport, VenueOpeningHour

assert settings.DATABASES['default']['NAME'] == 'evidence_browser', 'Test DB only'
assert not settings.TU_APPLICATION_KEY, 'No real TU credential in mock harness'
call_command('migrate', interactive=False, verbosity=0)

names = {'mock_host': 'ผู้จัดทดสอบ โกล', 'mock_viewer': 'ผู้ขอทดสอบ เอ',
         'mock_empty': 'โปรไฟล์ข้อมูลว่าง', 'mock_zero': 'โปรไฟล์ศูนย์คะแนน'}
users = {}
for subject, name in names.items():
    users[subject] = get_or_create_university_user(
        {'subject': subject, 'display_name': name, 'type': 'student'})
sport, _ = Sport.objects.get_or_create(name='แบดมินตัน ทดสอบ')
venue, _ = Venue.objects.get_or_create(name='สนามจำลองสำหรับ Browser test',
    defaults={'location_text': 'MOCK — ไม่ใช่ข้อมูลสนามมหาวิทยาลัย'})
VenueSport.objects.get_or_create(venue=venue, sport=sport)
for weekday in range(7):
    VenueOpeningHour.objects.get_or_create(venue=venue, weekday=weekday,
        opens_at=time(0), defaults={'closes_at': time(23,59)})
UserProfile.objects.filter(user=users['mock_host']).update(credit_score=75)
UserProfile.objects.filter(user=users['mock_zero']).update(credit_score=0)
UserSportInterest.objects.get_or_create(user=users['mock_host'], sport=sport)
start = timezone.localtime() + timedelta(days=1)
start = start.replace(hour=17, minute=0, second=0, microsecond=0)
party, _ = Party.objects.get_or_create(title='ปาร์ตี้ทดสอบโปรไฟล์',
    defaults={'host': users['mock_host'], 'sport': sport, 'venue': venue,
        'starts_at': start, 'ends_at': start+timedelta(hours=1), 'capacity': 4})
PartyMembership.objects.get_or_create(party=party, user=users['mock_host'])
print('FIXTURES '+json.dumps({'users': {k:v.pk for k,v in users.items()},
    'party_id':party.pk, 'sport_id':sport.pk,'venue_id':venue.pk}, ensure_ascii=False), flush=True)

def mock_provider(username, password):
    if username not in names or password != 'fixture-only':
        raise UniversityLoginRejected('Mock credentials rejected')
    return {'status': True, 'username': username,
            'displayname_th': names[username], 'type': 'student'}

views.call_university_api = mock_provider
print('MOCK TU PROVIDER: isolated local test only; not real TU verification', flush=True)
call_command('runserver', '0.0.0.0:8000', use_reloader=False)
