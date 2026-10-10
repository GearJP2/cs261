# Migrations

ไฟล์ migration ที่รันจริงอยู่ใน `backend/<app>/migrations/` ใช้ `make migrations` หลังแก้ model และ `make migrate` เพื่อ apply โดยประสานโกลก่อนแก้ schema ที่หลาย task ใช้ร่วมกัน

โฟลเดอร์นี้เป็นจุดอ้างอิงเอกสาร ไม่ใช่ตำแหน่งสำหรับ SQL migrations อีกชุด `make check` ตรวจว่ามี model changes ที่ยังขาด migration หรือไม่
