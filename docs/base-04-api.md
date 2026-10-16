# BASE-04 — Party detail JSON API

ใช้ Django JSON views และ `JsonResponse` ตาม framework decision ของทีม ไม่มี DRF, serializer dependency หรือโมเดลชุดใหม่ โค้ดอ่านโมเดลและ migrations ของ BASE-02 ใน `backend/` โดยตรง

## ขอบเขตที่เพิ่ม

- `backend/core/api.py`: `json_error` และ `require_authenticated_api` สำหรับ JSON API
- `backend/parties/services.py`: `count_active_members(party)` และ `get_party_state(party, now=None, *, member_count=None)` ให้ฟีเจอร์ Party ใช้ร่วมกัน ค่า `member_count` ที่ส่งเข้าต้องเป็นจำนวน active memberships จากฐานข้อมูล ไม่รับจาก client
- `backend/parties/views.py` / `urls.py`: API-02 อ่านรายละเอียด Party และเชื่อมผ่าน `backend/config/urls.py`
- tests ใช้ Django test database และสร้างข้อมูลจริงผ่าน ORM; ไม่มี mock-success endpoint หรือ seed บัญชีมหาวิทยาลัย

## Endpoint และ response

`GET /api/v1/parties/{party_id}` ใช้ ID จำนวนเต็ม ไม่มี slash ท้าย ต้องมี session ของบัญชี local ที่ใช้งานได้

สำเร็จตอบ HTTP 200:

```json
{
  "data": {
    "id": 12,
    "title": "Badminton after class",
    "description": "เล่นแบดมินตัน 2 ชั่วโมง",
    "host": {"id": 7, "display_name": "Gear"},
    "sport_id": 1,
    "venue_id": 2,
    "starts_at": "2026-10-20T17:00:00+07:00",
    "ends_at": "2026-10-20T19:00:00+07:00",
    "capacity": 4,
    "member_count": 1,
    "remaining_slots": 3,
    "state": "Open",
    "is_host": false,
    "is_member": false
  }
}
```

ตัวเลขและเวลาในตัวอย่างเป็นเพียงคำอธิบาย contract; endpoint อ่านฐานข้อมูลจริงเสมอ

- นับสมาชิกจาก `PartyMembership.left_at IS NULL` รวม Host เมื่อมี active membership; ไม่เพิ่ม Host เข้า count เองและไม่นับ JoinRequest
- `remaining_slots = capacity - member_count` การป้องกันสมาชิกเกิน capacity เป็นหน้าที่ของบริการเขียนข้อมูล
- สถานะเรียก service กลางตามลำดับ Cancelled → Completed → InProgress → Full → Open; ที่ `starts_at` ถือว่าเริ่ม และที่ `ends_at` ถือว่าจบแล้ว ใช้ count เดียวกับ response
- `is_host` / `is_member` ใช้ `request.user` เท่านั้น query/body ไม่เปลี่ยนตัวผู้กระทำ
- วันเวลาส่งแบบ ISO 8601 พร้อม offset ตาม timezone ของแอป (`Asia/Bangkok`)
- ส่งเฉพาะฟิลด์ในตัวอย่าง ไม่ส่ง username, email, password hash, provider identity, token หรือ session
- ถ้า Host ไม่มี UserProfile ใช้ข้อความกลาง “ผู้จัดกิจกรรม” เพื่อรองรับบัญชี local/ข้อมูลเดิมโดยไม่เปิดเผย login identifier; ไม่สร้าง profile ให้ระหว่าง GET
- response มี `Cache-Control` ป้องกันการเก็บผลที่ขึ้นอยู่กับผู้ใช้ไว้ใน cache

## Error contract

```json
{"error": {"code": "NOT_FOUND", "message": "ไม่พบกิจกรรมที่ต้องการ"}}
```

