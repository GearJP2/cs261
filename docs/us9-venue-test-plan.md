# US9-T — แผนทดสอบสนามและเวลาเปิดบริการ

เจ้าของงาน: เกียร์

ผู้ช่วยตรวจ: โกล (ข้อมูลสนาม) และกอล์ฟ (API/validation)

สถานะ: **Blocked** จนกว่า `US9-B1`, `US9-B2` และ `US9-F` จะ merge เข้า `main`

เอกสารนี้เตรียมกรณีทดสอบของ `US9-T-01` ตาม [Technical Plan](sprint-1-technical-plan.md#5-us9--สนามและเวลาเปิดให้บริการ) โดยยังไม่อ้างว่า API หรือ service มีอยู่แล้ว ห้ามปิด task นี้จากเอกสารฉบับนี้เพียงอย่างเดียว

## Contract ที่ต้องมีให้ทดสอบ

- `GET /api/v1/sports` (API-03)
- `GET /api/v1/venues?sport_id=<id>&page=<n>&page_size=<n>` (API-04)
- `GET /api/v1/venues/<venue_id>/opening-hours` (API-05)
- `validate_party_schedule(sport_id, venue_id, starts_at, ends_at)` ที่ถูกเรียกจาก service สร้างและแก้ Party

ทุก API ต้องมี session ที่ผ่านการยืนยัน, ตอบ JSON รูปแบบ `{"data": ...}` เมื่อสำเร็จ และ error envelope ตาม Technical Plan เมื่อผิดเงื่อนไข

## Fixture ขั้นต่ำ

ใช้ migration/fixture ของ `US9-B1` สร้างข้อมูลแยกสำหรับ test database ดังนี้ ไม่ใช้ seed ที่ขึ้นกับเวลาปัจจุบัน

| รหัส | ข้อมูล | วัตถุประสงค์ |
| --- | --- | --- |
| `badminton` | กีฬา Badminton | กีฬาอ้างอิงหลัก |
| `basketball` | กีฬา Basketball | ตรวจสนามไม่รองรับกีฬา |
| `active_venue` | สนาม active รองรับ Badminton; เปิดวันจันทร์ 06:00–08:00 และ 17:00–22:00; วันอังคารไม่มีช่วงเปิด | boundary, ช่วงพัก และวันปิด |
| `other_venue` | สนาม active รองรับ Basketball เท่านั้น | ตรวจ mapping สนาม–กีฬา |
| `inactive_venue` | สนาม inactive รองรับ Badminton | ตรวจห้ามใช้งานสนาม inactive |

เวลาทดสอบใช้ `Asia/Bangkok` พร้อม offset `+07:00` และวันจันทร์ `2026-10-12` เพื่อให้ผลคงที่ ไม่ใช้ datetime แบบ naive

## กรณีทดสอบที่ต้องเขียน

| ID | ชั้นทดสอบ | กรณี | ผลที่คาดหวัง |
| --- | --- | --- | --- |
| US9-T-01 | API-03 | เรียก `/sports` ด้วย session ที่ใช้ได้ | `200`; มีเฉพาะ `id`, `name` ในรายการกีฬา |
| US9-T-02 | API-04 | ขอสนามด้วย `sport_id=badminton` | `200`; พบ `active_venue`; ไม่พบ `other_venue` และ `inactive_venue` |
| US9-T-03 | API-04 | ขาด `sport_id`, ID ไม่ใช่จำนวนเต็ม, page/page_size ไม่ถูกต้อง หรือ page_size เกิน 100 | `400` พร้อม error envelope; ไม่คืนรายการกว้าง ๆ แทน input ที่ผิด |
| US9-T-04 | API-04 | ตรวจ page 1/page_size 1 และ total | `200`; `data`, `page`, `page_size`, `total` ตรง contract และไม่ซ้ำข้ามหน้า |
| US9-T-05 | API-05 | อ่านเวลาเปิดของ `active_venue` | `200`; `timezone` เป็น `Asia/Bangkok`; มีช่วงจันทร์ 06:00–08:00 และ 17:00–22:00; วันอังคารไม่มี interval |
| US9-T-06 | API-05 | ID ไม่มีอยู่ | `404` พร้อม `NOT_FOUND` envelope |
| US9-T-07 | service | Badminton ที่ `active_venue`, 06:00–08:00 วันจันทร์ | ผ่าน: boundary เริ่มและจบเท่าช่วงเปิดอนุญาต |
| US9-T-08 | service | 05:59–07:00 หรือ 21:00–22:01 วันจันทร์ | ปฏิเสธ `VENUE_CLOSED` |
| US9-T-09 | service | 07:30–17:30 วันจันทร์ | ปฏิเสธ `VENUE_CLOSED`; ห้ามรวมสองช่วงเปิดข้ามเวลาปิดเป็นช่วงเดียว |
| US9-T-10 | service | 17:00–18:00 วันอังคาร | ปฏิเสธ `VENUE_CLOSED` เพราะไม่มีช่วงเปิด |
| US9-T-11 | service | Basketball ที่ `active_venue` หรือ Badminton ที่ `other_venue` | ปฏิเสธ `INVALID_INPUT` ตาม error code ที่ backend ตกลง; ไม่ผ่านเพียงเพราะเวลาเปิด |
| US9-T-12 | service | Badminton ที่ `inactive_venue` | ปฏิเสธ `INVALID_INPUT` หรือ code เฉพาะสนาม inactive ที่ตกลงก่อน implement; ต้องไม่อนุญาตให้สร้าง/แก้ Party |
| US9-T-13 | service | `starts_at >= ends_at`, datetime ไม่มี offset หรือข้ามวัน | ปฏิเสธ `INVALID_TIME_RANGE` หรือ `INVALID_INPUT`; ไม่แก้ timezone ให้เงียบ ๆ |
| US9-T-14 | integration | สร้าง Party และ PATCH แก้ Party ให้เข้าสู่กรณี US9-T-07 ถึง US9-T-13 | create/edit เรียก validator ตัวเดียวกันและให้ผลเท่ากัน |
| US9-T-15 | UI | เลือกกีฬา → สนาม → ดูเวลาเปิด; เปลี่ยนกีฬาเร็ว | UI ล้างสนามที่ไม่รองรับ, แสดง loading/empty/error และ response เก่าไม่ทับตัวเลือกใหม่ |

## วิธีทดสอบหลัง dependency พร้อม

1. รวม `main` ล่าสุดเข้า branch และยืนยัน migration จากฐานข้อมูลทดสอบว่างผ่าน `make check`.
2. เขียน Django tests ใกล้ service/API ที่เจ้าของ `US9-B1/B2` เพิ่มไว้; test ต้องสร้าง fixture ของตนเองและไม่พึ่งข้อมูลจาก development volume.
3. รัน `make test` และ `make lint`.
4. รันบริการด้วย `make up`; ใช้ session dev ที่ BASE-04 กำหนดเท่านั้น แล้วเรียก API-03–05 เพื่อยืนยัน response จริง.
5. เมื่อมีหน้าสร้างหรือแก้ Party จริง ให้ทำ US9-T-14 และ US9-T-15; แนบคำสั่ง ผลจริง และ commit ที่ทดสอบใน PR.

## เงื่อนไขก่อนเปลี่ยนเป็น Review

- `US9-B1` มี migration และ fixture test สำหรับ Venue/VenueSport/VenueOpeningHour
- `US9-B2` มีสาม endpoint และ schedule validator
- team ยืนยัน error code สำหรับสนามไม่รองรับกีฬาและสนาม inactive
- มี service สร้าง/แก้ Party อย่างน้อยหนึ่งจุดที่เรียก validator เดียวกัน
- หน้าสนามของ `US9-F` เชื่อม API จริงแล้วสำหรับกรณี UI
