# INT-02 — Sprint 1 API regression report

บันทึกนี้เป็นหลักฐานการตรวจ API integration สำหรับ Issue #29 ณ วันที่ 2026-10-20 ไม่ใช่ผลตรวจ UI หรือการเชื่อมต่อ TU provider จริง

## ขอบเขตที่ตรวจแล้ว

`backend/core/test_sprint_integration.py` รัน flow ต่อเนื่องด้วย Django test client ที่เปิดใช้ CSRF middleware:

1. สร้าง session จำลองของบัญชีมหาวิทยาลัยที่ยืนยันแล้วสำหรับ Host และ Applicant
2. อ่านรายการกีฬาและสนามที่รองรับกีฬาผ่าน API US9
3. Host สร้าง Party ผ่าน API US7
4. ตรวจ Host membership, `member_count=1` และ `remaining_slots=capacity-1`
5. Applicant ส่ง Join Request ผ่าน API US3 และมีสถานะ `Pending` โดยไม่เพิ่ม membership
6. Applicant แก้ไข Party ไม่ได้ (`403`)
7. Host แก้ไขและยกเลิก Party สำเร็จผ่าน API US7

## ผลตรวจ

บน branch `test/int-02-api-flow` หลัง commit `49aaa87`:

```text
make verify
275 tests passed
```

คำสั่งนี้ครอบคลุม Django system check, migration dry-run, Ruff lint/format และ Django tests บน PostgreSQL ใน Docker

## สิ่งที่ยังไม่ถือว่าผ่าน

- UI flow ของ US3-F, US7-F และ US9-F ยังไม่พร้อม จึงยังไม่ได้ browser/E2E test
- TU provider จริงยังรอ credential/ช่องทางจากมหาวิทยาลัย; test นี้ใช้ verified session fixture และไม่อ้างว่าเป็นการยืนยันบัญชี TU จริง
- INT-02 จะปิดได้หลังรัน flow ผ่าน UI บน commit เดียวกัน และบันทึกผล regression ซ้ำ
