# US3-B — Pending join requests

พัฒนาบน branch `feat/us-3-b-join-requests` ซึ่งเริ่มงานที่ commit `f93b169` ตรงกับ `origin/main` หลัง fetch วันที่ 16 ตุลาคม 2026 มี BASE-01/02/04 แล้ว ใช้ Django JSON views, โมเดลและ migrations เดิม ไม่เพิ่ม DRF, dependency หรือ environment variable

อ้างอิง [Technical Plan](sprint-1-technical-plan.md) API-06/07 และ [Schema Contract](base-02-schema-contract.md) หัวข้อ 4.1.1 ซึ่งยืนยันให้ Rejected/ผู้ถอนตัวขอใหม่ได้ตั้งแต่ 14 ตุลาคม 2026

## API

### POST /api/v1/parties/{party_id}/join-requests

ใช้ ID จำนวนเต็ม ไม่มี slash ท้าย ส่ง `Content-Type: application/json` และ body `{}` (ยอมรับ body ว่างด้วย) พร้อม session cookie และ `X-CSRFToken` ที่ถูกต้อง ไม่รับฟิลด์อื่นใน body เช่น user_id, host_id, party_id หรือ status; query string ไม่เปลี่ยนผู้กระทำ ซึ่งใช้ `request.user` เท่านั้น

สร้างใหม่หรือเปิดคำขอเดิมเป็น Pending สำเร็จตอบ HTTP 201:

```json
{"data":{"id":45,"party_id":12,"status":"Pending","created_at":"2026-10-16T17:00:00+07:00"}}
```

ตัวเลขและเวลาเป็นตัวอย่าง endpoint อ่าน/เขียนฐานข้อมูลจริง ไม่เพิ่ม membership และไม่เปลี่ยน capacity

### GET /api/v1/parties/{party_id}/join-requests/me

ใช้ session เดียวกันเพื่ออ่านเฉพาะคำขอของตัวเองใน Party ที่ระบุ ตอบ HTTP 200:

```json
{"data":{"id":45,"status":"Pending","created_at":"2026-10-16T17:00:00+07:00"}}
```

ยังไม่เคยขอคืน `{"data":null}`; status อาจเป็น Pending/Approved/Rejected อ่านได้แม้ Party เต็ม/เริ่ม/จบ/ยกเลิก เพื่อให้หน้าเว็บโหลดสถานะล่าสุด ไม่ส่ง user/provider identity หรือข้อมูลผู้ตัดสินออกไป

GET นี้ออก CSRF cookie ผ่าน `ensure_csrf_cookie` สำหรับหน้า frontend ที่ยังไม่มี cookie ให้อ่านค่า `csrftoken` และส่งกลับใน header `X-CSRFToken` เมื่อ POST ภายใต้ origin เดียวกัน ทั้งสอง endpoint ห้าม cache response ที่ขึ้นกับผู้ใช้

## Transaction และกติกาส่งซ้ำ

`submit_join_request(party_id=..., user=...)` ใน `backend/parties/services.py` ต้องถูกเรียกหลัง shared guard ตรวจผู้ใช้แล้ว:

1. เปิด `transaction.atomic` และ `SELECT FOR UPDATE` แถว Party ก่อนอ่านสถานะ
2. อ่านเวลาปัจจุบันหลังได้ lock แล้ว เพื่อไม่ใช้เวลาค้างระหว่างรอ
3. ตรวจ state ผ่าน service กลาง: ยกเลิก → เริ่ม/จบ → เต็ม ก่อนตรวจ Host/active membership
4. ล็อกคำขอเดิมเมื่อมี และใช้ unique `(party,user)` จาก BASE-02 เป็นข้อบังคับฐานข้อมูล
5. ไม่มีคำขอ: สร้าง Pending; Pending เดิม: 409 REQUEST_EXISTS
6. Rejected เดิม: ใช้แถวเดิมกลับเป็น Pending; Approved เดิม: ทำได้เมื่อมี membership ที่ถอนตัวแล้วเท่านั้น
7. การเปิดคำขอใหม่ตั้ง created_at ใหม่ ล้าง decided_at/decided_by แต่ไม่เปิด membership กลับเอง ต้องรอ Host อนุมัติใน US10

เก็บเฉพาะรอบล่าสุดตาม schema contract ไม่เพิ่มตารางประวัติ ถ้าพบ Approved แต่ไม่มีหลักฐาน membership ที่ถอนตัว จะคืน REQUEST_DECIDED โดยไม่รีเซ็ตคำขอ

คนเดียวส่งพร้อมกันได้สำเร็จหนึ่งครั้ง อีกคำขอเป็น conflict; คนละคนขอเมื่อเหลือหนึ่งที่ได้ Pending ทั้งคู่ เพราะ Pending ไม่จองที่

บริการยกเลิก/แก้ไข/อนุมัติ/ถอนตัวต้องล็อก Party ก่อน request/membership เช่นเดียวกัน หากยกเลิก commit ก่อน การขอถูกปฏิเสธ; หากส่งคำขอ commit ก่อน ยกเลิกทีหลังได้โดยยังเก็บ Pending ไว้ การป้องกันอนุมัติบน Party ที่ปิดแล้วเป็นงาน US10

## Errors

ใช้ `{"error":{"code":"...","message":"..."}}` ผ่าน helper ของ BASE-04:

