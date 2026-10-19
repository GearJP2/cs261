# US1 Backend Report — Login API และ Django session

เอกสาร implementation ณ 18 ตุลาคม 2026 สำหรับ Backend US1-B และ Frontend ที่เชื่อมบัญชีผู้ใช้
โค้ดและ tests อยู่ใน `backend/accounts/` ใช้ PostgreSQL และ Django session ชุดเดียวกับระบบ
เอกสารนี้รายงานสิ่งที่ implement และทดสอบแล้ว แยกจาก Technical Plan และไม่เปลี่ยนสถานะการรับรองแผนของทีม

## สถานะและขอบเขต

ทำแล้ว: ตัวเรียก TU API, ตรวจ response/type, ผูก User กับ UniversityIdentity,
Login/session, CSRF, `/me`, Logout และ guard กลาง

ทดสอบด้วย mock โดยไม่เรียก TU API จริง ไม่มี endpoint mock Login สำหรับใช้งานจริง
ยังไม่ยืนยัน Application-Key, สิทธิ์รับ/ส่ง credentials ผ่าน verify API หรือ contract ของ TU
จึงยังไม่ถือว่าการเชื่อมมหาวิทยาลัยหรือ US1 ทั้งฟีเจอร์เสร็จ

Technical Plan เดิมร่าง AUTH-02/03 แบบ redirect SSO ไว้ แต่โค้ดนี้ใช้ Backend ส่ง POST
ไป verify API จึงไม่มี `/auth/university/start` หรือ callback ต้องยืนยันวิธีที่ TU อนุญาต
ก่อนนำไปใช้จริง หากต้องใช้ SSO ให้ปรับ implementation และ contract ร่วมกัน

## Flow และการจัดไฟล์

```text
Browser รับ CSRF token
  → POST Login พร้อม cookie, token และ username/password
  → Backend เรียก TU verify API
  → ตรวจ response และ type
  → หา/สร้าง User + UniversityIdentity + UserProfile
  → ตรวจบัญชี active และสร้าง Django session
  → Browser ใช้ cookie เรียก /me และ API ที่มี guard
  → POST Logout หรือ session หมดอายุ
```

| ไฟล์ | หน้าที่ |
| --- | --- |
| `backend/accounts/services.py` | เรียก TU API, ตรวจ response/สิทธิ์, หา/สร้าง User |
| `backend/accounts/views.py` | รับ HTTP, จัดการ error, Login/Logout/session และ `/me` |
| `backend/accounts/decorators.py` | `require_university_user` สำหรับป้องกัน JSON API |
| `backend/accounts/urls.py` | ประกาศ path ภายใต้ `/api/v1/` |
| `backend/config/urls.py` | รวม accounts URLs เข้ากับระบบ |
| `backend/accounts/tests.py` | tests แบบ mock และ PostgreSQL concurrency |

## API contract

ทุก path ด้านล่างไม่มี slash ท้าย URL ใช้ origin เดียวกับหน้าเว็บ เช่น `http://localhost:8000`
Browser ต้องส่ง cookie ของ origin นี้มาด้วย ไม่ส่ง user ID เพื่อเลือกผู้กระทำ

| Method | Path | สำเร็จ | สิทธิ์ |
| --- | --- | --- | --- |
| GET | `/api/v1/auth/csrf` | 200 พร้อม CSRF token | สาธารณะ |
| POST | `/api/v1/auth/login` | 200 พร้อมผล Login | สาธารณะ แต่ต้องผ่าน CSRF |
| GET | `/api/v1/me` | 200 พร้อมผู้ใช้ปัจจุบัน | session มหาวิทยาลัยที่ผ่าน guard |
| POST | `/api/v1/auth/logout` | 200 พร้อมผล Logout | ต้องผ่าน CSRF; ไม่มี session ก็เรียกซ้ำได้ |

### รับ CSRF token

`GET /api/v1/auth/csrf` คืน:

```json
{"data": {"csrf_token": "token ที่ Django สร้าง"}}
```

Django ตั้ง cookie `csrftoken` และปิด caching ของ response หน้าเว็บต้องแนบ token
จาก JSON ใน header `X-CSRFToken` เมื่อส่ง POST พร้อม cookie ของ Browser เดียวกัน
GET นี้ไม่สร้าง authenticated session

### Login

`POST /api/v1/auth/login` รับ `Content-Type: application/json`:

