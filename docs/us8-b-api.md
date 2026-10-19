# US8-B — Public profile API (API-10)

เริ่มงานบน `feat/us-8-b-profile-api` ที่ commit `1152c0a` ซึ่งตรงกับ `origin/main` หลัง fetch วันที่ 17 ตุลาคม 2026 ใช้ BASE-01/02/04 และ Django JSON views เดิม ไม่เพิ่ม DRF, migrations, environment variables หรือ dependencies

อ้างอิง [Technical Plan](sprint-1-technical-plan.md) API-10 / US8-B-01, [User Stories](user-stories.md) US8 และ [Task Backlog](tasks.md) US8-B

## Endpoint

`GET /api/v1/users/{user_id}/profile` ไม่มี slash ท้าย ใช้ ID จำนวนเต็มของ **User** ไม่ใช่ primary key ของ UserProfile ต้องมี session ที่ผ่าน shared guard สามารถอ่านโปรไฟล์ตนเองหรือผู้อื่นตาม URL ได้

สำเร็จตอบ HTTP 200:

```json
{
  "data": {
    "id": 7,
    "display_name": "เพื่อนนักกีฬา",
    "sports": [{"id": 1, "name": "Badminton"}],
    "credit_score": null
  }
}
```

- `id` คือ User ID ของโปรไฟล์ที่ขอ ไม่ใช่ ID ผู้เรียกหรือ UserProfile ID
- `display_name` มาจาก UserProfile ไม่มีการใช้ username/email แทน
- `sports` มาจาก UserSportInterest ของผู้ใช้เป้าหมาย โดย join Sport และเรียงตาม sport ID; ไม่มีความสนใจคืน `[]`
- `credit_score` อ่านค่าที่เก็บไว้: ไม่มีข้อมูลคืน `null`, ค่า 0 ยังคงเป็น 0 ไม่คำนวณดาว/คะแนนหรือหักเครดิตใน US8
- ส่งเฉพาะฟิลด์ในตัวอย่าง ไม่ serialize User ทั้ง object และไม่ส่ง username, email, ชื่อจริง, password hash, identity provider, token หรือ session
- Query parameters เช่น `user_id` ไม่แทนที่ ID ใน URL และไม่เปลี่ยนข้อมูล
- ใช้ `Cache-Control: ... no-store ... private` เพราะเป็น API ที่ต้องผ่าน session

## กรณีไม่พบโปรไฟล์

ทั้ง User ที่ไม่มีอยู่และ User ที่มีอยู่แต่ไม่มี UserProfile ตอบ HTTP 404 ด้วยข้อมูลเดียวกัน:

```json
{"error":{"code":"NOT_FOUND","message":"ไม่พบโปรไฟล์ที่ต้องการ"}}
```

**การตัดสินใจสำหรับ implementation นี้:** เอกสารเดิมระบุ 404 เมื่อไม่พบ resource แต่ไม่ได้กำหนด fallback ของบัญชีที่ยังไม่มี UserProfile จึงให้ถือว่า profile resource ยังไม่มี ไม่สร้าง profile ระหว่าง GET และไม่สมมติชื่อ/คะแนน ส่งประเด็นนี้ให้เนท/โกลตรวจรับพร้อม PR; ยังไม่อ้างว่าเป็นข้อสรุปทีมเพิ่มเติม

พฤติกรรมนี้ต่างจาก BASE-04 ที่ใช้ข้อความกลางแทนชื่อ Host เพื่อให้ยังดูรายละเอียด Party ได้ เพราะ endpoint นี้ขอ resource โปรไฟล์โดยตรง

## สิทธิ์และข้อผิดพลาด

| HTTP | code | กรณี |
| --- | --- | --- |
| 401 | AUTH_REQUIRED | ไม่มี session ที่ใช้งานได้ |
| 403 | ACCOUNT_INACTIVE | shared guard ได้รับ authenticated user ที่ inactive |
| 403 | FORBIDDEN | session ไม่มี identity มหาวิทยาลัยที่ผ่าน guard ของ US1-B |
| 404 | NOT_FOUND | ไม่พบ UserProfile ตาม User ID |
| 405 | METHOD_NOT_ALLOWED | method ที่เข้า view ไม่ใช่ GET; ส่ง Allow: GET |

ใช้ guard จาก `core.api` โดยไม่สร้าง authentication อีกชุด ModelBackend ปัจจุบันปฏิเสธ inactive account ตอนอ่าน session ทำให้คำขอจริงจาก session ดังกล่าวเป็น anonymous และได้ 401 ตามพฤติกรรม BASE-04/US3

ยังคง CSRF middleware และ JSON failure handler จาก US3 คำขอ unsafe ที่ไม่มี token อาจได้รับ 403 CSRF_FAILED ก่อนถึง view ส่วน ID ที่ไม่ตรง routing เช่นข้อความยังเป็น Django routing 404

## ตำแหน่งโค้ด

- `backend/accounts/views.py`: public_profile อ่าน UserProfile และ UserSportInterest/Sport ด้วยสอง queries (ไม่รวม session/auth) และประกอบ response ตาม allowlist
- `backend/accounts/urls.py`: route ของ API-10
- `backend/config/urls.py`: include accounts.urls ใต้ `/api/v1/`
- `backend/accounts/test_profile_api.py`: endpoint tests ด้วย university identity/session fixtures และข้อมูลในฐานทดสอบ

## ขอบเขตที่ยังรอ

- BASE-04 เชื่อม guard ของ US1-B แล้ว ต้องมี university identity/session ที่ผ่าน [นโยบายร่วม](base-04-api.md#การเชื่อม-us1-b-และขอบเขตที่เหลือ) ตรวจหลักฐานจาก login ล่าสุด ไม่เรียก TU ทุก request; การทดสอบกับ TU จริงและนโยบาย recheck ยังแยกจาก local tests
- US8-F: หน้า HTML `/users/{id}` และการเชื่อมจากชื่อ Host เป็นงาน Frontend ไม่ได้เพิ่มใน US8-B
- การแก้ไขโปรไฟล์ การคำนวณคะแนนดาว และการหักเครดิตไม่อยู่ในงานนี้
- ไม่มีการเพิ่ม seed ลงฐานพัฒนา; tests สร้างข้อมูลแยกใน test database

## การทดสอบ

```bash
make verify
make up
make smoke
```

Tests ใหม่ตรวจ response allowlist และกีฬาให้ตรงคน, User ID ต่างจาก Profile ID, โปรไฟล์ตนเอง, เครดิต 0/null, ไม่มี interests, ไม่มี User/Profile โดยไม่สร้างข้อมูล, query ปลอม, anonymous/inactive/logout session และห้ามแก้/ลบด้วย method อื่น

## ผลตรวจ local วันที่ 17 ตุลาคม 2026

- `make verify` ผ่าน: Django checks, ไม่มี model change ที่ขาด migration, Ruff lint/format และ tests ทั้งหมด 74 กรณีบน PostgreSQL (เพิ่ม US8-B 9 กรณี)
- `make up` และ `make smoke` ผ่าน: backend/database healthy, HTTP, templates/static และ database readiness
- HTTP จริง: `GET /api/v1/users/1/profile` โดยไม่มี session ได้ JSON 401 AUTH_REQUIRED พร้อม no-store/private cache policy
- ผลเหล่านี้เป็น local checks ไม่ใช่ผล GitHub Actions, Frontend integration หรือ UAT ของระบบมหาวิทยาลัย
