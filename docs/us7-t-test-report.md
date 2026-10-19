# US7-T — ตรวจรับ Backend สร้าง/แก้ไข/ยกเลิก Party

อ้างอิง [Issue #19](https://github.com/GearJP2/cs261-group2-100001/issues/19),
[US7 API contract](us7-b-api.md) และ [Technical Plan](sprint-1-technical-plan.md)

## ขอบเขตและฐานที่ตรวจ

- วันที่ตรวจ: 20 ตุลาคม 2026
- Branch: `test/us-7-t-edit-cancel` จาก main `43ccdaf` (รวม BASE-03 / PR #41 แล้ว)
- โกลช่วยตรวจข้อมูลและ Backend ของ US7-T-03; ไม่เปลี่ยน production code, schema หรือ migrations
- ใช้ PostgreSQL 17 ผ่าน Docker Compose และฐานทดสอบที่ Django สร้าง/ทำลายแยกจากฐานพัฒนา
- Tests สร้างข้อมูลสมมติของตนเอง ไม่รัน seed ทับข้อมูลพัฒนา และไม่ใช้เลข ID ตายตัว
- Session ใช้ verified identity fixtures; ไม่เรียก TU API จริงหรือยืนยันสิทธิ์นักศึกษาจริง

## Coverage ตาม Issue

| เกณฑ์ | หลักฐาน | ผล |
| --- | --- | --- |
| สร้าง Party: Host จาก session และ active membership หนึ่งรายการ | `test_creation_api.py`, `test_management_api.py`, `test_us7_acceptance.py` | ผ่าน |
| capacity=1 ได้ Full และอีกคนส่งคำขอไม่ได้ โดยไม่ทิ้ง request/membership เพิ่ม | acceptance: `test_capacity_one_is_full_immediately_and_join_cannot_leave_partial_data` | ผ่าน |
| validation ของ required/readonly fields, capacity, เวลา และสนาม | `test_creation.py`, `test_creation_api.py`, `test_management_api.py` | ผ่าน |
| Host membership ล้มเหลวแล้ว rollback Party | creation: `test_membership_failure_rolls_back_party` (จำลอง DB error ที่ service) | ผ่าน |
| session, identity, inactive/logout, CSRF, สิทธิ์ Host | `test_management_api.py` ผ่าน URL จริงและ CSRF middleware | ผ่าน |
| แก้ไขต้องรวมค่าปัจจุบันและตรวจ capacity/schedule; ยกเลิกซ้ำไม่เปลี่ยนเวลา | `test_editing.py`, `test_editing_api.py`, `test_cancellation.py`, `test_cancellation_api.py` | ผ่าน |
| race Edit/Cancel/Join และตรวจข้อมูลล่าสุดหลังรอ Party lock | `test_editing_concurrency.py`, `test_cancellation.py` ใช้ PostgreSQL connections แยกและตรวจ lock wait | ผ่าน |
| สร้างผ่าน API จริง → อีกบัญชีส่ง Pending → Host ลด capacity → Cancel; Pending ไม่กินที่และไม่สูญประวัติ | acceptance: `test_created_party_pending_survives_edit_and_cancel_without_consuming_a_slot` | ผ่าน |

ใช้ tests เดิมสำหรับเกณฑ์ที่มี coverage แล้ว เพิ่มเพียงสอง acceptance tests ใน
`backend/parties/test_us7_acceptance.py` ซึ่งใช้สอง Client แยกบัญชีและเปิด CSRF checks
ตรวจผลทั้ง JSON และข้อมูลที่บันทึกจริง ไม่สร้าง Party ต้นทางด้วย ORM ในสอง flow นี้

กติกาปัจจุบันเก็บ Pending เดิมเมื่อ Party เต็มหรือยกเลิก แต่ปฏิเสธการขอใหม่ตาม state;
การเก็บ Pending นี้ไม่ใช่การอนุมัติหรือเพิ่มสมาชิก และไม่รวม US10

## คำสั่งและผลทดสอบ

```bash
docker compose run --rm -T backend python backend/manage.py test parties.test_us7_acceptance parties.test_creation parties.test_creation_api parties.test_editing parties.test_editing_api parties.test_editing_concurrency parties.test_cancellation parties.test_cancellation_api parties.test_management_api --noinput --verbosity 1
```

ผล: **63 tests ผ่าน ไม่มี skip** รวม acceptance ใหม่ 2 และ tests เดิม 61 กรณี
Django system check ไม่พบปัญหา และฐานทดสอบถูกทำลายหลังจบ

การตรวจทั้งโปรเจกต์เทียบเท่า `make verify` ผ่าน:

- Django system check: ไม่พบปัญหา
- Migration drift: `No changes detected`
- Ruff lint และ format check: ผ่าน (75 Python files)
- Regression ทั้งโปรเจกต์: **276 tests ผ่าน ไม่มี skip** บน PostgreSQL

รันคำสั่งต่อไปนี้ใน backend container ตามลำดับ และหยุดถ้าคำสั่งใดไม่ผ่าน:

```bash
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
ruff check backend scripts
ruff format --check backend scripts
python backend/manage.py test backend --top-level-directory backend --noinput --verbosity 1
```

ไม่ได้รัน smoke ใหม่ เพราะรอบนี้เพิ่มเฉพาะ tests/รายงาน ไม่มีการแก้ runtime หรือหน้าเว็บ

ผลในรายงานนี้เป็นการรัน local บน branch ที่ระบุ ไม่ใช่ผล GitHub Actions ของ PR ใหม่

## งานที่ยังรอ Frontend / E2E

- [ ] ฟอร์มสร้างจริงคงข้อมูลหลัง error และแสดง backend error ถูกฟิลด์
- [ ] ป้องกันกดส่งซ้ำระหว่าง request; สำเร็จแล้วไป Party detail ของ ID ที่ได้รับ
- [ ] เชื่อมเลือกกีฬา/สนาม/เวลา US9 กับหน้าสร้างและแก้ไขจริง
- [ ] Browser flow: สร้าง Party → อีกบัญชีขอเข้าร่วม → Host แก้ไข/ยกเลิก
- [ ] ตรวจ confirm Cancel และ UI ของ non-host/expired session พร้อม browser/commit/ภาพหลักฐาน

API integration ข้างต้นไม่แทนการตรวจผ่านเบราว์เซอร์หรือ TU จริง
PR นี้ใช้ `Refs #19` และยังไม่ปิด Issue ทั้งงานจนกว่าส่วน UI/E2E จะผ่านการตรวจรับ