```json
{"username": "บัญชีมหาวิทยาลัย", "password": "รหัสผ่าน"}
```

ทั้งสองค่าต้องเป็น string; username ห้ามว่าง/ช่องว่างล้วน และ password ห้ามเป็น string ว่าง
Backend ไม่ตัดช่องว่างของ password

เมื่อสำเร็จคืน `200` และ cookie `sessionid`:

```json
{"data": {"logged_in": true, "id": 7}}
```

User ภายในใช้ username แบบ `tu_<UUID>` และตั้ง unusable password; ไม่ใช้รหัสผ่าน
มหาวิทยาลัยเป็นรหัสผ่าน local ไม่เก็บหรือ log รหัสผ่านมหาวิทยาลัย
Login ซ้ำค้นหา identity ด้วย `(provider_key="tu", subject)` และใช้ User เดิม
ไม่จับคู่บัญชีด้วย email หรือชื่อ และอัปเดตชื่อแสดงกับเวลาตรวจสิทธิ์เมื่อ Login ผ่าน
การสร้าง User/identity อยู่ใน transaction และรองรับ unique identity ชนกันพร้อมกัน

**กฎสิทธิ์ปัจจุบันตามข้อตกลงในงานนี้:** ตรวจ `status` เป็น boolean `true` และ `type="student"`
ไม่ตรวจ `statusid` หรือ `tu_status` จึงไม่ได้แยกนักศึกษาปัจจุบันจากศิษย์เก่าด้วยสถานะเหล่านั้น
`student_verified=true` ใน `/me` หมายถึงผ่านนโยบายนี้ ไม่ใช่คำยืนยันสถานะนักศึกษาปัจจุบันเพิ่มเติม
ต้องให้ทีมรับรองนโยบายและเทียบความหมายฟิลด์กับ TU ก่อนใช้จริง

### ผู้ใช้ปัจจุบัน

`GET /api/v1/me` อ่าน session ไม่เรียก TU API ซ้ำและไม่รับ user ID เพื่อเลือกบัญชี:

```json
{"data": {"id": 7, "display_name": "นักศึกษาทดสอบ", "student_verified": true}}
```

ส่งเฉพาะฟิลด์ข้างต้น ไม่ส่ง password hash, subject, email, API key หรือ session key
response ปิด caching หาก profile ไม่มีจะคืน `403 FORBIDDEN` ให้ Login ใหม่

### Logout

`POST /api/v1/auth/logout` แนบ CSRF token และใช้ body `{}` ได้ คืน:

```json
{"data": {"logged_out": true}}
```

Django flush session ปัจจุบันและล้าง session cookie แต่ไม่ลบ User/identity/profile
cookie ของ session เดิมใช้ `/me` ต่อไม่ได้ รวมถึงแท็บอื่นที่ใช้ session เดียวกัน
ไม่ได้ยกเลิกทุก session ของผู้ใช้บนอุปกรณ์อื่น การ Logout ซ้ำได้ `200` แต่ยังต้องตรวจ CSRF

### Errors

Error ที่ view/guard จัดการใช้รูปแบบ:

```json
{"error": {"code": "AUTH_REQUIRED", "message": "กรุณาเข้าสู่ระบบ"}}
```

| HTTP | Code | กรณี |
| --- | --- | --- |
| 400 | `INVALID_INPUT` | Content-Type, JSON หรือ username/password ไม่ถูกต้อง |
| 401 | `LOGIN_FAILED` | TU ส่ง JSON ที่ `status` ไม่ใช่ boolean true |
| 401 | `AUTH_REQUIRED` | ไม่มี session ที่ใช้ได้/หมดอายุ |
| 403 | `FORBIDDEN` | ไม่ใช่ student, Login ด้วยบัญชี inactive, identity ไม่ผ่าน หรือ `/me` ไม่มี profile |
| 403 | `ACCOUNT_INACTIVE` | guard ได้รับ authenticated user ที่ inactive |
| 403 | response ของ Django | CSRF ไม่ผ่าน; ปัจจุบันอาจเป็น HTML ไม่ใช่ JSON envelope |
| 405 | response ของ Django | Method ไม่ตรง endpoint; อย่าสมมติว่าเป็น JSON |
| 502 | `UNIVERSITY_API_UNAVAILABLE` | ไม่มี key, HTTP error, connection/timeout หรือ response TU ผิดรูปแบบ |

