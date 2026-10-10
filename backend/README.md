# Backend

ใช้ Django apps ใน `accounts/` และ `core/` พร้อม config กลางใน `config/` รันและทดสอบผ่าน Docker ตาม [คู่มือ development](../docs/development.md)

```bash
make up
make verify
```

รันจาก root repository; Python dependencies อยู่ใน requirements.in และ requirements.txt ที่ล็อกเวอร์ชัน/hashes ใช้ `settings.AUTH_USER_MODEL` สำหรับ FK และ `get_user_model()` แทน import built-in User โดยตรง

สร้าง app ใหม่และเพิ่ม INSTALLED_APPS เมื่อเริ่ม domain ถัดไป โดยประสานเจ้าของ schema ก่อน โฟลเดอร์ controllers/routes/services/models/utils เดิมเป็น placeholder; Django ใช้ไฟล์ภายใน app ที่ลงทะเบียนเท่านั้น
