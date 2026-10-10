# Sprint 1 — Branch สำหรับทีม

เตรียม branch สำหรับ **US1/3/7/8/9**, งาน BASE/INT และงานประสาน Sprint ตาม [Sprint Checklist](sprint-1-checklist.md) รวม **29 task branches** จาก `main` commit `0158d0e22b5e069db49452444d7f036d796dc963` ณ วันที่ 10 ตุลาคม 2026

Branch ของแต่ละ task เริ่มจากโค้ดและเอกสารฐานเดียวกัน ข้อมูลนี้เป็นการเตรียมพื้นที่ทำงาน ไม่ใช่หลักฐานว่า task เสร็จแล้ว เมื่อ task ที่เป็น dependency merge เข้า main ให้ดึงเข้ามาก่อนเชื่อมระบบ

## เลือก branch ตามงาน

| Task | ผู้รับผิดชอบหลัก / ผู้ช่วย | Branch | Dependency ก่อนปิดงาน |
| --- | --- | --- | --- |
| BASE-01 | เกียร์ / โกล | `chore/base-01-project-setup` | PLAN-04 |
| BASE-02 | โกล / กอล์ฟ + เกียร์ | `feat/base-02-schema-contract` | PLAN-01,04,05 |
| BASE-03 | โกล / ออสติน | `chore/base-03-test-data` | BASE-01,02 |
| BASE-04 | พี / เกียร์ | `feat/base-04-shared-access` | PLAN-06, BASE-01,02 |
| US1-D | วี / พี + เกียร์ | `docs/us-1-d-login-design` | ตรวจ provider และช่องทางยืนยันสิทธิ์ |
| US1-B | พี / กอล์ฟ + โกล + เกียร์ | `feat/us-1-b-university-auth` | US1-D, BASE-01,02 และสิทธิ์เชื่อม provider |
| US1-F | วี / เนท | `feat/us-1-f-login-ui` | US1-D และ contract |
| US1-T | ออสติน / เกียร์ | `test/us-1-t-login` | US1-B,F |
| US3-D | เนท / พี | `docs/us-3-d-join-design` | — |
| US3-B | พี / กอล์ฟ + โกล | `feat/us-3-b-join-requests` | BASE-01,02,04 |
| US3-F | เนท / วี | `feat/us-3-f-join-ui` | US3-D และ contract; ปิดงานหลังเชื่อม US3-B |
| US3-T | ออสติน / พี | `test/us-3-t-join-requests` | BASE-03, US3-B,F |
| US7-D | วี / กอล์ฟ | `docs/us-7-d-edit-cancel-design` | PLAN-05 |
| US7-B | กอล์ฟ / พี | `feat/us-7-b-edit-cancel` | BASE-01,02,04, US9-B2 |
| US7-F | วี / เนท | `feat/us-7-f-edit-cancel-ui` | US7-D และ contract; ปิดงานหลังเชื่อม US7-B |
| US7-T | ออสติน / กอล์ฟ | `test/us-7-t-edit-cancel` | BASE-03, US7-B,F, US9 |
| US8-D | เนท / วี | `docs/us-8-d-profile-design` | — |
| US8-B | พี / กอล์ฟ | `feat/us-8-b-profile-api` | BASE-01,02,04 |
| US8-F | เนท / วี | `feat/us-8-f-profile-ui` | US8-D และ contract; ปิดงานหลังเชื่อม US8-B |
| US8-T | วี / โกล | `test/us-8-t-profile` | BASE-03, US8-B,F |
| US9-D | ออสติน / วี | `docs/us-9-d-venue-design` | — |
| US9-B1 | โกล / กอล์ฟ | `feat/us-9-b1-venue-database` | BASE-01,02 |
| US9-B2 | กอล์ฟ / พี + โกล | `feat/us-9-b2-venue-api` | US9-B1, PLAN-05 |
| US9-F | ออสติน / เนท | `feat/us-9-f-venue-ui` | US9-D,B2 และข้อสรุปหน้าสร้าง Party |
| US9-T | เกียร์ / โกล + กอล์ฟ | `test/us-9-t-venue-hours` | US9-B1,B2,F และหน้าที่เชื่อมต่อ |
| INT-01 | เกียร์ / ตัวแทนแต่ละคู่ | `chore/int-01-integration` | ทุก US ที่เลือก |
| INT-02 | เกียร์ / เจ้าของ task ที่มีบั๊ก | `test/int-02-regression` | INT-01 |
| INT-03 | เกียร์ / วี + เนท + ออสติน | `docs/int-03-demo-report` | INT-02 |
| PLAN-02–08 | เกียร์ / ตัวแทนแต่ละคู่ | `docs/plan-02-08-sprint-coordination` | ข้อสรุปทีม / ช่องทางยืนยันบัญชี |