ModelBackend ปกติจะไม่โหลด User ที่ inactive เป็น authenticated user แล้ว ดังนั้น
บัญชีที่ถูกระงับหลัง Login จะได้ `401 AUTH_REQUIRED` เมื่อเรียก `/me` ใน flow ปัจจุบัน
Frontend ต้องรองรับทั้ง 401 และ 403

HTTP 401/403 จาก TU เองยังถูกจัดเป็น `502` ในตัว client ไม่ได้แปลงเป็นรหัสผ่านผิด
จนกว่าจะยืนยัน contract ของ provider; รายละเอียด error ภายในไม่ถูกส่งกลับหน้าเว็บ

## ตัวอย่าง Frontend แบบ origin เดียวกัน

ตัวอย่างนี้ใช้ credentials ที่ได้รับจากฟอร์ม ไม่ hardcode รหัสผ่านหรือ key
โค้ด Login นี้เรียก TU จริงเมื่อ Backend ตั้ง key แล้ว; ไม่ใช่ช่องทาง mock

```javascript
async function getCsrfToken() {
  const response = await fetch('/api/v1/auth/csrf', {
    credentials: 'same-origin',
    cache: 'no-store',
  });
  if (!response.ok) throw new Error('รับ CSRF token ไม่สำเร็จ');
  return (await response.json()).data.csrf_token;
}

async function login(username, password) {
  const token = await getCsrfToken();
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': token,
    },
    body: JSON.stringify({ username, password }),
  });
  // CSRF/method errors อาจเป็น HTML ต้องตรวจ Content-Type ก่อนอ่าน JSON
  const type = response.headers.get('Content-Type') || '';
  const body = type.includes('application/json') ? await response.json() : null;
  if (!response.ok) throw new Error(body?.error?.message || 'เข้าสู่ระบบไม่สำเร็จ');
  return body.data;
}

async function logout() {
  // Login หมุน CSRF token จึงขอ token ล่าสุดก่อน POST
  const token = await getCsrfToken();
  const response = await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRFToken': token },
  });
  if (!response.ok) throw new Error('ออกจากระบบไม่สำเร็จ');
  return (await response.json()).data;
}
```

หลัง Login หรือรีเฟรชหน้าใช้ `GET /api/v1/me` อ่านชื่อจาก session เมื่อได้ 401/403
หยุดแสดงสถานะว่า Login ใช้งานได้ ไม่เก็บ password ใน localStorage หรือ log
อย่าเปิด CORS ให้เว็บไซต์อื่นอ่าน token โดยไม่มีข้อตกลงของทีม

## Session และ guard กลาง

`UNIVERSITY_SESSION_AGE = 24 * 60 * 60` ใน settings ใช้ตั้งวันหมดอายุแบบแน่นอน
ตอน Login สำเร็จ: 24 ชั่วโมงนับจากครั้งนั้น การเรียก `/me` ไม่ต่อเวลา Login ใหม่ที่สำเร็จตั้งเวลาใหม่
ใช้ `django_session` และเก็บ `university_identity_id` ใน session ฝั่งเซิร์ฟเวอร์
cookie เป็น HttpOnly, SameSite=Lax; session/CSRF cookies ใช้ Secure เมื่อ `DEBUG=False`

หลักฐานตรวจสิทธิ์มาจาก Login ล่าสุด ไม่เรียก TU เพื่อตรวจสิทธิ์ใหม่ระหว่าง session
`student_verified_at`/`eligibility_checked_at` เพียงอย่างเดียวไม่ใช่ผลตรวจ TU ครั้งใหม่
นโยบาย recheck แยกต่างหากยังรอทีม; ห้ามอ้างว่าตรวจสถานะปัจจุบันทุก request

API ธุรกิจใช้ guard เดียวกัน:

```python
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.decorators import require_university_user


@require_POST
@require_university_user
def example_party_action(request, party_id):
    # ต้องตรวจสิทธิ์ Host/Member และกฎของ Party เพิ่มที่นี่หรือใน service
    return JsonResponse({'data': {'id': request.user.pk}})
```

