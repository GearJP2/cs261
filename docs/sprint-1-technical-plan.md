# Sprint 1 — Technical Tasks, API และ Database

ใช้คู่กับ [Sprint Checklist และรายชื่อทีม](sprint-1-checklist.md) เอกสารนี้แตกงานย่อยที่นำไปสร้าง Issue ได้ โดยคงรหัส task เดิม เช่น `US3-B` แล้วเพิ่มรหัสย่อย เช่น `US3-B-01`

**สถานะ:** แบบเสนอสำหรับพัฒนา ยังไม่มี API, migration หรือผลทดสอบเหล่านี้จริง ขอบเขตเดิมยังเป็น US1/3/7/8/9; US1 ยืนยันเป็น Login/Logout ของนักศึกษาธรรมศาสตร์ (High, 3 points) แล้ว และ US10/6/4 ด้านล่างเป็นข้อเสนอ ไม่ใช่งานที่เพิ่มเข้า Sprint แล้ว

## 1. ข้อเสนอว่าจะเริ่ม US ไหนเพิ่ม

| ลำดับ | งาน | เหตุผลและขอบเขตที่แนะนำ | ผลต่อแผน |
| --- | --- | --- | --- |
| จำเป็นก่อนเริ่ม flow | **US1 Login** และกำหนด Story สร้าง Party แยก | US1 ยืนยันแล้วว่าเป็น Login/Logout; ยังต้องมี Party ให้ขอเข้าร่วมและแก้ไข | เริ่ม US1 ทันที; ถ้าต้องเดโมสร้างนัดจริงให้เลือก Story สร้าง Party เพิ่มก่อน US10; seed ใช้ทดสอบได้แต่ไม่นับว่าสร้าง Party ผ่านหน้าเว็บได้ |
| ควรเลือกเพิ่มเป็นอันดับแรก | **US10 — Host อนุมัติ/ปฏิเสธ** | ต่อ US3 จาก Pending ไปเป็นสมาชิกจริง มีรายการคำขอและปุ่มตัดสินใจ พร้อมควบคุมที่ว่าง | US10 = 5 points; เปลี่ยน US8 = 1 point เป็น US10 เพิ่มรวมจาก 22 เป็น 26 จึงต้องประเมินใหม่ ถ้าเน้นสมาชิกครบ flow ให้พิจารณาเลื่อน US7 = 8 points จะเหลือ 19 points ก่อนงานสร้าง Party/setup |
| ถัดจาก US10 | **US6 — รายชื่อสมาชิก** | ใช้ข้อมูล Membership เดียวกัน แสดง Host/Member และเห็นผลหลังอนุมัติ | เริ่ม schema/contract รองรับได้ก่อน; เพิ่ม UI/API เต็มเมื่อมีเวลา ไม่จำเป็นต่อการตรวจรับ US10 ซึ่งตรวจสมาชิกจากฐานข้อมูลได้ |
| หลัง flow หลักพร้อม | **US4 — ถอนตัว** | ช่วยคืนที่ว่างและทดสอบวงจรสมาชิกครบขึ้น | ควรอยู่ Sprint ถัดไปหาก Backend ยังไม่พร้อม เพราะต้องจัดการถอนซ้ำและคำขอพร้อมกัน |
| ยังไม่แนะนำเพิ่ม | US5, US11–14 และแชท | ไม่ได้ปลดล็อก flow ขอเข้าร่วมและจัดการ Party ในรอบนี้ | เลื่อนไปหลังระบบสมาชิกนิ่ง |

**ข้อเสนอ Sprint ที่เน้นการใช้งาน:** ฐานระบบ/login + การสร้าง Party ตาม Story ที่ยืนยัน → US9 → US3 → US10 → US7 แล้วค่อย US6/US8 ตามกำลังทีม ไม่ควรสัญญาว่าทำทุกอย่างได้ใน 2 สัปดาห์ก่อนตรวจช่องทางเชื่อมบัญชี US1 และชั่วโมงว่างจริงของทีม

### ภาระงานจากคะแนนที่ทีมส่งมา

| ทางเลือก | Story points | เงื่อนไข |
| --- | --- | --- |
| Scope เดิม US1/3/7/8/9 | 22 | ขอได้เป็น Pending; ยังไม่มีหน้าสร้าง Party |
| เพิ่ม US10 คง scope เดิม | 27 | ภาระ Backend/concurrency เพิ่ม |
| เลื่อน US8 แล้วเพิ่ม US10 | 26 | ลดงานเพียง 1 point จึงไม่ใช่ทางเลือกที่ลดภาระมาก |
| เสนอเลื่อน US7 แล้วเพิ่ม US10 | 19 | ได้ US1/3/8/9/10; ไม่มีแก้/ยกเลิกในรอบนี้ และ US9 ยังต้องทดสอบกับหน้าสร้างจริงหากรับเข้ามา |
| ทางเลือก 19 points + US6 | 21 | มีหน้ารายชื่อสมาชิก แต่ให้รับเพิ่มหลังประเมินงานพื้นฐานครบ |

ทุกทางเลือกยังต้องเผื่อ setup/integration และ Story สร้าง Party ที่ยังไม่มี estimate จึงยังรับรอง capacity ของทีมไม่ได้ คะแนน US7/US8 ต่างกันมาก ควรทบทวนเหตุผลร่วมกันโดยคงตัวเลขต้นทางไว้จนทีมตกลงใหม่

วัน Planning ให้ตัดสินใจเลือก scope แล้วอัปเดต checklist หลักด้วย ก่อนเริ่มงานเสริม US2 ยืนยันว่าเป็น Search (3 points) ไม่ใช่สร้าง Party; ถ้าเปิดจาก seed/ลิงก์ได้อยู่แล้วให้พิจารณา Search หลัง flow สมาชิกครบ ส่วน US4 (High, 2 points) เป็นงานถัดไปที่ช่วยคืนที่ว่างได้จริง

## 2. ข้อตกลงทางเทคนิคที่เสนอ

ยึด Django + PostgreSQL ตามแผน Python เดิม ตั้ง prefix `/api/v1` สำหรับ JSON endpoints และแยกหน้าเว็บจาก service logic หากใช้ Django Templates สามารถให้ view เรียก service เดียวกันได้ โดยไม่ต้องเพิ่ม SPA หรือแยก deployment เพื่อทำตามเอกสารนี้

