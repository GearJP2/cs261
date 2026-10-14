# Sprint 1 — Issue และ Branch สำหรับทีม

ใช้ **Issue เป็น backlog หลัก** สำหรับ US1/3/7/8/9, งาน BASE/INT และงานประสาน Sprint ตาม [Sprint Checklist](sprint-1-checklist.md) ณ วันที่ 14 ตุลาคม 2026

จะสร้าง branch เมื่อเจ้าของเริ่มพัฒนาจริงเท่านั้น โดยเริ่มจาก `main` ล่าสุด งานที่ยังไม่เริ่มถูกติดตามด้วย Issue เพื่อเห็น owner, dependency และเกณฑ์ปิดงานโดยไม่ต้องดูแล branch ว่างจำนวนมาก เมื่อ dependency merge เข้า `main` ให้ดึง `main` ล่าสุดก่อนเชื่อมระบบ

## เลือก Issue แล้วสร้าง branch เมื่อเริ่มงาน

| Task | ผู้รับผิดชอบหลัก / ผู้ช่วย | Issue / branch ที่ใช้เมื่อเริ่มงาน | Dependency ก่อนปิดงาน |
| --- | --- | --- | --- |
| BASE-01 | เกียร์ / โกล | `chore/base-01-project-setup` | PLAN-04 |
| BASE-02 | โกล / กอล์ฟ + เกียร์ | [PR #6](https://github.com/GearJP2/cs261/pull/6) · `feat/base-02-schema-contract` | PLAN-01,04,05 |
| BASE-03 | โกล / ออสติน | [#7](https://github.com/GearJP2/cs261/issues/7) · `chore/base-03-test-data` | BASE-01,02 |
| BASE-04 | พี / เกียร์ | [PR #4](https://github.com/GearJP2/cs261/pull/4) · `feat/base-04-shared-access` | PLAN-06, BASE-01,02 |
| US1-D | วี / พี + เกียร์ | [#8](https://github.com/GearJP2/cs261/issues/8) · `docs/us-1-d-login-design` | ตรวจ provider และช่องทางยืนยันสิทธิ์ |
| US1-B | พี / กอล์ฟ + โกล + เกียร์ | [#9](https://github.com/GearJP2/cs261/issues/9) · `feat/us-1-b-university-auth` | US1-D, BASE-01,02 และสิทธิ์เชื่อม provider |
| US1-F | วี / เนท | [#10](https://github.com/GearJP2/cs261/issues/10) · `feat/us-1-f-login-ui` | US1-D และ contract |
| US1-T | ออสติน / เกียร์ | [#11](https://github.com/GearJP2/cs261/issues/11) · `test/us-1-t-login` | US1-B,F |
| US3-D | เนท / พี | [#12](https://github.com/GearJP2/cs261/issues/12) · `docs/us-3-d-join-design` | — |
| US3-B | พี / กอล์ฟ + โกล | [#13](https://github.com/GearJP2/cs261/issues/13) · `feat/us-3-b-join-requests` | BASE-01,02,04 |
| US3-F | เนท / วี | [#14](https://github.com/GearJP2/cs261/issues/14) · `feat/us-3-f-join-ui` | US3-D และ contract; ปิดงานหลังเชื่อม US3-B |
| US3-T | ออสติน / พี | [#15](https://github.com/GearJP2/cs261/issues/15) · `test/us-3-t-join-requests` | BASE-03, US3-B,F |
| US7-D | วี / กอล์ฟ | [#16](https://github.com/GearJP2/cs261/issues/16) · `docs/us-7-d-edit-cancel-design` | PLAN-05 |
| US7-B | กอล์ฟ / พี | [#17](https://github.com/GearJP2/cs261/issues/17) · `feat/us-7-b-edit-cancel` | BASE-01,02,04, US9-B2 |
| US7-F | วี / เนท | [#18](https://github.com/GearJP2/cs261/issues/18) · `feat/us-7-f-edit-cancel-ui` | US7-D และ contract; ปิดงานหลังเชื่อม US7-B |
| US7-T | ออสติน / กอล์ฟ | [#19](https://github.com/GearJP2/cs261/issues/19) · `test/us-7-t-edit-cancel` | BASE-03, US7-B,F, US9 |
| US8-D | เนท / วี | [#20](https://github.com/GearJP2/cs261/issues/20) · `docs/us-8-d-profile-design` | — |
| US8-B | พี / กอล์ฟ | [#21](https://github.com/GearJP2/cs261/issues/21) · `feat/us-8-b-profile-api` | BASE-01,02,04 |
| US8-F | เนท / วี | [#22](https://github.com/GearJP2/cs261/issues/22) · `feat/us-8-f-profile-ui` | US8-D และ contract; ปิดงานหลังเชื่อม US8-B |
| US8-T | วี / โกล | [#23](https://github.com/GearJP2/cs261/issues/23) · `test/us-8-t-profile` | BASE-03, US8-B,F |
| US9-D | ออสติน / วี | [#24](https://github.com/GearJP2/cs261/issues/24) · `docs/us-9-d-venue-design` | — |
| US9-B1 | โกล / กอล์ฟ | [#25](https://github.com/GearJP2/cs261/issues/25) · `feat/us-9-b1-venue-database` | BASE-01,02 |
| US9-B2 | กอล์ฟ / พี + โกล | [#26](https://github.com/GearJP2/cs261/issues/26) · `feat/us-9-b2-venue-api` | US9-B1, PLAN-05 |
| US9-F | ออสติน / เนท | [#27](https://github.com/GearJP2/cs261/issues/27) · `feat/us-9-f-venue-ui` | US9-D,B2 และข้อสรุปหน้าสร้าง Party |
| US9-T | เกียร์ / โกล + กอล์ฟ | [PR #5](https://github.com/GearJP2/cs261/pull/5) · `test/us-9-t-venue-hours` | US9-B1,B2,F และหน้าที่เชื่อมต่อ |
| INT-01 | เกียร์ / ตัวแทนแต่ละคู่ | [#28](https://github.com/GearJP2/cs261/issues/28) · `chore/int-01-integration` | ทุก US ที่เลือก |
| INT-02 | เกียร์ / เจ้าของ task ที่มีบั๊ก | [#29](https://github.com/GearJP2/cs261/issues/29) · `test/int-02-regression` | INT-01 |
| INT-03 | เกียร์ / วี + เนท + ออสติน | [#30](https://github.com/GearJP2/cs261/issues/30) · `docs/int-03-demo-report` | INT-02 |
| PLAN-02–08 | เกียร์ / ตัวแทนแต่ละคู่ | [#31](https://github.com/GearJP2/cs261/issues/31) · `docs/plan-02-08-sprint-coordination` | ข้อสรุปทีม / ช่องทางยืนยันบัญชี |

PLAN-01 ยืนยัน requirement แล้วจึงไม่ต้องสร้าง Issue หรือ branch ใหม่ ส่วน PLAN-02 ถึง PLAN-08 ติดตามรวมใน Issue #31 และสร้าง branch เฉพาะเมื่อมีเอกสารที่ต้องเปลี่ยน ส่วน US10/US6/US4 ยังเป็นข้อเสนอและยังไม่อยู่ใน Sprint นี้

## งานย่อยใช้ branch ของ task หลัก

เช่น `US1-B-01` ถึง `US1-B-04` ทำใน [#9](https://github.com/GearJP2/cs261/issues/9) · `feat/us-1-b-university-auth` ถ้าคู่เดียวกันทำต่อเนื่อง ใช้ PR เดียวที่ทยอย commit ได้ หากต้องส่งบางส่วนก่อน ให้ตกลงขอบเขต PR กับผู้ช่วยและสร้าง branch ย่อยจาก main ล่าสุดเมื่อเริ่มงานนั้น

| Task หลัก | Task ย่อยใน Technical Plan |
| --- | --- |
| BASE-01 | `BASE-01-01` |
| BASE-02 | `BASE-02-01`, `BASE-02-02`, `BASE-02-03` |
| BASE-03 | `BASE-03-01` |
| BASE-04 | `BASE-04-01`, `BASE-04-02` |
| US1-D | `US1-D-01`, `US1-D-02` |
| US1-B | `US1-B-01`, `US1-B-02`, `US1-B-03`, `US1-B-04` |
| US1-F | `US1-F-01`, `US1-F-02` |
| US1-T | `US1-T-01`, `US1-T-02`, `US1-T-03` |
| US3-D | `US3-D-01` |
| US3-B | `US3-B-01`, `US3-B-02`, `US3-B-03` |
| US3-F | `US3-F-01` |
| US3-T | `US3-T-01`, `US3-T-02` |
| US7-D | `US7-D-01` |
| US7-B | `US7-B-01`, `US7-B-02` |
| US7-F | `US7-F-01` |
| US7-T | `US7-T-01`, `US7-T-02` |
| US8-D | `US8-D-01` |
| US8-B | `US8-B-01` |
| US8-F | `US8-F-01` |
| US8-T | `US8-T-01` |
| US9-D | `US9-D-01` |
| US9-B1 | `US9-B1-01` |
| US9-B2 | `US9-B2-01`, `US9-B2-02` |
| US9-F | `US9-F-01` |
| US9-T | `US9-T-01` |

## เริ่มทำงานในเครื่อง

เริ่มจากเปิด Issue ของตน ตรวจ dependency แล้วสร้าง branch จาก `main` ล่าสุด ตัวอย่าง Issue #13 (US3-B):

```bash
git switch main
git pull --ff-only
git switch -c feat/us-3-b-join-requests
git push -u origin feat/us-3-b-join-requests
```

ใช้ชื่อ branch ที่เสนอในตารางได้ แต่ยังไม่ต้องสร้างจนกว่าจะเริ่มงานจริง `git switch` สลับ branch เช่นเดียวกับ `git checkout` จึงไม่ต้องใช้ทั้งสองคำสั่ง เมื่อเปิด PR ให้ใส่ `Closes #13` (แทนเลข Issue ของงาน) เพื่อให้ Issue ปิดอัตโนมัติหลัง Squash and merge

## อัปเดต dependency จาก main

หลังงานพื้นฐานหรือ API ที่ต้องใช้ merge แล้ว ให้บันทึกงานค้าง จาก branch งานของตนรัน:

```bash
git fetch origin
git merge origin/main
```

แก้ conflict ร่วมกับเจ้าของส่วนที่ชนและทดสอบใหม่ก่อน push อย่า merge branch ของเพื่อนที่ยังไม่ผ่าน review เพื่อข้ามขั้นตอน หากต้องทดสอบงานสองส่วนก่อน merge ให้ประสานเกียร์ใช้ INT-01 เป็นจุดทดลองรวม และเปิด PR ของแต่ละ task เข้าสู่ main ตามปกติ

INT-01 เป็น branch งานทดสอบรวมชั่วคราว ไม่ใช่ base ถาวรของทีม การมี branch ทดสอบแยกไม่ยกเว้นให้ผู้เขียน Backend/Frontend ส่งงานโดยไม่มี tests ของตัวเอง

## Commit, push และเปิด PR

```bash
git diff
git add path/to/file
git diff --cached
git diff --cached --check
git commit -m "feat(auth): add verified student session"
git push
```

ใช้ `path/to/file` จริงของงาน และ commit ทีละไฟล์ตามแนวทางที่เกียร์ขอไว้สำหรับการเตรียมงานชุดนี้ เปิด PR จาก task branch เข้า `main` โดยระบุรหัส task, สิ่งที่เปลี่ยน, วิธีทดสอบและผลจริง พร้อมผู้ตรวจที่ไม่ได้ร่วมเขียนอย่างน้อยหนึ่งคน ใช้ Conventional Commits และ Squash and merge ตาม [README](../README.md)

อย่าเปิด PR หรือสร้าง branch เปล่าเพื่อจองงาน ให้เริ่มส่ง PR เมื่อมีงานที่ตรวจได้ หาก PR ถูก squash merge และทีมลบ remote branch แล้ว ให้จบ branch นั้นและแตก branch งานถัดไปจาก main ล่าสุด

## ทำงานเป็นคู่

- กอล์ฟกับพีใช้ branch Backend ตามงาน สลับคนเขียน/ตรวจ ถ้า push branch เดียวกันให้แจ้งอีกคนและ `git pull --ff-only` ก่อนเริ่มรอบใหม่
- วี/เนท/ออสตินใช้ branch Design/Frontend/Testing ของตน โดยอิง contract เดียวกับ Backend
- โกลเริ่ม schema และสนาม ประสานลำดับ migrations โดยเฉพาะ Venue ที่ Party จะอ้างอิง
- เกียร์เริ่ม BASE-01 และช่วยรวมระบบ/review ผู้ที่แก้ migration หรือข้อมูลร่วมต้องแจ้งโกลก่อน
- ถ้าเกิด non-fast-forward ให้ดึงและรวมงานที่เกี่ยวข้อง อย่า force push ไปทับ branch ที่ทีมใช้ร่วมกัน

## ลำดับเริ่มงานที่แนะนำ

1. เกียร์/โกล: BASE-01 setup; พี/เกียร์: ตรวจช่องทางมหาวิทยาลัยใน US1-D; วี/เนท/ออสติน: Design แต่ละหน้า
2. โกล/กอล์ฟ/พี: BASE-02 schema/contract และ US9-B1 สนาม ก่อน migration Party ที่อ้างถึง Venue
3. พี: US1-B และ BASE-04; กอล์ฟ: US9-B2; โกล/ออสติน: BASE-03 seed
4. แบ่งทำ US3/7/8 API และหน้าเว็บ; US7 ต้องรอตัวตรวจเวลาจาก US9
5. ทดสอบราย task แล้วรวม flow ใน INT-01, regression ใน INT-02 และเอกสารเดโมใน INT-03

## สถานะ development runtime

BASE-01 ถูก merge แล้ว: repository ใช้ Django 5.2, PostgreSQL 17 และ Docker Compose ชุดเดียวกัน ดูคำสั่งติดตั้งและตรวจระบบใน [Development Guide](development.md) ก่อนเริ่ม task ใหม่ ให้สร้าง branch จาก `main` ล่าสุดเพื่อรับ environment และ dependency ที่ผ่าน review แล้ว

ค่าบัญชีมหาวิทยาลัยและ secrets ตั้งในเครื่องหรือช่องทางที่ทีมกำหนด ห้ามแนบใน commit ไฟล์เอกสารส่วนตัวที่อยู่นอก task ให้เลือก stage แยกอย่างระมัดระวัง
