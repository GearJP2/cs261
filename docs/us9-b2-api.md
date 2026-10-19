# US9-B2 — Venue API และ schedule validation

ใช้ Django JSON views และ schema เดิมของ US9-B1 ไม่มี migration ใหม่
ทุก endpoint ต้องมี session ที่ผ่าน `accounts.decorators.require_university_user` ของ US1
ใช้ URL ไม่มี slash ท้าย และรองรับเฉพาะ GET (method อื่นตอบ 405 พร้อม Allow: GET)

| Endpoint | Response |
| --- | --- |
| `GET /api/v1/sports` | `{"data":[{"id":1,"name":"แบดมินตัน"}]}` เรียง id |
| `GET /api/v1/venues?sport_id=1&page=1&page_size=20` | `{"data":[{"id":2,"name":"สนาม","location_text":"..."}],"page":1,"page_size":20,"total":1}` |
| `GET /api/v1/venues/2/opening-hours` | `{"data":{"venue_id":2,"timezone":"Asia/Bangkok","intervals":[{"weekday":0,"opens_at":"09:00:00","closes_at":"12:00:00"}]}}` |

ตัวเลขเป็นตัวอย่าง ห้ามผูก client/tests กับ seed ID
รายการสนามแสดงเฉพาะ active ที่รองรับกีฬา เรียง id; location_text คงป้าย REAL/MOCK จาก seed
sport_id จำเป็น; ID/page/page_size ต้องเป็นเลขจำนวนเต็มบวกในช่วงที่รองรับ
page เริ่มที่ 1, page_size default 20 สูงสุด 100; query ซ้ำของฟิลด์เหล่านี้ตอบ 400
กีฬาไม่มีอยู่หรือไม่มีสนามได้รายการว่าง; หน้าที่เกินรายการได้ data ว่างและ total เดิม
สนามไม่มีอยู่หรือ inactive ที่ opening-hours ตอบ 404; สนามไม่มีช่วงเปิดได้ intervals ว่าง
intervals เรียง weekday แล้ว opens_at; weekday 0=จันทร์ ถึง 6=อาทิตย์ ไม่มีแถวคือปิด
ทุก response ปิด cache ตาม pattern ของ API เดิม

Errors ใช้ `{"error":{"code":"...","message":"...","fields":{...}}}` โดย fields เป็น optional:
401 AUTH_REQUIRED, 403 ACCOUNT_INACTIVE/FORBIDDEN, 400 INVALID_INPUT, 404 NOT_FOUND, 405 METHOD_NOT_ALLOWED

## Contract สำหรับผู้ทำสร้าง/แก้ Party

Import `validate_party_schedule` และ `ScheduleValidationError` จาก `venues.services`
เรียก service ตรงภายใน Django backend ไม่ต้องเรียก HTTP เพื่อ validate

```python
from core.api import json_error
from venues.services import ScheduleValidationError, validate_party_schedule

# Parse ISO 8601 request timestamps into aware datetime objects first.
# On PATCH, merge supplied fields with the existing Party before validation.
try:
    validate_party_schedule(sport_id, venue_id, starts_at, ends_at)
except ScheduleValidationError as error:
    return json_error(error.code, error.message, error.status, error.fields)
# Persist only after successful validation, inside the writer's transaction.
```

Input: sport_id/venue_id เป็น positive int (ไม่รับ bool/string); starts_at/ends_at เป็น aware datetime
ผลสำเร็จคืน None ไม่มีการเขียนฐานข้อมูลหรือเปลี่ยน input
ตัวตรวจแปลงเวลาเป็น Asia/Bangkok ก่อนตรวจวัน/เวลา เริ่มต้องก่อนจบและเป็นวันเดียวกัน
ต้องอยู่ครบภายในหนึ่งช่วงเปิด เริ่มตรง opens_at และจบตรง closes_at ได้
ห้ามคร่อมช่วงพักหรือรวมหลายช่วง แม้ช่วงติดกัน; ตรวจความละเอียดระดับ microsecond
ตรวจ active venue และ VenueSport mapping เสมอ จึงต้องส่งทั้งสี่ค่าทุกครั้งรวมกรณีแก้สนามอย่างเดียว

| code | status | เหตุผล |
| --- | --- | --- |
| INVALID_INPUT | 400 | ID ผิดรูปแบบ/สนามไม่รองรับกีฬา (รวมกีฬาไม่มีอยู่) |
| INVALID_TIME_RANGE | 400 | ไม่ใช่ aware datetime, เริ่มไม่ก่อนจบ หรือข้ามวัน Bangkok |
| NOT_FOUND | 404 | สนามไม่มีอยู่หรือ inactive |
| VENUE_CLOSED | 400 | วันปิด/นอกเวลา/คร่อมช่วงพัก |
| INVALID_OPENING_HOURS | 400 | ช่วงเปิดของวันนัดซ้อนกัน ให้ผู้ดูแลแก้ configuration |

ตัวตรวจไม่แก้ตารางที่ซ้อนกัน ไม่เพิ่ม API จัดการ configuration และไม่รวมการตรวจการจอง/สนามว่าง
ไม่ตรวจเวลาในอดีต, Host, capacity หรือสถานะ Party; เป็นหน้าที่ service ผู้เขียน
ยังไม่รวมวันหยุดพิเศษ VenueClosure และนัดข้ามเที่ยงคืน
บริการเขียนต้องจัดการ transaction/Party lock และเรียก validator ก่อนบันทึก
การแก้ configuration พร้อมการเขียน Party ยังไม่มีระบบ lock ร่วมในงานนี้

## ขอบเขตส่งต่อและตรวจรับ

branch นี้เพิ่มสาม read endpoints และ shared service พร้อม tests ไม่เพิ่ม endpoint สร้าง/แก้ Party
ฝั่งสร้าง/แก้ Party อยู่ backend เดียวกันและต้องเชื่อม service นี้ในงานของตน
ไม่ถือว่าการมี validator เท่ากับตรวจ integration ของบริการเหล่านั้นแล้ว

รัน `make verify` เพื่อตรวจ Django, migration drift, Ruff และ backend tests บน PostgreSQL
Tests ของ `venues.test_api_schedule` สร้าง fixtures เอง ไม่ต้องรัน seed

ผลตรวจ local วันที่ 19 ตุลาคม 2026:
- Django system check และ migration drift ผ่าน (No changes detected)
- Ruff lint/format ผ่าน
- ชุด venues ล่าสุดผ่าน 28 tests (รวม API/schedule ใหม่ 9 tests)
- `make verify` รอบแรกทดสอบ 155 tests มี error 8 กรณีใน
  `accounts.test_profile_acceptance`: reverse ชื่อ `user-public-profile` ไม่พบ
  เพราะ accounts URL มี namespace; HEAD เดิมมี namespace นี้อยู่แล้ว
  อีก 147 tests ผ่าน งานนี้ไม่แก้ namespace/tests ของ US8
- สอง tests ขอบเขตเพิ่มเติมตรวจแล้วในชุด venues ข้างต้น
- ยังไม่ได้ทดสอบ integration กับ service สร้าง/แก้ Party ของผู้รับงาน
