# US7 Backend API

US7 รวมสร้าง แก้ไข และยกเลิก Party ตามขอบเขตที่ตกลงล่าสุด แทนข้อเสนอเดิมที่แยกงานสร้างออกไป
เปิด Create/Edit/Cancel routes แล้ว โดยใช้ `accounts.decorators.require_university_user` จาก US1
POST/PATCH ต้องผ่าน Django CSRF middleware และ university session guard

## สร้าง Party

`POST /api/v1/parties` (ไม่มี slash ท้าย) รับ `Content-Type: application/json`
ต้องใช้ university session และ CSRF cookie/header `X-CSRFToken`

Create/Edit/Cancel ใช้ guard จาก US1 ที่ merge แล้ว ไม่มีการคัดลอกหรือสร้าง guard ใหม่
GET รายละเอียดและ US3 คงใช้ guard เดิมของงานนั้น
รับ CSRF token จาก `GET /api/v1/auth/csrf` และใช้ cookie/session เดียวกัน

```json
{
  "title": "Badminton practice",
  "description": "",
  "sport_id": 1,
  "venue_id": 1,
  "starts_at": "2030-01-07T09:00:00+07:00",
  "ends_at": "2030-01-07T10:00:00+07:00",
  "capacity": 6
}
```

ทุกฟิลด์จำเป็นยกเว้น description ซึ่ง default เป็นข้อความว่าง
ปฏิเสธ unknown/read-only fields รวม host_id, user_id, state และ cancelled_at
Host มาจาก session เท่านั้น วันที่ต้องเป็น ISO 8601 พร้อม T และ timezone offset หรือ Z
ชื่อถูกตัดช่องว่างหัวท้ายและยาวไม่เกิน 150; description ไม่เกิน 2,000; capacity เป็น integer ≥ 1
รวม Host และไม่รับ boolean เวลาเริ่มต้องอยู่ในอนาคตและสิ้นสุดหลังเริ่ม

ตรวจสนาม active และรองรับกีฬา; นัดอยู่วันเดียวตาม Asia/Bangkok และครบในช่วงเปิดหนึ่งช่วง
อนุญาตเริ่มตรงเวลาเปิด/จบตรงเวลาปิด ไม่อนุญาตคร่อมพักหรือข้ามวัน

สร้าง Party และ active Host membership ใน transaction เดียว หาก membership ล้มเหลวจะ rollback Party
สำเร็จคืน 201 `{"data": {...}}` ใช้ Party fields เดียวกับ GET รายละเอียด
member_count เริ่มที่ 1, remaining_slots = capacity − 1, is_host/is_member เป็น true
capacity = 1 จะมี state Full

| HTTP | Error |
| --- | --- |
| 400 | INVALID_INPUT, INVALID_TIME_RANGE, VENUE_CLOSED, INVALID_OPENING_HOURS; อาจมี error.fields |
| 401 | AUTH_REQUIRED |
| 403 | FORBIDDEN, ACCOUNT_INACTIVE, CSRF_FAILED |
| 404 | NOT_FOUND เมื่อไม่พบสนามหรือสนาม inactive; กีฬาไม่มีอยู่คืน 400 INVALID_INPUT ตาม US9 |
| 405 | METHOD_NOT_ALLOWED พร้อม Allow: POST |

Tests อยู่ใน `backend/parties/test_creation.py` และ `test_creation_api.py`
ทดสอบการบันทึก/rollback, validation, schedule, request allowlist และ response เทียบ GET
ผ่าน RequestFactory บน PostgreSQL; HTTP/session/CSRF integration อยู่ใน test_management_api.py

## Cancel service

`cancel_party(party_id=..., user=...)` รับ trusted user จาก caller หลังผ่าน auth
เปิด transaction และล็อก Party ก่อนตรวจ Host; ไม่พบคืน PartyError NOT_FOUND (404)
ไม่ใช่ Host คืน FORBIDDEN (403) แม้ Party ยกเลิกแล้ว
ถ้ายกเลิกแล้วคืน Party เดิมโดยไม่แก้ cancelled_at/updated_at
ครั้งแรกอ่านเวลาหลังได้ lock และต้องก่อน starts_at มิฉะนั้น PARTY_STARTED (409)
Party เต็มยังยกเลิกได้ บันทึก cancelled_at และ updated_at โดยเก็บ membership/request ไว้
ทดสอบด้วย `test_cancellation.py` รวม PostgreSQL lock wait และยกเลิกพร้อมกัน
เชื่อม university guard และ route แล้ว

## Cancel API