| เรื่อง | ข้อเสนอขั้นต่ำที่ทีมต้องยืนยัน |
| --- | --- |
| Authentication | ใช้ session; `request.user` เป็นผู้กระทำทุกครั้ง ไม่รับ `user_id` หรือ `host_id` จากผู้ใช้เพื่อแทนตัวผู้กระทำ |
| สิทธิ์ทั่วไป | API ธุรกิจต้องมี session ที่ยืนยันสิทธิ์นักศึกษาและบัญชีใช้งานได้; login entry/callback เป็นข้อยกเว้นตามตาราง Auth; endpoint เปลี่ยนข้อมูลตรวจ CSRF; เจ้าของ Party ตรวจที่ Backend |
| ID / เวลา | ID จำนวนเต็ม; ส่งวันที่แบบ ISO 8601 พร้อม offset เก็บ timestamp เป็น UTC และใช้ `Asia/Bangkok` ตรวจตารางสนาม |
| ความจุ | `capacity` รวม Host; สร้าง Host เป็น active membership 1 แถว; ที่ว่าง = capacity − จำนวน active memberships |
| สถานะ Party | เก็บ `cancelled_at`; คำนวณสถานะตามลำดับ Cancelled → Completed → InProgress → Full → Open จากเวลาและจำนวนสมาชิก ไม่เก็บ Full ที่อาจค้าง |
| ตารางสนามขั้นต่ำ | ตารางรายสัปดาห์ หลายช่วงต่อวันได้; วันไม่มีช่วงคือปิด; ใน Sprint นี้เสนอรับนัดภายในวันเดียวและอยู่ครบในหนึ่งช่วงเปิด ยังไม่รวมวันหยุดพิเศษ/ข้ามเที่ยงคืน ต้องยืนยันข้อจำกัดนี้ก่อนถือเป็น AC |
| แก้ไข Party | เสนอให้แก้/ยกเลิกก่อนเริ่มเท่านั้น; แก้ไม่ได้เมื่อยกเลิกแล้ว; capacity ใหม่ต้องไม่ต่ำกว่าสมาชิกปัจจุบัน; เปลี่ยนกีฬา/สนาม/เวลาได้ถ้าผ่าน validation |
| คำขอซ้ำ | หนึ่งแถวต่อผู้ใช้ต่อ Party; Pending เดิมคืน `409 REQUEST_EXISTS`; Rejected ยังไม่ให้ขอซ้ำใน Sprint นี้ ต้องยืนยันนโยบายก่อนพัฒนา |
| คะแนนเครดิต | อ่านค่าที่เก็บไว้; ถ้ายังไม่กำหนดเครดิตตั้งต้นให้ใช้ `null` และแสดง “ยังไม่มีข้อมูล” ไม่สมมติคะแนนหรือสร้างสูตร US14 |
| ข้อมูลตัวอย่าง | ตัวอย่าง ID และวันที่ในเอกสารเป็นสมมติ เวลาใน seed ต้องสร้างเทียบกับเวลารันทดสอบเพื่อไม่ให้หมดอายุ |

ข้อเสนอนี้ไม่เพิ่มระบบจองสนามหรือห้ามสอง Party ใช้สนามพร้อมกัน เพราะยังไม่มี requirement เรื่องสิทธิ์จองสนาม

### รูปแบบ response ร่วม

สำเร็จใช้ `{"data": ...}`; รายการใช้ `{"data": [], "page": 1, "page_size": 20, "total": 0}` โดย `page_size` สูงสุด 100 สำหรับรายการที่แบ่งหน้า

```json
{
  "error": {
    "code": "VENUE_CLOSED",
    "message": "ช่วงเวลาที่เลือกอยู่นอกเวลาเปิดสนาม",
    "fields": {"starts_at": "กรุณาเลือกช่วงเวลาเปิดให้บริการ"}
  }
}
```

| HTTP | ใช้เมื่อ |
| --- | --- |
| 200 / 201 | อ่านหรือแก้ไขสำเร็จ / สร้างข้อมูลสำเร็จ |
| 400 | JSON/ชนิดข้อมูล/ช่วงเวลา/สนามไม่ตรงกีฬาไม่ถูกต้อง เช่น `INVALID_INPUT`, `INVALID_TIME_RANGE`, `VENUE_CLOSED` |
| 401 | `AUTH_REQUIRED` ไม่มี session ที่ใช้ได้ (สำหรับ JSON API; หน้า HTML redirect ไป login ได้) |
| 403 | `FORBIDDEN`, `ACCOUNT_INACTIVE` หรือ `CSRF_FAILED` |
| 404 | `NOT_FOUND` ไม่พบ resource หรือ request ไม่อยู่ใน Party ตาม URL |
| 409 | สถานะข้อมูลไม่ให้ทำ เช่น `PARTY_FULL`, `PARTY_STARTED`, `PARTY_CANCELLED`, `ALREADY_MEMBER`, `REQUEST_EXISTS`, `REQUEST_DECIDED`, `CAPACITY_TOO_SMALL` |

พฤติกรรม 401/error envelope เป็น contract ที่ทีมต้อง implement และทดสอบเอง ไม่สมมติว่า Django view/middleware ทุกตัวส่งรูปแบบนี้ให้อัตโนมัติ

## 3. Database ขั้นต่ำ — โกลนำ กอล์ฟ/พีร่วมตรวจ

ชื่อตารางเป็น logical names; ใช้ migrations เป็นแหล่งกำหนด schema หลัก ไม่แก้ SQL กับ ORM ให้เป็นสองชุดที่ไม่ตรงกัน `FK` หมายถึง foreign key และทุกตารางมี primary key เว้นตารางเชื่อมที่เลือก composite key