| HTTP | code | กรณี |
| --- | --- | --- |
| 401 | AUTH_REQUIRED | ไม่มีผู้ใช้ที่ผ่าน authentication จาก session |
| 403 | ACCOUNT_INACTIVE | guard ได้รับ authenticated user ที่ `is_active=False` |
| 404 | NOT_FOUND | ผู้ใช้ผ่าน guard แต่ไม่พบ Party ID |
| 405 | METHOD_NOT_ALLOWED | ผู้ใช้ผ่าน guard แต่ใช้ method อื่น; ส่ง `Allow: GET` |

`json_error` รองรับ `fields` เมื่อจำเป็นต้องส่งข้อผิดพลาดรายฟิลด์ด้วย URL ที่ไม่ตรง routing เช่น ID ที่ไม่ใช่จำนวนเต็มยังเป็น Django routing 404 ปกติ

CSRF middleware เดิมยังทำงาน ไม่มี `csrf_exempt` คำขอ unsafe ที่ไม่ผ่าน CSRF อาจถูกปฏิเสธก่อนเข้า view; US3-B เพิ่ม failure handler ให้ `/api/v1/` ตอบ JSON `403 CSRF_FAILED` แล้ว ส่วนหน้า HTML/admin ใช้ response ของ Django ตามเดิม ดู [US3-B API](us3-b-api.md)

## ส่วนที่ยังรอ US1 และงานอื่น

guard นี้เป็น local session guard ตามตัวอย่างในรีวิว ไม่ตรวจ provider หรือสิทธิ์นักศึกษา และไม่ใช้การมี timestamp ใน UniversityIdentity เป็นหลักฐานแทน eligibility policy ต้องเชื่อม guard/policy ของ US1 ก่อนถือว่าเป็นระบบที่จำกัดเฉพาะนักศึกษาและปิด integration ของ BASE-04

Django ModelBackend ปัจจุบันไม่คืน inactive user จาก session: เมื่อปิดบัญชี session เดิมจะถูกมองเป็น anonymous และ API ตอบ 401 ส่วน 403 ทดสอบตรง guard เมื่อ `request.user` เป็น inactive user จริง ไม่เปลี่ยน authentication backend เพียงเพื่อบังคับ status code; ให้ทีม US1 ตกลงพฤติกรรมนี้ใน policy กลาง

งานนี้ไม่เพิ่ม Login/Logout, `/api/v1/me`, หน้า HTML `/parties/{id}` (BASE-04-02), การสร้าง/แก้ไข/เข้าร่วม/อนุมัติ Party หรือ API โปรไฟล์

## ตรวจงาน

รันจาก root repository:

```bash
make verify
make up
make smoke
```

Tests ใหม่ตรวจ JSON helper, guard anonymous/inactive/active, URL จริงผ่าน session, response allowlist, การปลอม user_id/host_id, membership ปัจจุบัน/ถอนตัว/Pending/Rejected, Party ไม่พบ, Host ไม่มี profile, method ที่ไม่อนุญาต, session ที่ยกเลิก/บัญชีถูกปิด, จำนวนที่ว่าง และลำดับสถานะรวมขอบเขตเวลา โดยไม่ถือว่า tests ของ local session เป็นการเชื่อมมหาวิทยาลัยสำเร็จ

## ผลตรวจ local วันที่ 14 ตุลาคม 2026

- `make verify` ผ่าน: Django system checks, ไม่มี model change ที่ขาด migration, Ruff lint/format และ tests 40 กรณีบน PostgreSQL (เพิ่มใหม่ 12 กรณี)
- `make up` ผ่าน: backend/database healthy และใช้ migrations เดิมของ BASE-02
- `make smoke` ผ่าน: หน้าแรก, static CSS, liveness และ database readiness
- เรียก `GET /api/v1/parties/1` ผ่าน HTTP จริงโดยไม่มี session ได้ 401 พร้อม JSON `AUTH_REQUIRED`
- ผลเหล่านี้เป็น local checks ไม่ใช่ผล GitHub Actions หรือ UAT ของระบบมหาวิทยาลัย