`POST /api/v1/parties/{id}/cancel` รับ application/json body `{}` เท่านั้น
ไม่รับ client-selected actor/status หรือข้อมูลอื่น สำเร็จคืน 200
`{"data":{"id":1,"state":"Cancelled","cancelled_at":"..."}}`
เรียกซ้ำคืน timestamp เดิม ผิด method คืน 405 พร้อม Allow: POST
ผิด body คืน INVALID_INPUT (400); service errors ใช้ code/status เดิม
Tests ใน `test_cancellation_api.py` เรียก handler ผ่าน RequestFactory เท่านั้น
ทดสอบ session/CSRF ผ่าน URL จริงใน test_management_api.py

## Edit service

`edit_party(party_id=..., user=..., changes={...})` รับ trusted user และ parsed datetimes
ล็อก Party ใน transaction ก่อนตรวจ Host; ไม่พบ NOT_FOUND (404), ไม่ใช่ Host FORBIDDEN (403)
ตรวจสถานะเดิมก่อนรวมค่า: Cancelled ให้ PARTY_CANCELLED (409), เริ่มแล้วให้ PARTY_STARTED (409)
จึงไม่สามารถเลื่อนเวลาเพื่อเปิด Party ที่เริ่มแล้วกลับมาแก้ได้

รับเฉพาะ title/description/sport_id/venue_id/starts_at/ends_at/capacity
รวมค่ากับ Party เดิมแล้วตรวจ validation และ schedule ชุดเดียวกับ Create
capacity ต่ำกว่า active memberships ให้ CAPACITY_TOO_SMALL (409); Pending ไม่จองที่
Party เต็มยังแก้ได้ การแก้ไม่ลบ membership/request; changes ว่างตรวจข้อมูลแต่ไม่เขียน updated_at
Tests ใน test_editing.py; เชื่อม PATCH handler, guard และ route แล้ว

## Edit API

`PATCH /api/v1/parties/{id}` รับ application/json object เฉพาะฟิลด์ที่อนุญาต
ไม่บังคับส่งทุกฟิลด์ และไม่เติม default ให้ฟิลด์ที่ไม่ได้ส่ง; `{}` เป็น no-op เมื่อข้อมูลเดิมยังผ่าน validation
starts_at/ends_at ที่ส่งต้องเป็น ISO 8601 พร้อม T และ timezone เช่นเดียวกับ Create
handler ใช้ datetime parser ร่วมกับ Create แล้วส่ง changes ไป Edit service
สำเร็จคืน 200 พร้อม Party data ชุดเดียวกับ GET; error ใช้ status/code/fields จาก service
Tests ใน test_editing_api.py เรียก handler ผ่าน RequestFactory
party_detail ส่ง PATCH ไป edit_party_api ที่ใช้ university guard; GET ยังใช้สิทธิ์เดิม
method อื่นที่ path รายละเอียดคืน 405 พร้อม Allow: GET, PATCH

## Edit concurrency tests

`test_editing_concurrency.py` ใช้ TransactionTestCase และ PostgreSQL connections แยกจริง
ตรวจ `pg_backend_pid() = ANY(pg_blocking_pids(worker_pid))` เพื่อยืนยันว่า worker
รอ Party lock ของ transaction หลัก มี lock timeout และ future/queue timeout ป้องกันค้าง

ครอบคลุม Cancel commit ก่อน Edit (ปฏิเสธ) และ Edit commit ก่อน Cancel (คงค่าที่แก้),
Edit ลดความจุจนเต็มก่อน Join (ปฏิเสธ) และ Join commit ก่อน Edit (Pending เดิมยังอยู่),
partial edits พร้อมกันรวมข้อมูลล่าสุดโดยไม่ทับฟิลด์ที่ไม่ได้ส่ง,
อ่านนาฬิกาหลังได้ lock และตรวจจำนวนสมาชิกที่ commit ระหว่างรอใหม่
กรณีสมาชิกเพิ่มจำลอง writer ที่ล็อก Party ก่อนตามสัญญา ไม่ใช่ implementation ของ US10
เป็น service concurrency tests ไม่รวม HTTP/auth integration

## HTTP integration หลัง US1 merge

`test_management_api.py` ใช้ Django Client(enforce_csrf_checks=True) ผ่าน URL จริง
รับ token จาก endpoint US1 ใช้ university session fixtures ที่ผูกกับ identity จริงในฐานทดสอบ
ครอบคลุม Create → GET → Edit → Cancel → ยกเลิกซ้ำ และ US3 ขอหลัง Cancel,
anonymous/local-only session, identity ข้าม user/ถูกลบ, inactive/logout,
CSRF ขาด/ผิด/origin ไม่เชื่อถือ, non-host, readonly fields, schedule และ 404/405
ไม่ได้เรียก TU API จริงหรือยืนยันการใช้งาน Frontend