| ตาราง | ฟิลด์ขั้นต่ำ | Constraint / Index / การใช้งาน |
| --- | --- | --- |
| User | ใช้ Django user: `id`, `is_active` และกลไกบัญชีตามที่เลือก | ตัดสินใจ user model ก่อน migration แรก; ไม่สร้างที่เก็บรหัสผ่านมหาวิทยาลัยเอง |
| UniversityIdentity | `id`, `user_id` FK, `provider_key` varchar(150), `subject` varchar(255), `student_verified_at`, `eligibility_checked_at` | unique `(provider_key, subject)`; ใช้ identifier จากผลตรวจ provider ที่เชื่อถือได้ ไม่ใช้ชื่อ/email ผูกบัญชี; ไม่เก็บ password/token หากไม่จำเป็น |
| UserProfile | `user_id` FK, `display_name` varchar(100), `credit_score` integer nullable | unique `user_id`; ชื่อไม่ว่าง; ส่งออกเฉพาะฟิลด์อนุญาต |
| Sport | `id`, `name` varchar(80) | unique name |
| UserSportInterest | `user_id` FK, `sport_id` FK | unique `(user_id, sport_id)` |
| Venue | `id`, `name` varchar(150), `location_text` varchar(255), `is_active` boolean | เก็บจุดนัดพบขั้นต่ำ; สนาม inactive ห้ามใช้สร้าง/แก้ Party |
| VenueSport | `venue_id` FK, `sport_id` FK | unique `(venue_id, sport_id)`; index sport_id สำหรับค้นสนาม |
| VenueOpeningHour | `id`, `venue_id` FK, `weekday` smallint, `opens_at` time, `closes_at` time | weekday 0–6 (จันทร์–อาทิตย์); check opens_at < closes_at; unique `(venue_id, weekday, opens_at)`; validator กันช่วงซ้อน |
| Party | `id`, `host_id` FK, `sport_id` FK, `venue_id` FK, `title` varchar(150), `description` text, `starts_at`, `ends_at`, `capacity` integer, `cancelled_at` nullable, `created_at`, `updated_at` | check capacity ≥ 1 และ starts_at < ends_at; index `(sport_id, starts_at)` และ host_id; จำกัด description ใน validation เช่น 2,000 ตัวอักษร |
| PartyMembership | `id`, `party_id` FK, `user_id` FK, `joined_at`, `left_at` nullable | unique `(party_id, user_id)`; active เมื่อ left_at เป็น null; role คำนวณจาก Party.host_id ไม่เก็บซ้ำ |
| JoinRequest | `id`, `party_id` FK, `user_id` FK, `status` (Pending/Approved/Rejected), `created_at`, `decided_at` nullable, `decided_by_id` FK nullable | unique `(party_id, user_id)`; index `(party_id, status, created_at)`; Pending ต้องไม่มีข้อมูลผู้ตัดสิน; เตรียม Approved/Rejected ไว้สำหรับ US10 |

**กฎที่ service ต้องรักษา:** Host ต้องมี active membership, จำนวน active membership ต้องไม่เกิน capacity, สนามต้องรองรับกีฬา และช่วงนัดต้องอยู่ในเวลาเปิด กฎข้ามตารางเหล่านี้ไม่สำเร็จด้วย unique/check constraint ธรรมดาเพียงอย่างเดียว

เสนอห้าม hard delete User/Sport/Venue/Party ที่ถูกอ้างอิงใน Sprint นี้ ใช้ is_active/cancelled_at แทน; โกลกำหนด FK delete policy ใน migration ให้สอดคล้องกัน ไม่เปิด delete endpoint โดยไม่จำเป็น

เมื่อทำ US4 ภายหลัง ใช้ `left_at` ถอนตัวและเปิด membership เดิมเมื่ออนุมัติการกลับเข้าใหม่ตามนโยบายที่ตกลง ไม่สร้างแถวซ้ำ; การขอใหม่หลัง Rejected/ถอนตัวยังไม่อยู่ใน scope รอบนี้

### Checklist ฐานระบบ (แตกจาก BASE)

- [ ] **BASE-01-01** เกียร์ + โกล: ทำให้ app/DB รันได้จริง มี dependency lock, `.env.example`, migration และคำสั่ง test; ตรวจจากเครื่องเพื่อนหนึ่งคน
- [ ] **BASE-02-01** โกล + กอล์ฟ: สร้าง ERD และตกลง field/constraint ข้างต้น ส่งเป็น PR ก่อนเริ่ม API ที่ใช้ข้อมูล
- [ ] **BASE-02-02** โกล + พี: ทำ migrations ของ User/Profile/Sport/Interest/Party/Membership/JoinRequest; ประสานลำดับ migration สนาม US9-B1-01 ก่อน FK Party→Venue
- [ ] **BASE-02-03** กอล์ฟ + พี + เกียร์: สร้าง contract ของ error/auth/Party state และ service กลาง `get_party_state`, `validate_party_schedule`, `count_active_members`
- [ ] **BASE-03-01** โกล + ออสติน: seed ทำซ้ำได้ มี Host H, ผู้ขอ A/B, สมาชิกเดิม M, outsider X, inactive user, สนามเปิด/ปิด และ Party แต่ละสถานะ; มี Party เหลือหนึ่งที่สำหรับทดสอบพร้อมกัน
- [ ] **BASE-04-01** พี + เกียร์: ใช้ session และ API-01 ที่ US1-B-03 ทำให้แล้ว; implement API-02 และ route protection ด้วย guard เดียวกัน; fixture/session dev ใช้ทดสอบแยกจากการเชื่อมจริง ไม่สร้าง login ซ้ำใน BASE
- [ ] **BASE-04-02** วี + เนท: สร้างหน้า `/parties/{id}` และทางเข้าจาก fixture/ลิงก์เดโม ให้ US3/7 ใช้ร่วมกัน; redirect login และกลับหน้าต้นทางโดยไม่รับ redirect URL ภายนอก

## 4. API Inventory — ขอบเขตหลัก

ทุก endpoint ในตารางใช้ prefix `/api/v1` และต้อง login; ตารางนี้กำหนดสิ่งที่จะ implement ไม่ใช่รายการ API ที่มีอยู่แล้ว

