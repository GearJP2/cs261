# INT-01 — แผนรวมระบบ Sprint 1

เจ้าของการประสาน: เกียร์
ผู้ร่วมตรวจ: เจ้าของ US1, US3, US7, US8 และ US9

เอกสารนี้เป็นแผนและบันทึกผลสำหรับ Issue #28 ไม่ใช่หลักฐานว่า flow ผ่านแล้ว

## เงื่อนไขก่อนเริ่มรันรวม

1. `main` ต้องมี PR ที่ review ผ่านและ CI เขียวของส่วนที่เกี่ยวข้อง
2. รับ PR #47 ก่อน เพื่อแก้ regression ของ profile tests แล้วรัน `make verify` บนฐานเดียวกัน
3. PR #48 ต้องแก้ validation ของ `capacity` ที่เกินช่วง `IntegerField` และรัน `make verify` ผ่านก่อนรับ
4. เจ้าของ US7-F และ US9-F ต้องระบุ URL/วิธีเปิดหน้าสร้าง Party และหน้า detail ที่เชื่อม API จริง
5. TU API ยังรอการอนุมัติ จึงแยกผลเป็น `fixture session` กับ `TU provider จริง` เสมอ ห้ามนับ fixture เป็นการตรวจรับ US1

## ลำดับรวมงาน

| ลำดับ | สิ่งที่ต้องพร้อม | ผู้ตรวจหลัก | เกณฑ์ผ่าน |
| --- | --- | --- | --- |
| 1 | `make verify` บน main | เกียร์ | Django checks, migration, lint และ tests ทั้งหมดผ่าน |
| 2 | กีฬา/สนาม/เวลาเปิด US9 | โกล + กอล์ฟ | API กีฬา สนาม และ opening hours คืนข้อมูลตาม contract |
| 3 | สร้าง Party US7 | กอล์ฟ + พี | สร้าง Party และ Host membership ใน transaction เดียว; capacity/เวลา/สนามผิดไม่สร้างข้อมูลค้าง |
| 4 | รายละเอียด Party และ Join Request US3 | พี + เนท | ผู้ใช้อีกบัญชีส่ง Pending ได้หนึ่งรายการ; Pending ไม่ลดที่ว่าง |
| 5 | แก้ไข/ยกเลิก US7 | กอล์ฟ + วี | Host เท่านั้นทำได้; Cancelled ปฏิเสธคำขอใหม่ |
| 6 | Profile US8 | พี + เนท | เปิด profile ที่ถูกคน และไม่ส่งข้อมูลลับ |
| 7 | Login/Logout US1 | พี + ออสติน | แยกผล fixture session กับ TU provider จริง; ส่วนหลังยัง Blocked จน provider พร้อม |

## ข้อมูลทดสอบขั้นต่ำ

- `host`: account ที่มี university identity/session สำหรับทดสอบในระบบ
- `applicant`: identity/session คนละบัญชีกับ host
- กีฬาและสนาม active ที่มีช่วงเปิดครอบคลุมเวลานัด
- สนาม inactive หรือกีฬาที่ไม่ match อย่างน้อยหนึ่งชุด
- Party เริ่มในอนาคต และ capacity 2 เพื่อเห็น Pending โดยที่ remaining slots ไม่เปลี่ยน

ห้ามใส่ TU credential, cookie, session key หรือข้อมูลนักศึกษาจริงในเอกสาร, issue, screenshot หรือ seed

## Flow ที่ต้องบันทึกผล

| ID | ขั้นตอน | ผลที่ต้องตรวจ | เจ้าของเมื่อ Fail |
| --- | --- | --- | --- |
| INT-01-A | เปิด sport → venue → opening hours | เปลี่ยนกีฬาแล้วสนามเดิมถูกล้าง; response เก่าไม่ทับค่าใหม่ | US9-F |
| INT-01-B | Host สร้าง Party ในช่วงเปิด | 201; Host เป็น active member; `member_count=1`; `remaining_slots=capacity-1` | US7-B/F |
| INT-01-C | applicant ส่ง Join Request | Pending หนึ่งแถว; membership/capacity/remaining slots ไม่เปลี่ยน | US3-B/F |
| INT-01-D | Host เปลี่ยน venue หรือเวลา | validate ค่าเดิมที่ merge แล้ว; นอกเวลาไม่บันทึก; ข้อมูลถูกต้องบันทึกได้ | US7-B + US9 |
| INT-01-E | Host ยกเลิก Party | เก็บสมาชิก/คำขอเดิม; applicant ส่งคำขอใหม่ได้ `PARTY_CANCELLED` | US7-B + US3-B |
| INT-01-F | เปิด Profile ของ Host/applicant | ตรง user; ไม่มี email, username, token หรือ session | US8-B/F |
| INT-01-G | logout แล้วเรียก write API | session เดิมถูกปฏิเสธ; ระบุว่า fixture หรือ provider จริง | US1 + เจ้าของ API |

## วิธีรันและบันทึก

1. เริ่มจาก `main` ล่าสุดและใช้ Docker project ใหม่ตาม [Development guide](development.md)
2. รัน `make verify`, `make up`, และ `make smoke`
3. ทำ flow A–G ด้วย browser/HTTP client ตามหน้าที่พร้อมจริง
4. บันทึก commit, ผล `Pass`/`Fail`/`Blocked`, หลักฐานที่ลบข้อมูลส่วนตัวแล้ว และ Issue ของบั๊ก
5. หากพบ bug ที่ขัด acceptance criteria ให้เปิด Issue แยกและ assign เจ้าของ US; อย่าแก้ข้าม branch ของเพื่อนโดยไม่ตกลง

## ตารางผลจริง

| Flow | Commit ที่ทดสอบ | ผล | หลักฐาน / Issue | หมายเหตุ |
| --- | --- | --- | --- | --- |
| INT-01-A | — | Not run | — | รอ US9-F |
| INT-01-B | — | Not run | — | รอ PR #48 พร้อม merge และ US7-F |
| INT-01-C | — | Not run | — | รอ US3-F |
| INT-01-D | — | Not run | — | รอ US7-F |
| INT-01-E | — | Not run | — | รอ US7-F |
| INT-01-F | — | Not run | — | รอ US8-F ที่ใช้ข้อมูลจริง |
| INT-01-G | — | Blocked | — | รอ TU API/ช่องทางที่อนุมัติ |
