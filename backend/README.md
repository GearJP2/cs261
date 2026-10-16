# Backend

ใช้ Django apps ใน `accounts/`, `core/`, `venues/` และ `parties/` พร้อม config กลางใน `config/` รันและทดสอบผ่าน Docker ตาม [คู่มือ development](../docs/development.md)

```bash
make up
make verify
```

รันจาก root repository; Python dependencies อยู่ใน requirements.in และ requirements.txt ที่ล็อกเวอร์ชัน/hashes ใช้ `settings.AUTH_USER_MODEL` สำหรับ FK และ `get_user_model()` แทน import built-in User โดยตรง

สร้าง app ใหม่และเพิ่ม INSTALLED_APPS เมื่อเริ่ม domain ถัดไป โดยประสานเจ้าของ schema ก่อน โฟลเดอร์ controllers/routes/services/models/utils เดิมเป็น placeholder; Django ใช้ไฟล์ภายใน app ที่ลงทะเบียนเท่านั้น

## BASE-04 — JSON API รายละเอียด Party

ใช้ Django views และ `JsonResponse` โดยไม่เพิ่ม Django REST Framework หรือ root-level `apps/` ดู contract, ขอบเขต session guard และวิธีตรวจใน [BASE-04 API](../docs/base-04-api.md)

## US3-B — ส่งและอ่านคำขอเข้าร่วม Party

เพิ่ม API ส่ง Pending และอ่านคำขอของผู้ใช้จาก session โดยใช้ Party lock และ unique constraint เดิม รองรับการขอใหม่หลัง Rejected/ถอนตัวตาม schema contract ล่าสุด ดู [US3-B API](../docs/us3-b-api.md) สำหรับ request/response, CSRF, error codes และข้อจำกัดที่ยังรอ US1