## การเชื่อม US9

ใช้ `validate_party_schedule` และ `ScheduleValidationError` จาก `venues.services`
ตาม [US9 API contract](us9-b2-api.md) ที่รวมผ่าน PR #46
ไม่มี validator แยกของ US7; Create/Edit เรียก service โดยตรงใน transaction ก่อนบันทึก
Edit รวมค่าที่ส่งกับข้อมูลเดิมก่อนตรวจ แม้เปลี่ยนเพียง venue_id ก็ต้องส่งกีฬาและเวลาเดิมครบ
`ScheduleValidationError` ถูกแปลงเป็น `PartyError` โดยคง code/message/status/fields
แล้ว handler ใช้ `json_error` คืน JSON envelope เดียวกัน

| กรณีจาก US9 | HTTP / code |
| --- | --- |
| ID ผิดรูปแบบ กีฬาไม่มีอยู่ หรือสนามไม่รองรับกีฬา | 400 INVALID_INPUT |
| ช่วงเวลาไม่ถูกต้องหรือข้ามวันตามเวลาไทย | 400 INVALID_TIME_RANGE |
| ไม่พบสนามหรือสนาม inactive | 404 NOT_FOUND |
| วันปิด นอกเวลา หรือคร่อมช่วงพัก | 400 VENUE_CLOSED |
| ตารางเวลาเปิดของวันนั้นซ้อนกัน | 400 INVALID_OPENING_HOURS |

ทั้งช่วงนัดต้องอยู่ในหนึ่งช่วงเปิด แม้สองช่วงเปิดติดกันก็ไม่นำมารวม
ตัวตรวจไม่ใช่ระบบจองสนาม และไม่รวมวันหยุดพิเศษ/นัดข้ามเที่ยงคืน
เวลาเริ่มในอนาคต สิทธิ์ Host ความจุ และสถานะ Party เป็นกฎของ US7
ยังไม่มี lock ร่วมกับการแก้ configuration สนาม ตามข้อจำกัด US9

## สถานะตรวจความพร้อม Backend — 19 ตุลาคม 2026

รวม US1 และ US9 แล้วผ่าน merge commit `a701306` มี Create/Edit/Cancel APIs,
Host authorization, atomic Host membership และ Party lock พร้อม service/HTTP/concurrency tests
พร้อมส่ง review ฝั่ง Backend; ยังไม่ถือว่า US7 ทั้ง Story ผ่านการตรวจรับ Frontend

หลักฐานตรวจที่รันแล้ว:

- รอบ merge `a701306`: Ruff lint/format ผ่าน และ regression 200 tests ผ่าน เมื่อรัน
  `parties core venues accounts.tests accounts.test_profile_api`
- หลังเพิ่ม US7–US9 integration อีก 4 เคส: `parties.test_management_api` ผ่าน 12 tests
  บน PostgreSQL และ Ruff lint ผ่าน; ยังไม่ได้รัน regression ทั้งชุดซ้ำหลังเพิ่มสี่เคสนี้
- tests ใหม่ตรวจอ่าน sports → venues → opening-hours แล้วนำค่าตอบกลับมาสร้าง/แก้ Party,
  เปลี่ยนเฉพาะสนามต้องตรวจเวลาเดิม, เปลี่ยนสนามพร้อมเวลาใหม่ผ่าน,
  ตารางเปิดซ้อนกันต้องไม่บันทึก และกีฬาไม่มีอยู่/สนาม inactive คืน error ตาม US9
- รอบ US1 integration ก่อนหน้า: Django check และ migration drift ผ่าน
- ผล full backend run รอบก่อนหน้าติด 8 errors ใน `accounts.test_profile_acceptance`
  เพราะอ้าง `reverse("user-public-profile")` แต่ accounts URLs ใช้ namespace
  `accounts:user-public-profile`; ไม่แก้โค้ด/tests ของ US8 ในงานนี้ และไม่อ้างว่า full suite ผ่าน

งานที่ยังต้องตรวจร่วมกับทีม:

- Frontend เรียกสาม APIs ด้วย session/CSRF จริง รวม form errors และยืนยัน Cancel
- เชื่อมรายการสนาม/เวลาเปิดของ US9 กับฟอร์มจริง; Backend ใช้ service กลางแล้ว
- การเรียก TU API จริงเป็นการตรวจรับ US1 แยกจาก university session fixtures ของ US7
- ส่ง PR/review และจัดการ US8 test namespace ก่อนให้ CI ทั้งชุดผ่าน

สถานะใน Sprint checklist ยังไม่ติ๊ก Done เพราะรวม review และการเชื่อม Frontend ด้วย
