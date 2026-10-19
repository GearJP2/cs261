# US9-B1-01 — ข้อมูลสนาม กีฬา และเวลาเปิดบริการ

งานของโกล/กอล์ฟตาม [Issue #25](https://github.com/GearJP2/cs261/issues/25) และ [Technical Plan](sprint-1-technical-plan.md) หัวข้อ 3 และ 5 ใช้ schema ที่ BASE-02 merge แล้ว ไม่สร้างตารางหรือ migration ซ้ำ และไม่ต้องรอ BASE-03

## รันข้อมูลตัวอย่าง

```bash
docker compose run --rm -T backend python backend/manage.py migrate
docker compose run --rm -T backend python backend/manage.py seed_venues
```

ใช้ `.env` ตามคู่มือ development และ `DEBUG=true` เท่านั้น คำสั่งไม่รันอัตโนมัติเมื่อเปิดระบบ ใช้ชื่อกีฬาและสนามจริงของ **มธ. ศูนย์รังสิต** พร้อมแยกแหล่งที่มาของชื่อและเวลา ตรวจเว็บวันที่ **18 ตุลาคม 2569**

| สถานที่ (ชื่อจริง / REAL) | กีฬา | ตารางเวลา | ที่มาของเวลา |
| --- | --- | --- | --- |
| สนามแบดมินตัน ยิมเนเซียม 4 | แบดมินตัน | ทุกวัน 17:00–21:00 | REAL ตามเว็บ [PSM แบดมินตัน](https://psm.tu.ac.th/our-services/facilities-services/sports-center-11/) |
| สนามแบดมินตัน ยิมอินเตอร์โซน | แบดมินตัน | อาทิตย์–ศุกร์ 16:00–21:00; เสาร์ไม่อยู่ในตารางที่ประกาศ | REAL ตามเว็บ PSM แบดมินตัน |
| สระว่ายน้ำ ศูนย์กีฬาทางน้ำ | ว่ายน้ำ | ทุกวัน 07:00–21:00 | REAL ตามเว็บ [PSM สระว่ายน้ำ](https://psm.tu.ac.th/our-services/facilities-services/sports-center-13/) |
| สนามเทนนิส | เทนนิส | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |
| สนามสควอช ยิมเนเซียม 7 | สควอช | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |
| สนามพิกเคิลบอล | พิกเคิลบอล | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |
| สนามบาสเกตบอล | บาสเกตบอล | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |
| สนามฟุตบอลหญ้าเทียม | ฟุตบอล | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |
| สนามฟุตซอล | ฟุตซอล | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |
| สนามซอฟท์บอล | ซอฟท์บอล | จันทร์–เสาร์ 16:00–21:00; อาทิตย์ปิด | **MOCK ทั้งเวลาและวันหยุด** |

ชื่อเทนนิส/สควอช/พิกเคิลบอลอ้างอิง [ระบบจองสนาม PSM](https://psm.tu.ac.th/booking-court/); ชื่อบาสเกตบอล/ฟุตบอลหญ้าเทียม/ฟุตซอล/ซอฟท์บอลอ้างอิง [รายการสถานที่ PSM](https://psm.tu.ac.th/our-services/facilities-services/) ไม่ได้อ้างว่าเว็บเหล่านี้ประกาศเวลา mock ข้างต้น

REAL หมายถึงข้อมูลที่เว็บทางการเผยแพร่ ไม่ใช่การยืนยันว่าตารางยังใช้ได้ทุกวันหรือคอร์ทว่างจริง บางเว็บของมหาวิทยาลัยแสดงเวลาแบดมินตันต่างกัน ชุดนี้เลือกเว็บผู้ดูแลสนาม PSM และบันทึกวันที่ตรวจ; วันหยุดพิเศษ/งานแข่งขันต้องตรวจประกาศเพิ่ม `is_active=true` ของทั้งสิบสนามเป็น **ค่าตั้งต้นทดสอบ** ไม่ใช่สถานะเปิดจริงแบบเรียลไทม์

ไฟล์ [venue_catalog.py](../backend/venues/venue_catalog.py) ระบุ `venue_kind`, `venue_source`, `hours_kind`, `hours_source`, `checked_on` แยกรายสนาม โดยเวลา MOCK มี `hours_source=None` และไม่ปลอมแหล่งอ้างอิง ส่วนฐานข้อมูลใช้ `Venue.location_text` แสดง `สถานที่: REAL; เวลา: REAL (ตามเว็บ PSM)` หรือ `เวลา: MOCK (เวลาสมมติ)` เพื่อให้เห็นป้ายผ่าน field เดิมของ API-04 โดยไม่เปลี่ยน schema; ฝั่ง #27 ต้องแสดง location_text/ป้ายนี้เมื่อแสดงเวลาจริงกับ mock แก่ผู้ใช้

ได้ 9 Sport, 10 Venue, 10 VenueSport และ 62 VenueOpeningHour; ไม่มีสนาม inactive ที่สมมติชื่อขึ้นมาใน catalog แล้ว ใช้ fixture ใน tests สำหรับ inactive/หลายกีฬา/ช่วงพักต่อไป

รันซ้ำได้โดยไม่เพิ่ม Sport/Venue ซ้ำและคง ID ของทั้งสองตาราง แต่จะสร้าง VenueSport/OpeningHour ของสิบสนามใน catalog ใหม่เพื่อคืนค่า จึงห้ามผูก fixture/API test กับเลข ID ของแถวเหล่านั้น คำสั่งแสดง `venue_id` และ REAL/MOCK ที่ได้จริง หาข้อมูลจากชื่อหรือ FK ห้ามสมมติว่า ID เริ่มที่ 1

คำสั่งแก้เฉพาะสนามตามชื่อข้างต้นที่มี `location_text` ขึ้นต้น `มธ. ศูนย์รังสิต | [US9-CATALOG] ` หากชื่อชนกับข้อมูลอื่นหรือมีสนามชื่อสงวนซ้ำ จะหยุดและ rollback ทั้งชุด ไม่แตะสนามทั่วไปหรือชุด `[BASE-03]`; ไม่สร้าง User, Party, Membership หรือ JoinRequest ถ้าเคยรัน seed เวอร์ชัน mock เดิม `[US9]` มาก่อน แถวเก่าจะยังอยู่ ไม่ลบทิ้งอัตโนมัติ

ชุด `seed_demo` ของ BASE-03 ใช้ทดสอบ flow สมาชิก/Party ต่อไป ส่วน `seed_venues` ใช้ข้อมูลอ้างอิง US9 ที่แยกจริง/mock จึงอยู่ร่วมกันได้โดยไม่ต้อง cherry-pick BASE-03

## Data contract สำหรับ US9-B2 / US7

- `Sport.name`: ความยาวสูงสุด 80, unique
- `Venue`: name 150, location_text 255 และ is_active; ใช้ schema เดิม ไม่มีคอลัมน์ประเภทสนามเพิ่ม ไม่เดาประเภท indoor/outdoor เมื่อแหล่งข้อมูลยังไม่ยืนยัน
- `VenueSport`: FK สนาม/กีฬาและ unique `(venue_id, sport_id)`; `sport_id` มี index จาก Django ForeignKey รองรับการค้นสนามตามกีฬา
- `VenueOpeningHour`: weekday 0–6 (จันทร์–อาทิตย์), opens_at < closes_at และ unique `(venue_id, weekday, opens_at)`; หนึ่งวันมีหลายช่วงได้ **ไม่มีแถวของวันนั้นหมายถึงปิด**
- เวลาเปิด–ปิดเป็น local wall time ของ `Asia/Bangkok`; เวลาเริ่ม/จบ Party ต้องรับ offset แล้วแปลง timezone ก่อนเทียบ
- ลบ Venue ที่ยังไม่มี Party อ้างอิงแล้ว configuration ตามไปด้วย (`CASCADE`); Sport ที่มี VenueSport และ Venue/Sport ที่มี Party อ้างอิงลบไม่ได้ (`PROTECT`) ใช้ `Venue.is_active=false` เมื่อต้องปิดสนามที่มีประวัติ
- constraint ฐานข้อมูลไม่ได้กันช่วงเปิดซ้อนกันหรือยืนยันว่า Party อยู่ครบในช่วงเปิด: shared validator/บริการแก้ configuration ใน US9-B2 ต้องตรวจเพิ่มเติม ไม่ใช้การผ่าน schema tests เป็นหลักฐานว่า endpoint หรือ schedule validation เสร็จแล้ว

Migration ที่มีแล้วคือ `venues/0001_initial.py`; `parties/0001_initial.py` และ `accounts/0003_usersportinterest.py` อ้างอิง migration นี้ ไม่มีการแก้ migration ที่ทีมใช้งานไปแล้ว

## ตรวจรับ

```bash
docker compose run --rm -T backend python backend/manage.py test venues --noinput --verbosity 2
make verify
```

Tests ใช้ PostgreSQL และสร้างข้อมูลของตนเอง ไม่ต้อง seed ก่อน ครอบคลุม FK ที่ไม่มี parent, unique กีฬา/คู่สนามกีฬา/จุดเริ่มเวลา, weekday และลำดับเวลา, หลายช่วงในวันเดียว, delete policy และ seed ที่ทำซ้ำได้/rollback/ไม่แตะข้อมูลอื่น

การส่งงาน: เปิด PR จาก `feat/us-9-b1-venue-database` พร้อม `Closes #25` และผลตรวจจริง งาน API-03/04/05 และ `validate_party_schedule` เป็นของ US9-B2 (#26); หน้าเลือกสนามเป็น #27