| รหัส / Task | Method + Path | Input ขั้นต่ำ | Response data / สิทธิ์ / Backend owner |
| --- | --- | --- | --- |
| API-01 / US1-B (BASE-04 ใช้ร่วม) | `GET /me` | ไม่มี | `{id,display_name,student_verified:true}` หลังตรวจ session/บัญชี/สิทธิ์; พี |
| API-02 / BASE-04 | `GET /parties/{party_id}` | path ID | `{id,title,description,host:{id,display_name},sport_id,venue_id,starts_at,ends_at,capacity,member_count,remaining_slots,state,is_host,is_member}`; ไม่มีรายชื่อผู้ขอ; พี |
| API-03 / US9-B2 | `GET /sports` | ไม่มี | array `{id,name}`; กอล์ฟ |
| API-04 / US9-B2 | `GET /venues?sport_id=1&page=1&page_size=20` | sport_id จำเป็น | รายการสนาม active `{id,name,location_text}` ที่รองรับกีฬา; กอล์ฟ |
| API-05 / US9-B2 | `GET /venues/{venue_id}/opening-hours` | path ID | `{venue_id,timezone,intervals:[{weekday,opens_at,closes_at}]}`; กอล์ฟ |
| API-06 / US3-B | `POST /parties/{party_id}/join-requests` | `{}` ไม่รับ user_id | 201 `{id,party_id,status:"Pending",created_at}`; พี |
| API-07 / US3-B | `GET /parties/{party_id}/join-requests/me` | ไม่มี | `{id,status,created_at}` หรือ `null` ถ้ายังไม่เคยขอ; ผู้ใช้เห็นเฉพาะคำขอตนเอง; พี |
| API-08 / US7-B | `PATCH /parties/{party_id}` | ฟิลด์ที่อนุญาตจากตัวอย่างด้านล่าง | Party data เหมือน API-02 หลังแก้; Host เท่านั้น; กอล์ฟ |
| API-09 / US7-B | `POST /parties/{party_id}/cancel` | `{}` | `{id,state:"Cancelled",cancelled_at}`; Host เท่านั้น; กอล์ฟ |
| API-10 / US8-B | `GET /users/{user_id}/profile` | path ID | `{id,display_name,sports:[{id,name}],credit_score}`; login อ่านได้เฉพาะ public profile; พี |

### Input/Output สำคัญ

API-08 รับเฉพาะ `title`, `description`, `sport_id`, `venue_id`, `starts_at`, `ends_at`, `capacity`; unknown/read-only fields เช่น host_id/status/member_count ต้องถูกปฏิเสธ ไม่เอา request body ไป update model ทั้งก้อน

```json
{
  "venue_id": 2,
  "starts_at": "2026-10-20T17:00:00+07:00",
  "ends_at": "2026-10-20T18:00:00+07:00",
  "capacity": 6
}
```

PATCH ต้องรวมค่าที่ส่งกับข้อมูลเดิมแล้ว validate ทั้งชุด เช่นเปลี่ยนแค่ venue_id ก็ต้องตรวจ sport และเวลาเดิมกับสนามใหม่ ไม่ตรวจเฉพาะฟิลด์ที่เปลี่ยน

ตัวอย่าง API-06 เมื่อสำเร็จ:

```json
{"data":{"id":45,"party_id":12,"status":"Pending","created_at":"2026-10-09T10:00:00Z"}}
```

ตัวอย่าง API-10: `{"data":{"id":7,"display_name":"ผู้ใช้ตัวอย่าง","sports":[{"id":1,"name":"Badminton"}],"credit_score":null}}` ไม่ส่ง email, provider identifier, password hash, token หรือ session

## 5. US9 — สนามและเวลาเปิดให้บริการ

**ทำก่อน logic เวลาใน US7; โกลดู DB, กอล์ฟดู API, ออสตินดูหน้าเว็บ**

- [ ] **US9-D-01** ออสติน + วี: ออกแบบหน้ารายการสนาม ส่วนเลือกกีฬา/สนาม และ UI เวลาเปิด–ปิด; มี loading/empty/error และล้างสนามเดิมเมื่อเปลี่ยนกีฬา
- [ ] **US9-B1-01** โกล + กอล์ฟ: migration Venue/VenueSport/OpeningHour พร้อม constraint ในหัวข้อ DB; seed สนามหลายกีฬาและวันปิด; ทดสอบ FK/unique/check
- [ ] **US9-B2-01** กอล์ฟ + พี: implement API-03/04/05 พร้อม input validation, pagination ของ API-04 และ 404 เมื่อไม่พบสนาม
- [ ] **US9-B2-02** กอล์ฟ + โกล: implement `validate_party_schedule(sport_id, venue_id, starts_at, ends_at)` ตรวจ active venue, sport mapping, offset/timezone, start < end, วันเดียวกัน และอยู่ครบในช่วงเปิดหนึ่งช่วง; เรียกจาก service สร้างและแก้ Party
- [ ] **US9-F-01** ออสติน + เนท: เชื่อม API-03→04→05; ทำส่วนเลือกสนามใช้ร่วมกับฟอร์ม US7/สร้าง Party; ป้องกัน response เก่าทับตัวเลือกใหม่เมื่อสลับกีฬาเร็ว
- [ ] **US9-T-01** เกียร์ + โกล/กอล์ฟ: ทดสอบเริ่มตรงเวลาเปิด/จบตรงเวลาปิดผ่าน; เริ่มก่อนเปิด/จบหลังปิด/คร่อมช่วงพัก/วันปิด/สนามไม่รองรับกีฬา/ไม่มี offset/ข้ามวันถูกปฏิเสธตาม contract

ผลส่งมอบ: migration, seed, 3 endpoints, schedule service, UI component และผลทดสอบจาก Backend โดยตรง การเชื่อมหน้าสร้าง Party ยังต้องมีเจ้าของและ Story จริงก่อนปิด US9 ทั้ง Story

## 6. US3 — ส่งคำขอเข้าร่วม

