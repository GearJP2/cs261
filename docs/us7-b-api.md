# US7 Backend API

US7 รวมสร้าง แก้ไข และยกเลิก Party ตามขอบเขตที่ตกลงล่าสุด แทนข้อเสนอเดิมที่แยกงานสร้างออกไป
ตอนนี้มี Create service และ HTTP handler แต่ยังไม่เปิด route; รอเชื่อม guard จาก US1
PATCH และ Cancel ยังไม่พร้อม

## สร้าง Party

`POST /api/v1/parties` (ไม่มี slash ท้าย) รับ `Content-Type: application/json`
ต้องใช้ university session และ CSRF cookie/header `X-CSRFToken`

จุดเชื่อมที่รอ US1: import และใช้ `require_university_user` ก่อนลงทะเบียน route
จากนั้นทดสอบ university session และ CSRF ผ่าน URL จริง ไม่คัดลอกโค้ด US1 มาใน branch นี้
contract ด้านล่างเป็นพฤติกรรมที่เตรียมไว้สำหรับ integration

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
| 400 | INVALID_INPUT, INVALID_TIME_RANGE, VENUE_CLOSED; อาจมี error.fields |
| 401 | AUTH_REQUIRED |
| 403 | FORBIDDEN, ACCOUNT_INACTIVE, CSRF_FAILED |
| 404 | NOT_FOUND เมื่อไม่พบกีฬา/สนาม |
| 405 | METHOD_NOT_ALLOWED พร้อม Allow: POST |

Tests อยู่ใน `backend/parties/test_creation.py` และ `test_creation_api.py`
ทดสอบการบันทึก/rollback, validation, schedule, request allowlist และ response เทียบ GET
ผ่าน RequestFactory บน PostgreSQL; ยังไม่ได้ทดสอบ Create route, university session หรือ CSRF integration
