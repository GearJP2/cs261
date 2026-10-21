"""Control fixtures only in the disposable browser evidence database."""
import os
import sys
sys.path.insert(0, '/app/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone
from accounts.models import UniversityIdentity
from parties.models import Party, PartyMembership, JoinRequest
assert settings.DATABASES['default']['NAME'] == 'evidence_browser'
action = sys.argv[1]
if action in {'expire', 'inactive', 'active'}:
    subject = sys.argv[2]
    assert subject in {'mock_host', 'mock_viewer', 'mock_empty', 'mock_zero'}
    user = UniversityIdentity.objects.get(provider_key='tu', subject=subject).user
    if action == 'expire':
        n = 0
        for session in Session.objects.all():
            if session.get_decoded().get('_auth_user_id') == str(user.pk):
                session.expire_date = timezone.now()
                session.save(update_fields=['expire_date'])
                n += 1
        print('Expired fixture sessions:', n)
    else:
        user.is_active = action == 'active'
        user.save(update_fields=['is_active'])
        print('Fixture active:', user.is_active)
elif action == 'summary':
    import json
    print(json.dumps([{'id': p.pk, 'title': p.title, 'capacity': p.capacity,
        'host_id': p.host_id, 'active_members': PartyMembership.objects.filter(
            party=p, left_at__isnull=True).count(), 'cancelled': bool(p.cancelled_at),
        'requests': list(JoinRequest.objects.filter(party=p).values('user_id','status'))}
        for p in Party.objects.all()], ensure_ascii=False))
else:
    raise ValueError('Unsupported fixture action')