- [ ] **US3-D-01** เนท + พี: ระบุ UI จาก API-02/07 เป็น ขอเข้าร่วม / กำลังส่ง / Pending / เป็นสมาชิกแล้ว / เต็ม / เริ่มแล้ว / ยกเลิก / Rejected; สถานะปิดรับมีผลเหนือปุ่มที่เคยเปิด
- [ ] **US3-B-01** พี + โกล: ตรวจ migration JoinRequest และ unique คู่ Party/User; ไม่ต้องเพิ่มตารางอีก; เขียน service ส่งคำขอพร้อม test constraint
- [ ] **US3-B-02** พี + กอล์ฟ: implement API-06 ภายใน transaction ล็อก Party ก่อนตรวจ state/capacity/membership/request เดิม; insert Pending แล้ว commit โดยไม่เปลี่ยน Membership
- [ ] **US3-B-03** พี + กอล์ฟ: implement API-07 ให้กรอง user จาก session; query ของคนอื่นห้ามเปลี่ยนเจ้าของที่อ่านได้
- [ ] **US3-F-01** เนท + วี: โหลด API-02/07 พร้อมหน้า; disable ระหว่างส่ง; เมื่อ 201 แสดง Pending; ถ้า 409 หรือ network error ให้โหลดสถานะใหม่ก่อนเปิดให้ retry เพื่อรองรับกรณีบันทึกสำเร็จแต่ response หาย
- [ ] **US3-T-01** ออสติน + พี: สอง request จาก user เดียวพร้อมกันได้ Pending หนึ่งแถว; สอง user ขอเมื่อเหลือหนึ่งที่สร้าง Pending ได้ทั้งคู่ เพราะยังไม่จองที่; จำนวนสมาชิก/ที่ว่างไม่เปลี่ยน
- [ ] **US3-T-02** ออสติน + พี: ทดสอบสมาชิกเดิม/Host/ไม่ login/inactive/Party เต็ม/เริ่ม/ยกเลิก/ID ผิด และลองส่ง user_id คนอื่น; Backend ปฏิเสธตาม contract

การส่งคำขอแข่งกับการยกเลิกใช้ Party lock เดียวกัน: ถ้ายกเลิก commit ก่อนต้องปฏิเสธคำขอ; ถ้าคำขอ commit ก่อน อนุญาตให้เก็บ Pending เดิมแต่ไม่สามารถอนุมัติบน Party ที่ยกเลิกแล้ว

## 7. US7 — แก้ไขและยกเลิก Party

- [ ] **US7-D-01** วี + กอล์ฟ: form แสดงข้อมูลปัจจุบัน ตรวจ required fields และ dialog ยืนยันยกเลิก; กำหนดรายการ error code ที่แต่ละช่องต้องแสดง
- [ ] **US7-B-01** กอล์ฟ + พี: implement API-08 ตรวจ Host ภายใน transaction/Party lock, merge ค่ากับของเดิม, allowlist ฟิลด์, เรียก schedule service, capacity ≥ active count และ starts_at ยังไม่ผ่าน
- [ ] **US7-B-02** กอล์ฟ + พี: implement API-09 ล็อก Party และตรวจ Host; ยกเลิกก่อนเริ่มได้; ยิงซ้ำบน Party ที่ Cancelled ให้ 200 พร้อม cancelled_at เดิม; ไม่ลบ membership/request ประวัติ
- [ ] **US7-F-01** วี + เนท: เชื่อม API-02/08/09 และส่วนเลือกสนาม US9; success แล้วแสดงข้อมูลตอบกลับ; failure คงข้อมูลฟอร์มและแสดง error; ยกเลิก dialog แล้วไม่ยิง API
- [ ] **US7-T-01** ออสติน + กอล์ฟ: outsider เรียกตรงไม่ได้, เปลี่ยน host_id ไม่ได้, capacity ต่ำกว่าสมาชิกไม่ได้, เปลี่ยนแค่สนามยังตรวจเวลาเดิม, แก้หลังเริ่มไม่ได้, ยกเลิกซ้ำไม่สร้างผลซ้ำ
- [ ] **US7-T-02** ออสติน + พี: ทดสอบ race ยกเลิกกับส่งคำขอ/แก้ไข; ตรวจทั้ง status ที่ตอบและข้อมูลหลัง transaction เสร็จ

Pending เดิมไม่จองความจุและไม่ลดจำนวนที่ว่างหลังแก้ไข; ถ้าเปลี่ยนเวลา/สนาม คำขอยังคงอยู่ตามข้อเสนอรอบนี้และผู้ใช้เห็นข้อมูล Party ล่าสุด ยังไม่มีการแจ้งเตือนอัตโนมัติ ต้องยืนยันนโยบายนี้กับทีม

## 8. US8 — โปรไฟล์

- [ ] **US8-D-01** เนท + วี: กำหนด public fields ของ API-10 และ UI ชื่อ/รายการกีฬา/เครดิต พร้อม no interests, null credit และ not found
- [ ] **US8-B-01** พี + โกล: ตรวจ Profile/Interest migration และ seed; implement API-10 ด้วยการเลือก field ที่อนุญาต ห้ามส่ง serialized User ทั้ง object
- [ ] **US8-F-01** เนท + วี: หน้า `/users/{id}` โหลด API-10; กดชื่อ Host จากหน้ารายละเอียด Party ไปหน้าคนที่ถูกต้อง; ไม่ต้องรอ US6
- [ ] **US8-T-01** วี + โกล: ตรวจ user หลาย ID, no interests/null credit, 404, 401, inactive session และตรวจชุด keys ของ response ไม่มีข้อมูลลับ

ถ้าทีมเลือกเลื่อน US8 เพื่อทำ US10 ให้คงเฉพาะ User/Profile ขั้นต่ำที่ใช้ session และชื่อ Host ส่วนหน้าโปรไฟล์และ API-10 ย้ายออกพร้อมกัน ไม่ทำครึ่งหนึ่งแล้วนับ Story เสร็จ

## 9. US1 — Login / ยืนยันบัญชีนักศึกษาธรรมศาสตร์ / Logout

**Priority High • Estimate 3 points ตามทีมระบุ** อ่าน [Story และ Scenario ที่ยืนยัน](user-stories.md) พีนำ Backend โดยกอล์ฟช่วยตรวจ วีทำหน้าเว็บ โกลทำ identity mapping เกียร์ช่วยเชื่อมระบบ และออสตินช่วยทดสอบ

### Flow และขอบเขต

หน้า Login → ช่องทางยืนยันตัวตนที่มหาวิทยาลัยอนุญาต → ตรวจผลยืนยันและสิทธิ์นักศึกษา → ผูก local user → สร้าง session → หน้าหลัก ส่วน Logout ยกเลิก session ของแอปแล้วกลับหน้า Login ไม่อ้างว่า logout จากทุกบริการของมหาวิทยาลัยด้วย