ตัวอย่างนี้เป็นโครง ไม่เพิ่ม route จริง และยังต้องใช้ CSRF middleware ของโปรเจกต์สำหรับ POST
Guard ตรวจ authenticated user, `is_active` และ marker identity ใน session ว่าตรงกับ user,
provider `tu` และมีเวลาตรวจทั้งสองค่า เมื่อผ่านเพิ่ม `request.university_identity` ให้ view
บัญชี local/Admin อย่างเดียวไม่ผ่าน guard; guard ไม่ตรวจ Host, capacity หรือ profile
การตรวจ profile เป็นหน้าที่ `/me` และ decorator ปัจจุบันใช้กับ synchronous views

## Configuration และ TU client

ใน `.env` ของเครื่องเมื่อได้รับสิทธิ์แล้ว:

```dotenv
TU_APPLICATION_KEY=ใส่ค่าจริงเฉพาะในเครื่อง
```

settings อ่านผ่าน environment; Docker โหลด `.env` ให้ Backend หลังเปลี่ยนค่าให้รัน `make up`
อย่า commit `.env` หรือ key; `UNIVERSITY_SESSION_AGE` เป็นค่าใน settings ไม่ได้อ่านจาก `.env`

Client ปัจจุบันส่ง POST ไป `https://restapi.tu.ac.th/api/v1/auth/Ad/verify`
ด้วย headers `Content-Type: application/json`, `Application-Key` และ JSON `UserName`/`PassWord`
แล้วอ่าน JSON object ตรวจฟิลด์ `username`, `displayname_th`, `type` ว่าเป็น string ไม่ว่าง
ใช้ `urlopen(..., timeout=10)` เป็น timeout ของการทำงาน connection ไม่ใช่เพดานเวลารวมแน่นอน
ข้อมูลทั้งหมดนี้อธิบายโค้ด ไม่ใช่การรับรอง contract จาก TU

ยังต้องยืนยันกับผู้ดูแลบริการ: วิธีที่อนุญาตรับ credentials, การลงทะเบียนแอป,
Application-Key, identifier ที่คงที่ และความหมายของ response/error หากเป็น redirect SSO จริง
ต้องใช้ client/redirect URI และ callback ตาม protocol แทนการเดา flow

## การรันและผลทดสอบ

รันจาก root `cs261/`:

```bash
make up
make verify
make smoke
```

ผลตรวจล่าสุดของ implementation ในเครื่องนี้: `make verify` ผ่าน 81 tests และ `make smoke` ผ่าน
จำนวน 81 รวม schema/core tests ของทั้งโปรเจกต์ ไม่ใช่ Login tests ทั้งหมด
ใช้ผลนี้เป็นหลักฐานของ commit ที่ตรวจเท่านั้น; GitHub Actions และเครื่องอื่นต้องตรวจแยก

Tests ครอบคลุม client request/errors, response/type validation, User/identity,
CSRF, Login, `/me`, Logout, session expiry/rotation และ guard
Concurrency test ใช้ TransactionTestCase, Barrier และ PostgreSQL สอง connection จริง
ตรวจว่าทั้งคู่ได้ User เดียวกันและไม่มีข้อมูลส่วนเกิน ไม่เรียก TU API จริง

ตรวจด้วย Browser โดยไม่ Login ได้:

- `/` หน้าแรก
- `/health/ready/` database พร้อม
- `/api/v1/auth/csrf` ได้ token
- `/api/v1/me` ได้ 401 `AUTH_REQUIRED` ตามปกติ

Browser Login สำเร็จและ integration กับมหาวิทยาลัยยังไม่ได้ตรวจรับ; ไม่มีการเปิด mock
ให้ Login จริง ขั้นตอนที่เหลือคือเชื่อม UI, ยืนยัน provider/policy และทดสอบ TU เมื่อได้รับสิทธิ์

### ฐานพัฒนาที่เคยใช้ accounts migration ชื่อเก่า

หลังแยก migration รวมเดิมเป็น accounts `0002/0003` ฐานที่เคยใช้ไฟล์เก่าอาจพบ
`relation accounts_universityidentity already exists` ตอน `make up`
นี่คือประวัติ migration ไม่ตรงไฟล์ ไม่ใช่เหตุให้ลบ volume
ให้สำรองฐานและตรวจตาราง/constraints เทียบกับ migrations ก่อนปรับประวัติ
อย่าใช้ `--fake` หรือเปลี่ยน constraint โดยไม่ตรวจ schema จริง; ฐานใหม่สร้างตาม migrations ได้ตามปกติ
