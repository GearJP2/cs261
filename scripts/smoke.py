"""Check the running Docker app, database readiness, template and static asset."""

import json
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:8000"


def fetch(path):
    with urlopen(BASE_URL + path, timeout=10) as response:
        assert response.status == 200, (path, response.status)
        return response.read().decode("utf-8")


def main():
    assert json.loads(fetch("/health/live/")) == {"status": "ok"}
    assert json.loads(fetch("/health/ready/")) == {"status": "ok", "database": "ok"}
    assert "UniSport Buddy" in fetch("/")
    assert ".welcome" in fetch("/static/css/site.css")
    print("Smoke passed: HTTP, PostgreSQL readiness, Django template and static CSS.")


if __name__ == "__main__":
    main()