| HTTP | code | กรณี |
| --- | --- | --- |
| 400 | INVALID_INPUT | JSON ผิด, ไม่ใช่ object ว่าง, มีฟิลด์ที่ไม่รับ หรือ body ที่ไม่ใช่ application/json |
| 401 | AUTH_REQUIRED | ไม่มี session ที่ใช้ได้ |
| 403 | ACCOUNT_INACTIVE | shared guard ได้รับ authenticated inactive user |
| 403 | CSRF_FAILED | POST ไม่ผ่าน CSRF/token/origin check |
| 404 | NOT_FOUND | ไม่พบ Party ของ URL |
| 405 | METHOD_NOT_ALLOWED | ใช้ method ผิด; response มี Allow |
| 409 | PARTY_CANCELLED | Party ยกเลิกแล้ว |
| 409 | PARTY_STARTED | ถึงเวลาเริ่มหรือจบแล้ว |
| 409 | PARTY_FULL | active memberships ถึงความจุแล้ว |
| 409 | ALREADY_MEMBER | ผู้เรียกเป็น Host หรือ active member |
| 409 | REQUEST_EXISTS | มีคำขอ Pending อยู่แล้ว |
| 409 | REQUEST_DECIDED | Approved แต่ไม่มี membership ที่ถอนตัวรองรับการขอใหม่ |

ลำดับ state ก่อน membership/request ทำให้กรณีผิดหลายเงื่อนไข เช่นสมาชิกของ Party ที่เต็ม ได้ PARTY_FULL ก่อน ALREADY_MEMBER

เพิ่ม `CSRF_FAILURE_VIEW = "core.api.csrf_failure"` ใน Django settings เพื่อให้ API ตอบ JSON ตาม contract โดยไม่ปิด CSRF ส่วนหน้า HTML/admin คง handler เดิมของ Django CSRF middleware อาจตอบ 403 ก่อน guard หาก POST ไม่มี token แม้ไม่มี session ส่วน URL ที่ไม่ตรง routing เช่น ID ที่ไม่ใช่เลขยังใช้ Django routing 404

## ข้อจำกัดและการส่งต่อ

- ยังใช้ local session guard ของ BASE-04 รอเพื่อนที่ทำ US1 เชื่อม eligibility/session policy จริง ไม่ถือว่า local tests ยืนยันสิทธิ์นักศึกษาหรือเชื่อมมหาวิทยาลัยแล้ว
- ModelBackend ปัจจุบันมอง session ของบัญชีที่ถูกปิดเป็น anonymous จึงตอบ 401; ไม่เปลี่ยน backend หรือสร้าง Login แยกใน US3
- ไม่รวม UI ของ US3-F, การอนุมัติ US10, การถอนตัว US4 หรือ cancellation endpoint ของ US7
- ไม่มี migration/env/dependency ใหม่; ใช้ฐานข้อมูล PostgreSQL และ unique constraint เดิม
- ทดสอบการยกเลิกด้วย transaction ที่ใช้ lock ตามสัญญา เนื่องจาก endpoint ยกเลิกจริงยังเป็นงานอื่น ต้องทดสอบ integration อีกครั้งเมื่อ US7 พร้อม

## การตรวจงาน

```bash
docker compose run --rm -T backend python backend/manage.py test parties.test_join_requests --noinput --verbosity 2
make verify
make up
make smoke
```

`test_join_requests.py` มี API tests และ `TransactionTestCase` สำหรับ concurrent requests ที่ใช้หลาย connection บน PostgreSQL ตรวจการรอ row lock ด้วย `pg_blocking_pids` และมี timeout เพื่อไม่ให้ค้าง ไม่มีการใช้ SQLite แทนผลทดสอบ concurrency ของ PostgreSQL

ก่อนส่ง PR ให้บันทึกผลคำสั่งจริงและเชื่อม Issue US3-B (เอกสารทีมระบุ #13); ยังไม่ปิด integration ด้านสิทธิ์นักศึกษาหรือหน้า UI แทนงานของเพื่อน

## ผลตรวจ local วันที่ 16 ตุลาคม 2026

- ชุด `parties.test_join_requests` ผ่าน 25 tests รวม 6 concurrency tests บน PostgreSQL โดยไม่ skip
- `make verify` ผ่าน: Django checks, ไม่มี model change ที่ขาด migration, Ruff lint/format และ tests ทั้งหมด 65 กรณี
- `make up` และ `make smoke` ผ่าน: backend/database healthy, HTTP, template/static และ readiness ใช้งานได้
- HTTP จริง: GET คำขอของตัวเองโดยไม่มี session ได้ JSON 401 AUTH_REQUIRED; POST ไม่มี CSRF token ได้ JSON 403 CSRF_FAILED
- Tests ใช้ฐานข้อมูลทดสอบแยกและลบทิ้งเมื่อจบ ไม่เพิ่มบัญชี/Party ตัวอย่างลงฐานพัฒนา
- เป็นผล local validation ไม่ใช่ผล CI, การเชื่อม UI หรือ UAT ของมหาวิทยาลัย

ข้อความสำหรับ PR หลังตรวจเลข Issue จริง:

```markdown
เพิ่ม API ส่ง Pending join request และอ่านคำขอของผู้ใช้จาก session
ใช้ transaction/Party row lock กับ unique constraint เดิมเพื่อป้องกันคำขอซ้ำ
รองรับ Rejected/ผู้ถอนตัวขอใหม่ด้วยแถวเดิมตาม schema contract ล่าสุด

Validation: make verify ผ่าน 65 tests (ใหม่ 25 รวม concurrency 6), make smoke ผ่าน
ไม่มี migration, environment variable หรือ dependency ใหม่
รอเชื่อม eligibility guard จาก US1 และ UI ของ US3-F

Closes #13
```
