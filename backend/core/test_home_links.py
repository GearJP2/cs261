"""PR #44 review: home/navbar controls link to real pages or are clearly disabled."""

from html.parser import HTMLParser

from django.template.loader import render_to_string
from django.test import SimpleTestCase
from django.urls import reverse

DISABLED_LABELS = (
    "สร้างปาร์ตี้",
    "เข้าร่วม",
    "ดูทั้งหมด",
    "ดูแผนที่สนาม",
    "สนามและกีฬา",
    "ปาร์ตี้ของฉัน",
    "โปรไฟล์",
    "ออกจากระบบ",
)


class ControlParser(HTMLParser):
    """Collect hrefs, forms and the text of each aria-disabled element."""

    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.forms = []
        self.disabled = []
        self._stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "href" in attrs and tag == "a":
            self.hrefs.append(attrs["href"])
        if tag == "form":
            self.forms.append(attrs)
        if attrs.get("aria-disabled") == "true":
            self.disabled.append({"tag": tag, "attrs": attrs, "text": ""})
            self._stack.append(len(self.disabled) - 1)
        elif self._stack:
            self._stack.append(None)

    def handle_endtag(self, tag):
        if self._stack:
            self._stack.pop()

    def handle_data(self, data):
        for index in self._stack:
            if index is not None:
                self.disabled[index]["text"] += data


def parse(html):
    parser = ControlParser()
    parser.feed(html)
    return parser


class HomeLinkTests(SimpleTestCase):
    def setUp(self):
        self.response = self.client.get(reverse("home"))
        self.assertEqual(self.response.status_code, 200)
        self.html = self.response.content.decode()

    def test_home_has_no_placeholder_links(self):
        self.assertNotContains(self.response, 'href="#"')
        self.assertNotIn("#", parse(self.html).hrefs)

    def test_disabled_controls_are_marked_and_have_no_href(self):
        disabled = parse(self.html).disabled
        texts = " ".join(item["text"] for item in disabled)
        # Navbar create button is hidden on home (show_create=False); the hero CTA remains.
        for label in DISABLED_LABELS:
            with self.subTest(label=label):
                self.assertIn(label, texts)
        self.assertEqual(sum("เข้าร่วม" in item["text"] for item in disabled), 3)
        for item in disabled:
            with self.subTest(text=item["text"].strip()):
                self.assertNotEqual(item["tag"], "a")
                self.assertNotIn("href", item["attrs"])
                self.assertIn("is-disabled", item["attrs"]["class"].split())
                self.assertIn("เร็วๆ นี้", item["text"])

    def test_real_links_resolve_to_home_route(self):
        # Logo and the "หาปาร์ตี้" nav link.
        self.assertContains(self.response, f'href="{reverse("home")}"', count=2)
        self.assertEqual(set(parse(self.html).hrefs), {reverse("home")})

    def test_home_does_not_link_json_api_or_venue_pages(self):
        # Logout is JSON-only (POST /api/v1/auth/logout), so it stays disabled for now.
        self.assertNotContains(self.response, "/api/v1/")
        self.assertNotContains(self.response, reverse("accounts:logout"))
        self.assertEqual(parse(self.html).forms, [])


class NavbarPartialTests(SimpleTestCase):
    def render(self, **context):
        return render_to_string("partials/navbar.html", context)

    def test_create_button_is_disabled_when_shown(self):
        html = self.render(active="home", show_create=True)
        self.assertNotIn('href="#"', html)
        create = [item for item in parse(html).disabled if "สร้างปาร์ตี้" in item["text"]]
        self.assertEqual(len(create), 1)
        self.assertIn("nv-create", create[0]["attrs"]["class"].split())

    def test_active_state_is_kept_on_disabled_section(self):
        for active, label in (("venues", "สนามและกีฬา"), ("mine", "ปาร์ตี้ของฉัน")):
            with self.subTest(active=active):
                items = parse(self.render(active=active)).disabled
                item = next(item for item in items if label in item["text"])
                self.assertIn("active", item["attrs"]["class"].split())
                self.assertEqual(item["attrs"].get("aria-current"), "page")
