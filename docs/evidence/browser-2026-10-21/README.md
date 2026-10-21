# Browser evidence — US8-T / US7-T

ตรวจวันที่ 21 ต.ค. 2026 ด้วย Chrome ใน Codex in-app browser บน Windows
ฐาน source คือ main `b6d4bd0b3d99564b04c0617b3d7c4e7401f044df`
branch `codex/us8-us7-browser-evidence` แก้เฉพาะการคืนค่าเวลาในฟอร์ม Edit
ภาพชื่อ `prefill-missing` เป็นก่อนแก้; `prefill-fixed` เป็นหลังแก้
ยังไม่มี commit/PR ของการแก้รอบนี้ จึงไม่อ้างว่า CI ทดสอบ patch นี้แล้ว

## Environment / fixture

- PostgreSQL 17, Django 5.2.18, Python 3.12 ใน Docker Compose project `cs261-evidence`
- Browser URL `http://localhost:8012`; database `evidence_browser` แยกจากฐานพัฒนา
- `harness/server.py` จำลองเฉพาะคำตอบของ TU ที่ boundary `call_university_api`
  ฟอร์ม Login, CSRF, Django session, database, views/services และ HTML/JS ใช้จริง
- Fixture names: `mock_host`, `mock_viewer`, `mock_empty`, `mock_zero`
  รหัสทดสอบร่วม `fixture-only` เป็นค่าจำลอง ไม่ใช่บัญชีมหาวิทยาลัย
- ไม่เรียก TU จริง ไม่ใช้ Application Key จริง และไม่ถือว่าเป็น provider UAT
- Login สลับสองบัญชีตามลำดับใน Browser เดียว; concurrency ใช้ automated tests

## ตรวจซ้ำอย่างปลอดภัย

ใช้ checkout ทดสอบแยกและสำเนา `.env.example` เป็น `.env` เฉพาะ checkout นั้น
ตั้ง `POSTGRES_DB=evidence_browser`, `APP_PORT=8012`, `POSTGRES_HOST_PORT=5545`,
`DEBUG=true`, `TU_APPLICATION_KEY=` ว่าง และ local-only database credentials
พร้อม SECRET_KEY สำหรับ development ตาม template; ห้ามใช้ฐานพัฒนาหรือฐานจริง
ตัว harness จะหยุดถ้าชื่อฐานไม่ตรงหรือมี TU_APPLICATION_KEY

```bash
docker compose -p cs261-evidence -f docker-compose.yml -f docs/evidence/browser-2026-10-21/harness/compose.evidence.yaml up -d --no-build --wait
```

ต้องมี backend image ที่ build จาก dependencies ของ repository ก่อน (`docker compose build backend`)
fixture seed ทำงานในฐานแยกครั้งเริ่ม harness; ใช้ฐานว่างสำหรับการตรวจรอบใหม่
ทดสอบผ่านหน้า Login → Home → Detail → Host profile และกรณีใน `browser-results.json`

ทำ session fixture หมดอายุ/ปิดใช้งานเพื่อทดสอบ แล้วเปิดกลับ:

```bash
docker compose -p cs261-evidence exec -T backend python /evidence/control.py expire mock_viewer
docker compose -p cs261-evidence exec -T backend python /evidence/control.py inactive mock_viewer
docker compose -p cs261-evidence exec -T backend python /evidence/control.py active mock_viewer
docker compose -p cs261-evidence exec -T backend python /evidence/control.py summary
```

## หลักฐานและข้อจำกัด

- `backend-tests.txt`: 86 tests ผ่านบน PostgreSQL ไม่มี skip
- `browser-results.json`: expected/actual สรุปผล Browser แยกก่อน/หลัง patch
- `http-log.txt`: HTTP status ของการทดสอบ ไม่รวม health checks หรือ credential
- `database-result.json`: หลังทดสอบ Party ที่สร้างผ่าน UI มี Host membership หนึ่งรายการ
  และคำขอของอีกบัญชีเป็น Pending แม้แก้ไข/ยกเลิกแล้ว; ไม่มี Party ซ้ำจาก double-click
- รูป `.jpg`: ผลหน้าเว็บจริง ใช้ข้อมูลจำลองทั้งหมด
- expired/logout/inactive profile ตอบ 401 JSON ไม่ redirect Login อัตโนมัติ ตาม guard ปัจจุบัน
- ไม่ได้ตรวจ Browser network/storage ด้วย DevTools; ใช้ source inspection
  (`app.js` ไม่มี localStorage/sessionStorage) และ automated private-field allowlist tests
- หน้า Profile render HTML จาก Backend; กรณี client-side Profile API retry ไม่ใช้กับหน้านี้
  ไม่จำลอง network outage ของ navigation ทั้ง Browser ในรอบนี้
- การจัดการ native confirm ของเครื่องมือไม่แน่นอน จึงไม่อ้างว่าตรวจ dismiss-Cancel ผ่าน
- หยุด test-only harness เมื่อจบ; ห้ามเปิดบริการนี้ให้เครื่องภายนอก
