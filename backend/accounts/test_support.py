"""University session fixtures for tests, not a login path for the application."""

from django.utils import timezone

from .models import UniversityIdentity


def force_university_login(client, user):
    """Install a local verified identity/session without calling the provider.

    Existing identity evidence is left unchanged so revocation is not undone.
    Tests of login itself must exercise the login endpoint instead.
    """
    now = timezone.now()
    identity, _ = UniversityIdentity.objects.get_or_create(
        user=user,
        provider_key="tu",
        subject=f"test-user-{user.pk}",
        defaults={"student_verified_at": now, "eligibility_checked_at": now},
    )
    client.force_login(user)
    session = client.session
    session["university_identity_id"] = identity.pk
    session.save()
    return identity