PLAN-01 ยืนยัน requirement แล้วจึงไม่ต้องสร้าง branch ใหม่ งาน PLAN-02 ถึง PLAN-08 ใช้ branch ประสานงานร่วมกัน ส่วน US10/US6/US4 ยังเป็นข้อเสนอและยังไม่สร้าง branch ใน Sprint นี้

## งานย่อยใช้ branch ของ task หลัก

เช่น `US1-B-01` ถึง `US1-B-04` ทำใน `feat/us-1-b-university-auth` ถ้าคู่เดียวกันทำต่อเนื่อง ใช้ PR เดียวที่ทยอย commit ได้ หากต้องส่งบางส่วนก่อน ให้ตกลงขอบเขต PR กับผู้ช่วยและสร้าง branch ย่อยจาก main ล่าสุดเมื่อเริ่มงานนั้น

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

หากยังไม่มี repository:

```bash
git clone https://github.com/GearJP2/cs261.git
cd cs261
```

สำหรับคนที่มี repository อยู่แล้ว ให้ commit งานค้างใน branch เดิมให้เรียบร้อยก่อนสลับ จากนั้นตัวอย่างนี้เลือก Backend Login ของพี:

```bash
git status
git fetch origin
git switch --track origin/feat/us-1-b-university-auth
```

คำสั่ง `switch --track` ใช้ครั้งแรกบนเครื่องที่ยังไม่มี local branch ชื่อนี้ ครั้งถัดไปใช้:

```bash
git switch feat/us-1-b-university-auth
git pull --ff-only
```

แทนชื่อ branch ด้วยงานของตนจากตาราง `git switch` สลับ branch เช่นเดียวกับ `git checkout` จึงไม่ต้องเรียกทั้งสองคำสั่ง และไม่ต้องแตก branch ชื่อซ้ำด้วย `-c` เพราะทีมเตรียม remote branch ไว้แล้ว

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

Branch ที่ยังไม่มี commit ต่างจาก main ยังเปิด PR ไม่ได้ ให้เริ่มส่ง PR เมื่อมีงานที่ตรวจได้ หาก PR ถูก squash merge และทีมลบ remote branch แล้ว ให้จบ branch นั้นและแตก branch งานถัดไปจาก main ล่าสุด

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

ตอนสร้าง branch โครง app ยังมีไฟล์ตั้งค่าที่ว่าง เช่น `backend/package.json` และ `frontend/package.json` และยังไม่มี Django app/dependency manifest ที่รันได้ Docker Compose/Dockerfile ที่มีอยู่ยังเป็น template จึงยังไม่ใช่ environment ที่ใช้คำสั่งเดียวแล้วเปิดแอปได้

งานทำให้ runtime ใช้งานได้อยู่ใน **BASE-01**: ยืนยัน stack ตามแผน Django/PostgreSQL, สร้าง app, dependencies/lock, `.env.example`, Docker/build configuration, คำสั่ง migrate/run/test และทดสอบเครื่องเพื่อน เมื่อ PR นี้ผ่าน review/merge ทุก task branch ต้อง merge main เพื่อรับ environment ชุดเดียวกัน

ค่าบัญชีมหาวิทยาลัยและ secrets ตั้งในเครื่องหรือช่องทางที่ทีมกำหนด ห้ามแนบใน commit ไฟล์เอกสารส่วนตัวที่อยู่นอก task ให้เลือก stage แยกอย่างระมัดระวัง
