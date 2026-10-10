# Development Environment — UniSport Buddy

ทีมใช้ **Python 3.12 + Django 5.2 + PostgreSQL 17** ผ่าน Docker Compose ชุดเดียวกัน Backend เสิร์ฟ Django Templates จาก `frontend/templates/` และ static assets จาก `frontend/static/` ที่พอร์ต 8000 ไม่มี Node server แยกใน Sprint นี้

Django 5.2 รองรับ Python 3.12 ตาม [release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/) ส่วน Compose รอ database health check ก่อนเริ่มแอปตาม [Docker startup order](https://docs.docker.com/compose/how-tos/startup-order/)

## สิ่งที่แต่ละคนต้องมี

- Git และสิทธิ์เข้าถึง repository
- Docker Desktop หรือ Docker Engine ที่กำลังทำงาน พร้อม Docker Compose v2 ที่รองรับ `up --wait`
- GNU Make สำหรับคำสั่งย่อ; ใช้คำสั่ง Docker โดยตรงด้านล่างได้หากไม่มี Make
- Windows แนะนำทำงานใน WSL2 พร้อมเปิด Docker Desktop integration ให้ distro นั้น; เก็บ repository ใน filesystem ของ WSL เพื่อให้ bind mount และ hot reload ทำงานสะดวก

ตรวจด้วย `docker version` และ `docker compose version` ไม่ต้องลง Python/PostgreSQL/Node ในเครื่องเพื่อใช้ workflow หลัก

## เริ่มต้นครั้งแรก

```bash
git clone https://github.com/GearJP2/cs261.git
cd cs261
git fetch origin
git switch --track origin/chore/base-01-project-setup
make init
```

ตัวอย่างใช้ branch BASE-01 สำหรับทดลอง PR environment ก่อน merge หลัง merge ให้เริ่มจาก main ล่าสุด แล้วเลือก task branch ของตนและ `git merge origin/main` เพื่อรับ environment นี้ หากมี local branch ชื่อนี้แล้วใช้ `git switch chore/base-01-project-setup` โดยไม่ใส่ `--track`

`make init` สร้าง `.env` จากตัวอย่างเมื่อไฟล์ยังไม่มีเท่านั้น ตรวจและเติมค่าตัวแปรใหม่หากเคยมี `.env` จาก template เดิมอยู่แล้ว; ไม่คัดลอกทับ secrets เดิม

บน Linux/WSL ตรวจ `id -u` และ `id -g` แล้วใส่ `LOCAL_UID`/`LOCAL_GID` ใน `.env` ถ้าไม่ใช่ 1000 เพื่อให้ migration/ไฟล์ที่สร้างจาก container เป็นเจ้าของเดียวกับผู้ใช้เครื่อง ให้ทำงานด้วยบัญชี non-root

```bash
make up
make verify
make smoke
```

เปิด <http://localhost:8000/> แอปจะรอ PostgreSQL พร้อม ใช้ migrations ที่ commit ไว้ แล้วเปิด development server พร้อม hot reload ไม่มีข้อมูลบัญชีมหาวิทยาลัยหรือ Party ตัวอย่างที่อ้างว่าใช้งานจริงได้ในขั้นนี้

## หากไม่มี Make

คัดลอก `.env.example` เป็น `.env` เฉพาะเมื่อยังไม่มีไฟล์ เช่น `cp .env.example .env` หรือ PowerShell `Copy-Item .env.example .env` จากนั้น:

```bash
docker compose up --build -d --wait
docker compose run --rm -T backend python backend/manage.py check
docker compose run --rm -T backend python backend/manage.py makemigrations --check --dry-run
docker compose run --rm -T --no-deps backend ruff check backend scripts
docker compose run --rm -T --no-deps backend ruff format --check backend scripts
docker compose run --rm -T backend python backend/manage.py test backend --top-level-directory backend --noinput --verbosity 2
docker compose exec -T backend python scripts/smoke.py
```

ทุกคำสั่งรันจาก root ของ repository คำสั่งทดสอบกำหนด `backend` เป็นจุดค้นหา tests เพื่อไม่พลาด tests เมื่อรันจาก root

## คำสั่งใช้ร่วมกัน

| คำสั่ง | ผลลัพธ์ |
| --- | --- |
| `make init` | สร้าง `.env` เมื่อยังไม่มี |
| `make build` | Build image ใหม่หลังแก้ dependencies หรือ Dockerfile |
| `make up` | Build และเปิดบริการแบบ background รอ health check |
| `make ps` | ดูสถานะบริการและพอร์ต |
| `make logs` | ดู log ต่อเนื่อง; Ctrl+C หยุดดู log |
| `make check` | Django system checks และตรวจว่า models ตรงกับ migration |
| `make test` | รัน Django tests กับฐาน PostgreSQL ทดสอบแยก |
| `make lint` | Ruff lint และตรวจ formatting |
| `make format` | จัดรูปแบบ Python; ไม่แก้ generated migrations |
| `make verify` | check → lint → test ตามลำดับเดียวกับ CI |
| `make smoke` | ตรวจหน้าเว็บ, CSS, liveness และ PostgreSQL readiness ของแอปที่เปิดอยู่ |
| `make migrations` | สร้าง migration หลังแก้ model; ประสานโกลก่อน |
| `make migrate` | ใช้ migration ที่ commit ไว้ |
| `make superuser` | สร้าง local admin เพื่อเข้าหน้า `/admin/` |
| `make shell` | Django shell ภายใน environment เดียวกับแอป |
| `make down` | หยุดบริการและลบ container โดยเก็บข้อมูล PostgreSQL ไว้ |

บัญชี local admin ใช้ดูแลฐานข้อมูลระหว่างพัฒนา ไม่ใช่หลักฐานยืนยันนักศึกษา Login มหาวิทยาลัยและ authorization ของ US1 ยังเป็นงานแยก

## โครงสร้างและงานของแต่ละส่วน

```text
backend/
  config/             settings, URL หลัก, ASGI และ WSGI
  accounts/           custom User และ migrations ของบัญชีแอป
  core/               หน้าเริ่มต้นและ health checks
  manage.py
  requirements.in     dependencies ที่ตั้งใจใช้
  requirements.txt    versions/hashes ที่ทีมติดตั้งร่วมกัน
frontend/
  templates/          HTML ของ Django; ใช้ base.html ร่วมกัน
  static/             CSS และ JavaScript เมื่อมีการใช้
scripts/              คำสั่งเริ่มแอปและ smoke check
database/             เอกสารฐานข้อมูล; migrations จริงอยู่ใน Django apps
```

- กอล์ฟ/พี: เพิ่ม Django app ตาม domain และเรียก business logic จาก views; อย่าสร้าง authentication หรือ DB connection คนละชุด
- วี/เนท/ออสติน: ทำหน้าใน templates และไฟล์ใน static; แก้ไฟล์ได้จากเครื่องและดูผลผ่านพอร์ตเดียวกับ Backend
- โกล: ใช้ ORM migrations และตรวจลำดับ FK; `accounts.User` เป็น user model ที่ตั้งไว้ตั้งแต่แรก ใช้ `settings.AUTH_USER_MODEL` ใน FK และ `get_user_model()` ใน Python
- เกียร์: ประสาน environment/CI และ dependency ที่หลาย task ใช้ร่วมกัน

โฟลเดอร์ placeholder เดิม เช่น controllers/routes/pages ยังอยู่เพื่ออ้างอิงโครงเดิม แต่ Django โหลดโค้ดจาก apps และ templates/static ตาม settings เท่านั้น

การมี `accounts.User` ยังไม่รวม UniversityIdentity, student verification, Party หรือ Venue; ให้ทำ schema เหล่านั้นตาม BASE-02/US1/US9 ร่วมกับโกล อย่าเพิ่ม SQL อีกชุดที่แข่งขันกับ migrations

## Environment และพอร์ต

ค่าตัวอย่างใน `.env.example` ใช้พัฒนาในเครื่องเท่านั้น `.env` ถูก ignore และไม่ถูกส่งเข้า Docker build context

| ตัวแปร | การใช้งาน |
| --- | --- |
| `APP_PORT` | พอร์ตบน host; ค่าเริ่มต้น 8000 |
| `POSTGRES_HOST_PORT` | พอร์ต DB บน host; ค่าเริ่มต้น 5433 |
| `POSTGRES_DB/USER/PASSWORD` | ค่าตั้งต้นของ DB และค่าที่แอปเชื่อมต่อ |
| `POSTGRES_HOST/PORT` | Compose กำหนดภายในเป็น database:5432 เสมอ |
| `SECRET_KEY` | ใช้กับ session/การลงลายเซ็น; example key จำกัดเฉพาะ DEBUG=true |
| `DJANGO_ALLOWED_HOSTS` | Host ที่แอปรับ ค่าเริ่มต้น localhost และ loopback |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | ใส่ origin พร้อม scheme/port หากจำเป็นตาม flow ที่ทีมตกลง |
| `LOCAL_UID/LOCAL_GID` | เจ้าของ process/ไฟล์ใน container; แก้แล้วต้อง build ใหม่ |
| `COMPOSE_PROJECT_NAME` | แยก container/network/volume เมื่อทำหลาย checkout |

แอปและ DB bind ที่ `127.0.0.1` เพื่อใช้บนเครื่องพัฒนา เครื่องมือ DB เช่น DBeaver เชื่อม `localhost:5433` พร้อมค่าจาก `.env`; ภายใน container ใช้ `database:5432` ไม่ใช่ localhost

ถ้าทำหลาย checkout ให้เปลี่ยน COMPOSE_PROJECT_NAME, APP_PORT และ POSTGRES_HOST_PORT ของแต่ละชุดเพื่อแยกทั้งข้อมูลและพอร์ต

## ข้อมูลและ migrations

PostgreSQL เก็บใน named volume ของ Compose ดังนั้น `make down`/`make up` ไม่ลบข้อมูล การเปลี่ยน POSTGRES_USER/PASSWORD ใน `.env` ไม่เปลี่ยน credentials ของ database ที่ initialize แล้ว ต้องวางแผนแก้ role หรือใช้ project name ใหม่เมื่อทดลองฐานว่าง

อย่าใช้ `docker compose down --volumes` กับข้อมูลที่ต้องเก็บ คำสั่งนี้ใช้ใน CI ซึ่งสร้างฐานใหม่สำหรับแต่ละ run เท่านั้น

Django test runner สร้างฐาน `test_<POSTGRES_DB>` แล้วลบเมื่อจบ ไม่ใช้ข้อมูลในฐานพัฒนาทำ tests บัญชี PostgreSQL ที่มากับ image ชุดนี้มีสิทธิ์สร้าง test database สำหรับ development; production ต้องออกแบบสิทธิ์แยก

แก้ model → ประสานโกล → `make migrations` → ตรวจไฟล์ migration → `make migrate` → `make verify` แล้ว commit model และ migration เป็น commit ย่อยที่ตรวจสอบได้ เมื่อดึงงานเพื่อนให้ใช้ `make migrate` โดยไม่สร้าง migration ซ้ำถ้าไม่ได้เปลี่ยน model

## เปลี่ยน dependency

เวอร์ชัน Python libraries รวม transitive dependencies ถูกล็อกพร้อม hashes ใน `backend/requirements.txt` Docker ใช้ `pip --require-hashes` ติดตั้ง และ CI ใช้ image/config/คำสั่งตรวจชุดเดียวกับทีม

Python base image และ PostgreSQL image ตรึงด้วย digest ของ image ที่ทดสอบแล้วด้วย เมื่อต้องอัปเดต OS/database image ให้แก้ tag/digest ใน Dockerfile หรือ Compose อย่างตั้งใจ แล้ว build/test/smoke ใหม่ก่อนส่ง PR

ผู้ดูแล dependency ใช้ uv รุ่น 0.11.23 สร้าง lock ครั้งนี้ เมื่อต้องอัปเดตให้แก้ `backend/requirements.in` และสร้าง lock สำหรับ Python 3.12:

```bash
uv pip compile backend/requirements.in --python-version 3.12 --generate-hashes --output-file backend/requirements.txt
make build
make verify
make up
make smoke
```

หากต้องการอัปเกรด dependency ที่ล็อกไว้อย่างตั้งใจ ให้เพิ่ม `--upgrade` แล้วตรวจ diff เวอร์ชัน/hashes ก่อนส่ง PR ทั้ง input และ lock ห้าม `pip install` เพิ่มเฉพาะใน container แล้วถือว่าทีมจะได้รับ dependency นั้นด้วย

## CI และส่งงาน

GitHub Actions รันเมื่อเปิด/อัปเดต PR และเมื่อ push main: build → Django checks/migration drift → Ruff → PostgreSQL tests → เริ่ม app/smoke test ทุก task branch ใช้กติกาเดียวกัน CI เป็นเครื่องมือยืนยันผล; branch protection/reviewer ยังต้องเป็นไปตามกติกาใน README

ก่อนส่ง PR ให้รัน `make verify` และ `make smoke` เมื่อแอปกำลังทำงาน ระบุคำสั่งและผลจริง พร้อม dependency ที่รอ merge ทีมใช้ Conventional Commits และ review อย่างน้อยหนึ่งคนก่อน Squash and merge

## ขอบเขตของ BASE-01

รอบนี้เตรียม environment, template/static pipeline, custom user เริ่มต้น, health checks และ CI ยังไม่มี Login มหาวิทยาลัย/ข้อมูล Party/seed ของ Story และยังไม่มีแชท จึงยังไม่เปิด Redis/Channels จนเริ่มงานแชทตามแผน

ใช้ Django development server สำหรับ local/CI เท่านั้น ก่อน deployment ต้องเตรียม ASGI server, static serving, HTTPS, secrets และ settings สำหรับ production ในงาน deployment แยก

## ผลตรวจ environment วันที่ 10 ตุลาคม 2026

- Build image และใช้ migration จาก PostgreSQL ว่างสำเร็จ
- `make verify` ผ่าน: Django checks, ไม่มี migration ค้าง, Ruff และ tests 7 กรณีบน PostgreSQL
- `make up` และ `make smoke` ผ่าน; หน้าเว็บและ CSS ตอบกลับจริง
- หยุด database แล้ว readiness เป็น 503 โดยไม่เปิดเผยรายละเอียด connection; liveness ยังเป็น 200 และ readiness กลับมาผ่านเมื่อเปิด DB
- หยุดด้วย Compose down แล้วเปิดใหม่ ข้อมูล probe ยังอยู่ใน named volume; ลบเฉพาะ probe หลังตรวจแล้ว
- แก้ CSS ผ่าน bind mount เห็นผลทันที และ process แอปเป็น non-root

ผลนี้เป็นการทดสอบ local Docker ของผู้เตรียม environment; ให้เพื่อนร่วมทีมทดลองตามคู่มือเพื่อยืนยันการเริ่มงานบนเครื่องของตน ส่วน GitHub Actions จะแสดงผลแยกใน PR ไม่ใช่ผลที่อนุมานจากการรัน local
