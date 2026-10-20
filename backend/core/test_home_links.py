"""Home navigation has real destination pages for the Sprint 1 UI flow."""

from html.parser import HTMLParser

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.urls import reverse


class ControlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])


def hrefs(html):
    parser = ControlParser()
    parser.feed(html)
    return parser.hrefs


class HomeLinkTests(SimpleTestCase):
    def test_home_has_sprint_one_navigation_and_no_placeholder_link(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'href="#"')
        for url in (
            reverse("home"),
            reverse("login-page"),
            reverse("party-create-page"),
            reverse("venues:venue_map"),
        ):
            with self.subTest(url=url):
                self.assertIn(url, hrefs(response.content.decode()))

    def test_home_keeps_business_api_out_of_markup(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "/api/v1/")


class NavbarPartialTests(SimpleTestCase):
    def test_create_button_has_a_real_destination(self):
        html = render_to_string("partials/navbar.html", {"active": "home", "show_create": True})
        self.assertIn(f'href="{reverse("party-create-page")}"', html)
        self.assertNotIn('href="#"', html)

    def test_venues_link_uses_its_active_state(self):
        html = render_to_string("partials/navbar.html", {"active": "venues", "show_create": False})
        self.assertIn(f'href="{reverse("venues:venue_map")}" class="active"', html)