ต้องตรวจสอบ provider, protocol, การลงทะเบียนแอป, credentials/redirect URI และข้อมูลที่ใช้ยืนยันสิทธิ์นักศึกษา ขณะนี้ยังไม่ทราบช่องทางจริง จึงไม่กำหนด URL ของมหาวิทยาลัยหรือสมมติว่ารองรับ OAuth/OIDC/SAML แล้ว การใช้ชื่อโดเมน email อย่างเดียวไม่เพียงพอต่อเกณฑ์ตรวจสิทธิ์นักศึกษาที่ Story ต้องการ

### Routes/API ที่เสนอ

ชื่อ route เป็นของแอปเรา ส่วน protocol และ callback method ต้องปรับตามเอกสารของ provider ที่ได้รับอนุญาต

| รหัส | Route | Input / Output / สิทธิ์ |
| --- | --- | --- |
| AUTH-01 / US1-D,F | `GET /login` | หน้า HTML สาธารณะ มีปุ่มไปยืนยันตัวตน/ช่องกรอกตาม flow ที่ได้รับอนุญาต; ผู้มี session ใช้ได้แล้วไปหน้าหลัก |
| AUTH-02 / US1-B | `GET /auth/university/start` (ข้อเสนอแบบ redirect SSO) | สาธารณะ; สร้าง login attempt อายุสั้น ผูก browser/session และ redirect ไป provider ที่กำหนดฝั่งเซิร์ฟเวอร์; ไม่รับ provider URL จากผู้ใช้ |
| AUTH-03 / US1-B | `/auth/university/callback` (GET หรือ POST ตาม protocol) | สาธารณะสำหรับรับผลยืนยัน แต่สร้าง session ได้หลังตรวจครบเท่านั้น; สำเร็จ redirect หน้าหลัก; ล้มเหลวกลับ Login พร้อม error ที่ไม่เปิดเผยข้อมูลลับ |
| API-01 / US1-B | `GET /api/v1/me` | session ปัจจุบันเท่านั้น; 200 `{data:{id,display_name,student_verified:true}}`; ไม่มี session/หมดอายุให้ 401, บัญชีถูกปิดหรือหมดสิทธิ์ให้ 403 |
| AUTH-04 / US1-B | `POST /api/v1/auth/logout` | `{}`; ตรวจ CSRF; ยกเลิก server session และล้าง cookie; 200 `{data:{logged_out:true}}`; เรียกซ้ำเมื่อไม่มี session ให้ 200 ได้แต่ไม่ข้าม CSRF policy |

AUTH-02/03 เป็นแบบตั้งต้นสำหรับ redirect SSO ไม่ใช่ข้อสรุปว่ามหาวิทยาลัยมีบริการนี้ หาก provider ให้ API แบบอื่น ให้แก้ contract สอง route นี้ก่อนพัฒนา และใช้เฉพาะวิธีที่ได้รับอนุญาต ห้ามสร้าง endpoint รับ password มหาวิทยาลัยเองเพียงเพื่อให้ตรงกับ mockup

### DB และ session ขั้นต่ำ

- โกลเพิ่ม UniversityIdentity ตามตาราง DB; `provider_key` มาจากการตั้งค่าที่เชื่อถือได้ ส่วน `subject` มาจากผลตรวจ provider ไม่รับจาก request ฝั่งหน้าเว็บโดยตรง
- ผูก identity→user ด้วย unique constraint และ transaction; login ซ้ำของ identity เดิมไม่สร้าง User/Profile ซ้ำ และไม่ auto-link ด้วย email/name ที่เหมือนกัน
- สร้าง local User/Profile หลังตรวจตัวตนและสิทธิ์ครบเท่านั้น; `student_verified_at`/`eligibility_checked_at` บันทึกเวลาเซิร์ฟเวอร์ ไม่ใช้ timestamp เพียงอย่างเดียวแทนผลตรวจสิทธิ์ปัจจุบัน
- ใช้กลไก session ของ Django ที่เลือกไว้ ไม่สร้างตาราง session/token เองโดยไม่จำเป็น; session เก็บ user/identity reference และข้อมูลตรวจสิทธิ์ขั้นต่ำ ไม่เก็บรหัสผ่านมหาวิทยาลัย
- ใช้ cookie HttpOnly/Secure บน HTTPS และกำหนด SameSite ให้เหมาะกับ callback protocol; หมุน session identifier หลัง login, กำหนดอายุ session ที่ทีมตกลง และไม่บันทึก credential/token/assertion ลง log
- กำหนด eligibility policy ใน US1-D-01: ตรวจใหม่เมื่อ login, อายุหลักฐานระหว่าง session และพฤติกรรมเมื่อข้อมูลหมดอายุ/ตรวจไม่ได้; API guard ตรวจ local is_active และหลักฐานที่ยังใช้ได้ ไม่เชื่อ `student_verified` ที่ client ส่งมา
- หาก protocol ต้อง POST callback ให้กำหนดข้อยกเว้น CSRF เฉพาะ callback ที่จำเป็นพร้อม validation ตาม protocol; API เปลี่ยนข้อมูลอื่นยังต้องตรวจ CSRF

### Task ย่อย

