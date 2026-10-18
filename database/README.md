# Database

ใช้ PostgreSQL 17 จาก Docker image กลางใน docker-compose.yml โกลเป็นผู้ประสาน schema/migrations ของทีม ดู [คู่มือ development](../docs/development.md)

- Source of truth ของ schema คือ Django ORM และ migrations ใน `backend/<app>/migrations/`
- schema.sql เดิมเป็น placeholder ไม่ถูกรันอัตโนมัติ อย่าสร้าง schema ซ้ำด้วย SQL และ ORM คนละชุด
- BASE-01 มีเฉพาะ custom User และตารางพื้นฐาน Django; Party/Venue/JoinRequest และ seed อยู่ใน task ของเจ้าของ domain
- ERD/data dictionary ของทั้งระบบ (รวมตารางที่ยังไม่สร้าง) อยู่ที่ [docs/base-02-schema-contract.md](../docs/base-02-schema-contract.md) — ตารางรอบ 2–5 เป็นแบบเพื่อรีวิวเท่านั้น อย่าสร้าง migration ก่อน Story นั้นเข้า Sprint
- มุมมองแยกตาม Story (ตารางไหนใช้กับ US ไหน เก็บอะไร ตัวอย่างแถว) พร้อมตารางรวมทุกตารางอยู่ที่ [docs/database-by-story.md](../docs/database-by-story.md) — เป็นเอกสารอ่านประกอบ ไม่ใช่ DDL
- Named volume เก็บข้อมูลข้าม `make down`/`make up`; การลบ volume จะลบข้อมูล
- เครื่องมือ DB บน host ใช้ localhost:5433 ตามค่า POSTGRES_HOST_PORT; app ใน Docker ใช้ database:5432
- Tests สร้างฐาน `test_<POSTGRES_DB>` แยกจากฐานพัฒนา
