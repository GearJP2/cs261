"""TU Rangsit names and field-level provenance, checked 2026-10-18.

REAL means published by TU, not live availability. MOCK hours are assumptions.
"""

from datetime import time

CHECKED_ON = "2026-10-18"
MARKER = "[US9-CATALOG]"
BADMINTON_SOURCE = "https://psm.tu.ac.th/our-services/facilities-services/sports-center-11/"
SWIMMING_SOURCE = "https://psm.tu.ac.th/our-services/facilities-services/sports-center-13/"
BOOKING_SOURCE = "https://psm.tu.ac.th/booking-court/"
FACILITIES_SOURCE = "https://psm.tu.ac.th/our-services/facilities-services/"


def entry(
    name,
    sport,
    source,
    *,
    start=16,
    end=21,
    days=range(6),
    hours_kind="MOCK",
    venue_kind="REAL",
):
    return {
        "name": name,
        "sport": sport,
        "venue_kind": venue_kind,
        "venue_source": source,
        "hours_kind": hours_kind,
        "hours_source": source if hours_kind == "REAL" else None,
        "checked_on": CHECKED_ON,
        "intervals": tuple((day, time(start), time(end)) for day in days),
    }


def mock_entry(name, sport):
    return entry(
        name,
        sport,
        "Mock data for the map demo; not a verified TU facility.",
        venue_kind="MOCK",
    )


VENUES = (
    entry(
        "สนามแบดมินตัน ยิมเนเซียม 4",
        "แบดมินตัน",
        BADMINTON_SOURCE,
        start=17,
        days=range(7),
        hours_kind="REAL",
    ),
    entry(
        "สนามแบดมินตัน ยิมอินเตอร์โซน",
        "แบดมินตัน",
        BADMINTON_SOURCE,
        days=(0, 1, 2, 3, 4, 6),
        hours_kind="REAL",
    ),
    entry(
        "สระว่ายน้ำ ศูนย์กีฬาทางน้ำ", "ว่ายน้ำ", SWIMMING_SOURCE, start=7, days=range(7), hours_kind="REAL"
    ),
    entry("สนามเทนนิส", "เทนนิส", BOOKING_SOURCE),
    entry("สนามสควอช ยิมเนเซียม 7", "สควอช", BOOKING_SOURCE),
    entry("สนามพิกเคิลบอล", "พิกเคิลบอล", BOOKING_SOURCE),
    entry("สนามบาสเกตบอล", "บาสเกตบอล", FACILITIES_SOURCE),
    entry("สนามฟุตบอลหญ้าเทียม", "ฟุตบอล", FACILITIES_SOURCE),
    entry("สนามฟุตซอล", "ฟุตซอล", FACILITIES_SOURCE),
    entry("สนามซอฟท์บอล", "ซอฟท์บอล", FACILITIES_SOURCE),
    mock_entry("พื้นที่ TU Xtreme — ปีนผาจำลอง", "ปีนผาจำลอง"),
    mock_entry("พื้นที่ TU Xtreme — ปิงปอง", "ปิงปอง"),
)


def location_label(record):
    hours = "REAL (ตามเว็บ PSM)" if record["hours_kind"] == "REAL" else "MOCK (เวลาสมมติ)"
    return (
        f"มธ. ศูนย์รังสิต | {MARKER} สถานที่: {record['venue_kind']}; เวลา: {hours}; "
        f"ตรวจเว็บ {CHECKED_ON}; is_active=ค่าตั้งต้นทดสอบ"
    )
