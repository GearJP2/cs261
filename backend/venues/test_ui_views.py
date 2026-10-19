import re
from datetime import time

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from . import venue_catalog
from .models import Sport, Venue, VenueOpeningHour, VenueSport
from .ui_extras import BUILDING_LABEL, CATALOG_BUILDING, MAX_PLAYERS, VENUE_POS
from .ui_views import _hours_summary


class CatalogMappingTests(SimpleTestCase):
    def test_mapping_uses_real_catalog_names(self):
        catalog_names = {record["name"] for record in venue_catalog.VENUES}
        self.assertLessEqual(set(CATALOG_BUILDING), catalog_names)

    def test_every_mapped_building_has_position_and_label(self):
        for building in set(CATALOG_BUILDING.values()):
            with self.subTest(building=building):
                self.assertIn(building, VENUE_POS)
                self.assertIn(building, BUILDING_LABEL)

    def test_max_players_keys_are_catalog_sports(self):
        catalog_sports = {record["sport"] for record in venue_catalog.VENUES}
        self.assertLessEqual(set(MAX_PLAYERS), catalog_sports)


class VenueUiTestCase(TestCase):
    def add_venue(self, name, *sport_names, is_active=True):
        venue = Venue.objects.create(name=name, location_text="มธ. ศูนย์รังสิต", is_active=is_active)
        for sport_name in sport_names:
            sport, _ = Sport.objects.get_or_create(name=sport_name)
            VenueSport.objects.create(venue=venue, sport=sport)
        return venue


class VenueMapTests(VenueUiTestCase):
    def get_buildings(self):
        response = self.client.get(reverse("venues:venue_map"))
        self.assertEqual(response.status_code, 200)
        return response.context["venues"]

    def test_tennis_and_pickleball_share_one_building_with_their_own_venue_ids(self):
        tennis = self.add_venue("สนามเทนนิส", "เทนนิส")
        pickleball = self.add_venue("สนามพิกเคิลบอล", "พิกเคิลบอล")

        buildings = self.get_buildings()

        self.assertEqual(len(buildings), 1)
        building = buildings[0]
        self.assertEqual(building["id"], tennis.id)
        self.assertEqual(building["name"], BUILDING_LABEL["Tennis Court"])
        self.assertEqual(building["pos"], VENUE_POS["Tennis Court"])
        self.assertEqual(
            [(s["name"], s["venue_id"]) for s in building["sports"]],
            [("เทนนิส", tennis.id), ("พิกเคิลบอล", pickleball.id)],
        )

    def test_sport_menu_links_use_each_sports_venue_id(self):
        tennis = self.add_venue("สนามเทนนิส", "เทนนิส")
        pickleball = self.add_venue("สนามพิกเคิลบอล", "พิกเคิลบอล")
        sport = Sport.objects.get(name="พิกเคิลบอล")

        response = self.client.get(reverse("venues:venue_map"))

        self.assertContains(response, f'href="/venues/{pickleball.id}/sports/{sport.id}/"')
        self.assertNotContains(response, f'href="/venues/{tennis.id}/sports/{sport.id}/"')

    def test_unmapped_active_venues_are_listed_under_other_venues(self):
        softball = self.add_venue("สนามซอฟท์บอล", "ซอฟท์บอล")
        unknown = self.add_venue("สนามที่ไม่มีใน catalog", "แบดมินตัน")
        swimming = self.add_venue("สระว่ายน้ำ ศูนย์กีฬาทางน้ำ", "ว่ายน้ำ")

        response = self.client.get(reverse("venues:venue_map"))

        self.assertEqual([b["id"] for b in response.context["venues"]], [swimming.id])
        others = response.context["other_venues"]
        self.assertEqual([v["id"] for v in others], [softball.id, unknown.id])
        self.assertEqual([s["name"] for s in others[0]["sports"]], ["ซอฟท์บอล"])
        self.assertContains(response, "สนามอื่น ๆ")
        for venue in (softball, unknown):
            self.assertContains(
                response, f'href="{reverse("venues:venue_detail", args=[venue.id])}"'
            )

    def test_mapped_venues_are_not_duplicated_in_other_venues(self):
        tennis = self.add_venue("สนามเทนนิส", "เทนนิส")
        pickleball = self.add_venue("สนามพิกเคิลบอล", "พิกเคิลบอล")
        softball = self.add_venue("สนามซอฟท์บอล", "ซอฟท์บอล")

        response = self.client.get(reverse("venues:venue_map"))

        other_ids = [v["id"] for v in response.context["other_venues"]]
        self.assertEqual(other_ids, [softball.id])
        self.assertNotIn(tennis.id, other_ids)
        self.assertNotIn(pickleball.id, other_ids)

    def test_inactive_unmapped_venue_appears_nowhere(self):
        softball = self.add_venue("สนามซอฟท์บอล", "ซอฟท์บอล", is_active=False)

        response = self.client.get(reverse("venues:venue_map"))

        self.assertEqual(response.context["venues"], [])
        self.assertEqual(response.context["other_venues"], [])
        self.assertNotContains(response, softball.name)

    def test_other_venues_section_hidden_when_every_venue_is_mapped(self):
        self.add_venue("สนามเทนนิส", "เทนนิส")

        response = self.client.get(reverse("venues:venue_map"))

        self.assertEqual(response.context["other_venues"], [])
        self.assertNotContains(response, "สนามอื่น ๆ")
        self.assertNotContains(response, "other-venues")

    def test_other_venue_link_reaches_its_page(self):
        softball = self.add_venue("สนามซอฟท์บอล", "ซอฟท์บอล")
        sport = Sport.objects.get(name="ซอฟท์บอล")
        multi = self.add_venue("สนามรวมไม่มีตำแหน่ง", "ฟุตบอล", "ฟุตซอล")

        single = self.client.get(reverse("venues:venue_detail", args=[softball.id]))
        self.assertRedirects(single, reverse("venues:sport_detail", args=[softball.id, sport.id]))

        many = self.client.get(reverse("venues:venue_detail", args=[multi.id]))
        self.assertEqual(many.status_code, 200)

    def test_inactive_venue_is_hidden(self):
        self.add_venue("สนามฟุตซอล", "ฟุตซอล", is_active=False)

        self.assertEqual(self.get_buildings(), [])