- [ ] **US1-D-01** พี + เกียร์: ตรวจช่องทางมหาวิทยาลัยและบันทึก protocol, app credentials ที่ต้องขอ, redirect/callback, identifier และหลักฐานสิทธิ์นักศึกษา; ยืนยัน eligibility/session expiry policy โดยไม่เผย secrets ใน Issue
- [ ] **US1-D-02** วี + เนท: ออกแบบ Login, loading, credentials ผิด/ยกเลิก, provider ล่ม, ไม่มีสิทธิ์ และ Logout; สำเร็จไปหน้าหลัก และรองรับกลับหน้าต้นทางเฉพาะ URL ภายในที่อนุญาต
- [ ] **US1-B-01** โกล + พี: migration UniversityIdentity, User/Profile mapping และทดสอบ unique/การ login ซ้ำไม่เกิดบัญชีซ้ำ
- [ ] **US1-B-02** พี + กอล์ฟ/เกียร์: implement AUTH-02/03 หรือ flow ที่ provider อนุญาตด้วย library ตาม protocol; ตรวจความถูกต้องและความสดใหม่ของผลตอบกลับ, ผู้ส่ง/ผู้รับที่คาดหวัง และป้องกัน replay ก่อนเชื่อข้อมูล; ถ้าเป็น OIDC ใช้ code flow และตรวจ state/nonce/PKCE/issuer/audience/signature/expiry ตาม flow ที่เลือก
- [ ] **US1-B-03** พี + กอล์ฟ: ตรวจสิทธิ์นักศึกษา, upsert mapping ใน transaction, สร้าง/หมุน session, API-01 และ guard กลาง; BASE-04 และ API ธุรกิจใช้ชุดเดียวกัน
- [ ] **US1-B-04** พี + เกียร์: implement AUTH-04, session expiry และ cookie/CSRF settings; ทดสอบ session เก่าหลัง logout เข้า API ไม่ได้จากทุกแท็บที่ใช้ session นั้น
- [ ] **US1-F-01** วี + เนท: เชื่อม AUTH-01/02 หรือ flow ที่ยืนยัน แสดง loading/error และกลับหน้าหลักเมื่อสำเร็จ; ไม่มี secret/token/password ใน localStorage หรือข้อความ error
- [ ] **US1-F-02** วี + เนท: ปุ่ม Logout เรียก AUTH-04 พร้อม CSRF, ล้างข้อมูลผู้ใช้ที่ cache ในหน้าเว็บและไป Login; response 401/403 จาก API ให้หยุดแสดงสถานะว่า login ใช้ได้
- [ ] **US1-T-01** ออสติน + พี: Scenario 1 ที่ทีมให้ — บัญชีนักศึกษาถูกต้องผ่านการตรวจจริง มี session ใหม่ เข้าหน้าหลัก/API-01 ได้ และ login ซ้ำไม่เพิ่มบัญชี
- [ ] **US1-T-02** ออสติน + พี: Scenario 2 ที่ทีมให้ — ข้อมูลผิดหรือ provider ปฏิเสธ แสดง error และไม่มี session ที่ใช้เข้าแอปได้; เริ่มทดสอบด้วย browser ที่ logout แล้ว
- [ ] **US1-T-03** เกียร์ + กอล์ฟ: ทดสอบเพิ่มเติม Logout/ยิงซ้ำ/session expiry, ไม่มีสิทธิ์นักศึกษา, inactive user, callback ปลอม/หมดอายุ/ซ้ำ, provider timeout, CSRF และ redirect ภายนอกถูกปฏิเสธ

**การปลดล็อกงาน:** เริ่ม Design, mapping และ mock-based tests ได้ก่อน credentials จริงพร้อม แต่ไม่ถือว่า integration กับมหาวิทยาลัยผ่าน และยังไม่ปิด US1 จนตรวจรับกับช่องทางที่อนุญาตจริง เก็บ provider response เฉพาะตัวอย่างที่ลบข้อมูลส่วนตัว/secret แล้ว

### งานสร้าง Party ซึ่งอยู่นอก US1

ก่อนเพิ่ม US10 ต้องมี Party ให้ทดสอบอยู่แล้ว ใช้ seed ได้ในรอบพัฒนา หากต้องการ flow สร้างนัดจริงให้ทีมกำหนดรหัส Story สร้าง Party และ scope แยกก่อน ไม่สมมติว่าเป็น US2

แบบ API ขั้นต่ำสำหรับ Story นั้น: `POST /api/v1/parties` รับ title/description/sport_id/venue_id/starts_at/ends_at/capacity; host มาจาก session US1; เรียก US9 schedule validation; สร้าง Party และ Host membership ใน transaction เดียว; 201 คืน Party; UI ใช้ส่วนเลือกสนามแล้วไปหน้ารายละเอียด งานนี้ยังไม่ committed และ US9 ส่วนเชื่อมหน้าสร้างยังต้องติดตาม dependency

## 10. US10 — แบบเทคนิคสำหรับกรณีทีมเลือกเพิ่ม

**ยังไม่ committed:** พี/กอล์ฟทำ Backend, วีทำหน้ารายการคำขอ, โกลช่วย transaction/constraint, เกียร์ช่วย concurrency tests โดยประเมิน scope ตามตาราง points ก่อนรับเพิ่ม ไม่ถือว่าตัด US8 เพียงอย่างเดียวแล้วภาระเท่าเดิม

| รหัส | Method + Path (prefix `/api/v1`) | Input / Output |
| --- | --- | --- |
| OPT-API-11 | `GET /parties/{id}/join-requests?status=Pending&page=1&page_size=20` | Host เท่านั้น; รายการ `{id,user:{id,display_name},status,created_at}`; validate status/pagination ตาม contract ร่วม |
| OPT-API-12 | `POST /parties/{id}/join-requests/{request_id}/decision` | Host เท่านั้น; `{decision:"Approved"}` หรือ `{decision:"Rejected"}`; 200 `{request:{id,status,decided_at},member_count,remaining_slots}` |

- [ ] **OPT-US10-D-01** วี + พี: หน้ารายการ Pending พร้อมปุ่มอนุมัติ/ปฏิเสธ แสดง empty/loading/error และสิทธิ์ Host
- [ ] **OPT-US10-B-01** พี + กอล์ฟ: implement OPT-API-11; ห้ามสมาชิกทั่วไปอ่านรายชื่อคำขอคนอื่น
- [ ] **OPT-US10-B-02** พี + โกล: implement decision transaction ตามลำดับด้านล่าง และบันทึก decided_by/decided_at จากเซิร์ฟเวอร์
- [ ] **OPT-US10-F-01** วี + เนท: เชื่อมสอง API; ปิดปุ่มระหว่างส่ง; success แล้วโหลดรายการ/จำนวนสมาชิกใหม่; เมื่อ conflict โหลดสถานะจริง
- [ ] **OPT-US10-T-01** เกียร์ + กอล์ฟ: ทดสอบอนุมัติ/ปฏิเสธสำเร็จ, non-host, request ข้าม Party, ตัดสินซ้ำ, Party เต็ม/เริ่ม/ยกเลิก และอนุมัติแข่งกันเมื่อเหลือหนึ่งที่

### Transaction สำหรับอนุมัติ