class VenueDetailTests(VenueUiTestCase):
    def test_single_sport_venue_redirects_to_sport_page(self):
        venue = self.add_venue("สนามเทนนิส", "เทนนิส")
        sport = Sport.objects.get(name="เทนนิส")

        response = self.client.get(reverse("venues:venue_detail", args=[venue.id]))

        self.assertRedirects(response, reverse("venues:sport_detail", args=[venue.id, sport.id]))

    def test_multi_sport_venue_renders_detail_page(self):
        venue = self.add_venue("สนามรวม", "เทนนิส", "พิกเคิลบอล")

        response = self.client.get(reverse("venues:venue_detail", args=[venue.id]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "venues/venue_detail.html")
        self.assertEqual(len(response.context["venue"]["sports"]), 2)

    def test_missing_or_inactive_venue_returns_404(self):
        inactive = self.add_venue("สนามฟุตซอล", "ฟุตซอล", is_active=False)
        for venue_id in (inactive.id, inactive.id + 999):
            with self.subTest(venue_id=venue_id):
                response = self.client.get(reverse("venues:venue_detail", args=[venue_id]))
                self.assertEqual(response.status_code, 404)


class SportDetailTests(VenueUiTestCase):
    def test_people_row_shows_max_players_for_sport(self):
        venue = self.add_venue("สนามสควอช ยิมเนเซียม 7", "สควอช")
        sport = Sport.objects.get(name="สควอช")

        response = self.client.get(reverse("venues:sport_detail", args=[venue.id, sport.id]))

        self.assertEqual(response.context["sport"]["max_players"], 2)
        self.assertContains(response, "_/2คน")
        self.assertNotContains(response, "_/4คน")

    def test_unknown_sport_falls_back_to_four_players(self):
        venue = self.add_venue("สนามทดลอง", "ปิงปอง")
        sport = Sport.objects.get(name="ปิงปอง")
        self.assertNotIn("ปิงปอง", MAX_PLAYERS)

        response = self.client.get(reverse("venues:sport_detail", args=[venue.id, sport.id]))

        self.assertEqual(response.context["sport"]["max_players"], 4)
        self.assertContains(response, "_/4คน")

    def test_sport_page_renders_with_back_link_to_map(self):
        venue = self.add_venue("สนามสควอช ยิมเนเซียม 7", "สควอช")
        sport = Sport.objects.get(name="สควอช")

        response = self.client.get(reverse("venues:sport_detail", args=[venue.id, sport.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["back_url"], reverse("venues:venue_map"))
        self.assertEqual(response.context["sport"]["courts"], ["สควอช คอร์ต 01", "สควอช คอร์ต 02"])

    def test_court_buttons_are_disabled_coming_soon(self):
        venue = self.add_venue("สนามสควอช ยิมเนเซียม 7", "สควอช")
        sport = Sport.objects.get(name="สควอช")

        response = self.client.get(reverse("venues:sport_detail", args=[venue.id, sport.id]))

        html = response.content.decode()
        buttons = re.findall(r"<button([^>]*)>(.*?)</button>", html, re.S)
        self.assertEqual(len(buttons), 2)
        for attrs, label in buttons:
            self.assertIn(" disabled", attrs)
            self.assertIn('aria-disabled="true"', attrs)
            self.assertEqual(re.sub(r"<span[^>]*>.*?</span>", "", label).strip(), "เลือก")
        self.assertContains(response, "เลือก", count=2)
        self.assertContains(response, '<span class="vu-soon-badge">เร็วๆ นี้</span>', count=2)
        self.assertNotContains(response, "ดูรายละเอียด")

    def test_sport_not_linked_to_venue_returns_404(self):
        venue = self.add_venue("สนามเทนนิส", "เทนนิส")
        other = Sport.objects.create(name="ฟุตบอล")

        response = self.client.get(reverse("venues:sport_detail", args=[venue.id, other.id]))

        self.assertEqual(response.status_code, 404)

    def test_nonexistent_sport_returns_404(self):
        venue = self.add_venue("สนามเทนนิส", "เทนนิส")
        self.assertFalse(Sport.objects.filter(pk=999).exists())

        response = self.client.get(reverse("venues:sport_detail", args=[venue.id, 999]))

        self.assertEqual(response.status_code, 404)

    def test_missing_or_inactive_venue_returns_404(self):
        inactive = self.add_venue("สนามเทนนิส", "เทนนิส", is_active=False)
        sport = Sport.objects.get(name="เทนนิส")
        for venue_id in (inactive.id, inactive.id + 999):
            with self.subTest(venue_id=venue_id):
                response = self.client.get(
                    reverse("venues:sport_detail", args=[venue_id, sport.id])
                )
                self.assertEqual(response.status_code, 404)


class HoursSummaryTests(VenueUiTestCase):
    def test_consecutive_days_with_same_hours_are_grouped(self):
        venue = self.add_venue("สนามแบดมินตัน ยิมอินเตอร์โซน", "แบดมินตัน")
        for weekday in (0, 1, 2, 3, 4, 6):
            VenueOpeningHour.objects.create(
                venue=venue, weekday=weekday, opens_at=time(16), closes_at=time(21)
            )
        VenueOpeningHour.objects.create(
            venue=venue, weekday=5, opens_at=time(9), closes_at=time(12)
        )

        self.assertEqual(
            _hours_summary(venue),
            ["จ.–ศ. 16:00–21:00", "ส. 09:00–12:00", "อา. 16:00–21:00"],
        )