1. เริ่ม transaction และล็อก Party ก่อน JoinRequest เสมอ (ใช้ลำดับเดียวกันทุก service ที่แก้ข้อมูลชุดนี้)
2. ตรวจ Host และ request อยู่ใน Party นี้ จากนั้นล็อก request; ต้องเป็น Pending และ Party ยังไม่เริ่ม/ไม่ยกเลิก
3. ถ้า Approved: ตรวจผู้ขอยัง active, ไม่เป็น active member และ active count < capacity ภายใน lock; เพิ่ม/เปิด membership แล้วเปลี่ยน request เป็น Approved พร้อมกัน
4. ถ้า Rejected: เปลี่ยนเฉพาะ request ไม่เปลี่ยนสมาชิก; Party เต็มยังปฏิเสธ Pending ได้
5. commit แล้วคืนจำนวนสมาชิก/ที่ว่าง; เมื่อ request ถูกตัดสินแล้ว ตอบ 409 โดยไม่เพิ่มสมาชิกหรือเปลี่ยนคำตัดสินเดิม

Service ส่งคำขอ/แก้ไข/ยกเลิก/อนุมัติ และถอนตัวในอนาคตต้องล็อก Party แถวเดียวกัน ไม่ใช้แค่การนับก่อน transaction ทดสอบด้วย PostgreSQL และ connection แยกจริง; test แบบส่งคำขอต่อกันไม่พิสูจน์ race condition

## 11. งานเตรียม US6 / US4 สำหรับ Sprint ถัดไป

| Story | Contract ที่เสนอเมื่อเลือกทำ | สิ่งที่ต้องทดสอบก่อนถือว่าเสร็จ |
| --- | --- | --- |
| US6 | `GET /api/v1/parties/{id}/members` แบบแบ่งหน้า ส่งเฉพาะ active members `{id,display_name,role}`; เสนอให้ผู้ login อ่านได้เพื่อดูคนก่อนขอเข้าร่วม โดยทีมยืนยันสิทธิ์ก่อน | Host/Member ถูกต้อง, ไม่มี Pending/Rejected/left member, ไม่เปิดเผยข้อมูลลับ, อัปเดตหลังอนุมัติ |
| US4 | `POST /api/v1/parties/{id}/leave` ตรวจสมาชิก/ก่อนเริ่มและล็อก Party; set left_at ครั้งเดียว; ที่ว่างคำนวณจาก active count; เสนอไม่ให้ Host ถอนตัวผ่าน route นี้ | ถอนซ้ำไม่คืนที่ว่างซ้ำ, หลังเริ่มไม่ได้, Host ใช้เส้นทางยกเลิก, แข่งกับอนุมัติแล้วยังไม่เกิน capacity |

สอง Story นี้ยังไม่มี task ที่ committed ใน Sprint 1 การเตรียม schema ไม่เท่ากับส่งมอบ feature

## 12. ลำดับ PR และการติดตามงานย่อย

1. เกียร์/พีตรวจ provider US1 ตั้งแต่วันแรก ขณะเกียร์/โกลส่ง setup และ schema พื้นฐาน; สนามต้องมาก่อน migration Party ที่อ้างอิง Venue
2. พีส่ง US1 session/guard/API-01 ให้ BASE-04 ใช้; กอล์ฟ/พีตกลง error/Party service; วี/เนท/ออสตินทำ UI ด้วย fixture ตาม contract ได้ทันที
3. ส่ง US9 API + schedule service เพื่อปลดล็อก create/edit; ส่ง API-02/07/06 เป็นชิ้นงาน US3
4. ส่ง US7 และ US8 ตาม scope ปัจจุบัน หรือจัดคิว US10 ตาม scope ใหม่ที่ทีมเลือกและบันทึกไว้ก่อน
5. รวม UI กับ API จริง ทดสอบข้าม US และ concurrency แล้วจึงตรวจรับ Story ใน checklist หลัก

ทุกข้อ `[ ]` ด้านบนคือ task ย่อยที่เปิด Issue ได้ ใช้สถานะ `Todo/Doing/Review/Blocked/Done` ใน Issue หรือเพิ่มแถวในตารางนี้เมื่อเริ่มทำ ติ๊ก `[x]` หลังมี PR/หลักฐานตรวจรับ งาน parent จะ Done ต่อเมื่อ task ย่อยครบและผ่าน integration

| Task ย่อย | หลัก / ผู้ช่วย | สถานะ | วันเป้าหมาย | Issue / Branch / PR | หลักฐานทดสอบ / งานที่รอ |
| --- | --- | --- | --- | --- | --- |
| BASE-01-01 | เกียร์ / โกล | Todo | — | — | ยืนยัน stack |
| BASE-02-01 | โกล / กอล์ฟ | Todo | — | — | ยืนยันกติกาและ schema |
| US1-D-01 | พี / เกียร์ | Todo | — | — | ตรวจ provider และสิทธิ์ใช้งานจริง |
| US1-B-02 | พี / กอล์ฟ + เกียร์ | Todo | — | — | US1-D-01 และ credentials ที่ได้รับอนุญาต |
| US1-F-01 | วี / เนท | Todo | — | — | US1-D-02 และ login contract |
| US9-B1-01 | โกล / กอล์ฟ | Todo | — | — | BASE-02-01 |
| US3-B-02 | พี / กอล์ฟ | Todo | — | — | Schema, session, Party service |
| US7-B-01 | กอล์ฟ / พี | Todo | — | — | US9-B2-02 |
| US8-F-01 | เนท / วี | Todo | — | — | API-10; ยืนยันว่าจะคง US8 |
| OPT-US10-B-02 | พี / โกล | Blocked | — | — | ทีมเลือกเพิ่ม US10 ก่อน |

### หลักฐานที่ต้องแนบใน PR

- DB: migration จากฐานว่างและ seed ทำซ้ำได้; ผลตรวจ unique/FK/check และกรณีข้อมูลผิด
- API: request/response ตัวอย่างจริงของ success และ validation/permission errors; ระบุคำสั่ง test และผล
- Frontend: ภาพหน้าหรือขั้นตอนทดสอบ loading/empty/error/success และยืนยันว่าเชื่อม Backend จริงแล้ว
- Concurrency: จำนวน connection/คำขอ สถานะ response และ query ตรวจจำนวน request/member หลังจบ ไม่ใช้ screenshot หน้าเว็บอย่างเดียว
- Integration: commit ที่ทดสอบและ flow ดูสนาม → สร้าง/เปิด Party → ขอเข้าร่วม → แก้/ยกเลิก; เพิ่มอนุมัติและตรวจจำนวนสมาชิกเมื่อเลือก US10
