# US3-T-01 / US3-T-02 — Backend test report

ตรวจวันที่ 19 ตุลาคม 2026 บน branch `test/us-3-t-join-requests` จาก `main` commit `5070794` ผู้ดำเนินการรอบนี้: พี

อ้างอิง [Technical Plan](sprint-1-technical-plan.md#6-us3--ส่งคำขอเข้าร่วม) และ [US3-B API](us3-b-api.md) งาน US3-T อยู่ใน Issue #15 ตาม [branch mapping](sprint-1-branches.md)

สถานะ: เทสต์ Backend ตามรายการด้านล่างผ่านและพร้อม review ยังไม่ติ๊กตรวจรับหรือปิด US3-T ทั้ง parent แทนทีม เพราะยังต้องตรวจ integration กับ US3-F และ guard ของ US1

## สิ่งที่เปลี่ยน

- ใช้เทสต์เดิมใน `backend/parties/test_join_requests.py` เป็นหลัก เพิ่ม 4 กรณี: Host ที่มี active membership, ปลอม user_id ของบัญชีที่มีอยู่จริงใน body, session หมดอายุ และเรียก logout endpoint แล้วนำ cookie เก่ากลับมาใช้
- เพิ่มการเทียบ membership ทุกฟิลด์ก่อน/หลัง รวม capacity และค่าจำนวนสมาชิก/ที่ว่างจาก API รายละเอียด Party ในกรณีส่งพร้อมกันและการปฏิเสธตาม state/สมาชิก
- ใน concurrency tests ตรวจ Party/User เจ้าของคำขอ, ID ที่ API คืนตรงกับฐานข้อมูล, decision fields ยังว่าง และแต่ละคนอ่านคำขอของตัวเองได้
- แก้ `reverse()` 3 จุดใน `backend/accounts/test_profile_acceptance.py` ให้ใช้ `accounts:user-public-profile` ตาม namespace ที่มีอยู่หลัง merge US1-B การรันรวมครั้งแรกพบ US8 acceptance tests ล้ม 8 กรณีด้วย `NoReverseMatch`; หลังแก้ผ่านครบ
- ไม่มีการแก้ production views/services/guard, schema, migration, env หรือ dependency

## US3-T-01 — คำขอพร้อมกันและกฎ Pending

ชื่อเทสต์อยู่ใน `JoinRequestConcurrencyTests` ของ `parties.test_join_requests`:

| เงื่อนไข | เทสต์ | ผลที่ตรวจและผลรัน |
| --- | --- | --- |
| คนเดียวส่งพร้อมกันสองคำขอ | `test_same_user_concurrent_posts_create_exactly_one_pending` | ผ่าน: 201 หนึ่งครั้งและ 409 REQUEST_EXISTS หนึ่งครั้ง มี Pending หนึ่งแถวของผู้ใช้/Party ที่ถูกต้อง |
| คนละคนขอเมื่อเหลือหนึ่งที่ | `test_different_users_can_both_request_the_last_slot` | ผ่าน: 201 ทั้งคู่ มี Pending คนละแถว และ GET ของแต่ละ session คืน request ของตัวเอง |
| Pending ไม่เพิ่มสมาชิกหรือจองที่ | สองเทสต์ข้างต้น และ `JoinRequestApiTests.test_create_pending_and_read_own_request_without_consuming_capacity` | ผ่าน: membership ไม่เปลี่ยน, capacity=2, member_count=1 และ remaining_slots=1 |

ใช้ `TransactionTestCase`, PostgreSQL หลาย connection และ Barrier เพื่อปล่อยคำขอพร้อมกัน ตรวจผลหลัง worker ทั้งสองจบ ไม่ใช้ SQLite หรือ mock transaction ผลรันนี้ไม่มี concurrency test ถูก skip

## US3-T-02 — การปฏิเสธและเจ้าของคำขอ

ชื่อเทสต์อยู่ใน `JoinRequestApiTests` ของ `parties.test_join_requests`:

| เงื่อนไข | เทสต์ | ผลที่ตรวจและผลรัน |
| --- | --- | --- |
| สมาชิกเดิม | `test_active_member_is_rejected` | ผ่าน: 409 ALREADY_MEMBER ขณะยังมีที่ว่าง ไม่สร้างคำขอหรือเปลี่ยน membership |
| Host | `test_host_with_active_membership_is_rejected_without_writing`, `test_host_is_rejected_even_when_host_membership_is_missing` | ผ่าน: 409 ALREADY_MEMBER ทั้งข้อมูลปกติและกรณี Host ไม่มี membership |
| ไม่ login / บัญชี inactive | `test_anonymous_and_revoked_sessions_cannot_read_or_create` | ผ่าน: POST และ GET ได้ 401 AUTH_REQUIRED ไม่สร้างคำขอหรือเปลี่ยน membership |
| Party เต็ม / เริ่ม / จบ / ยกเลิก | `test_closed_party_states_reject_new_requests` | ผ่าน: 409 PARTY_FULL / PARTY_STARTED / PARTY_CANCELLED ไม่สร้างคำขอ และสมาชิก/ที่ว่างไม่เปลี่ยนจาก state ที่ตั้งไว้ |
| ตรงเวลาเริ่มพอดี | `test_exact_start_boundary_rejects_request` | ผ่าน: 409 PARTY_STARTED |
| Party ID ที่ไม่มีอยู่ | `test_unknown_party_returns_json_404_for_both_endpoints` | ผ่าน: POST และ GET ได้ 404 NOT_FOUND |
| ส่ง user_id ของคนอื่นใน JSON | `test_body_cannot_create_request_for_an_existing_other_user`, `test_invalid_body_and_client_selected_fields_are_rejected` | ผ่าน: 400 INVALID_INPUT ไม่สร้างคำขอให้ผู้ใด |
| ปลอมเจ้าของผ่าน query | `test_query_cannot_change_actor_and_empty_body_is_supported`, `test_get_returns_null_and_cannot_read_another_users_request` | ผ่าน: POST ใช้เจ้าของจาก session; GET ไม่อ่านคำขอของผู้อื่นตาม query |
| Logout แล้วใช้ cookie เก่า | `test_logout_endpoint_revokes_copied_session_for_both_endpoints` | ผ่าน: logout endpoint ของ US1 ลบ server session; browser เดิมและ client ที่ถือ cookie เก่า GET/POST ไม่ได้ (401) โดย POST ส่ง CSRF ถูกต้อง |
| Session หมดอายุ | `test_expired_session_cannot_read_or_create` | ผ่าน: GET/POST ได้ 401 และไม่มีข้อมูลคำขอ/สมาชิกเปลี่ยน |

Inactive session ได้ 401 เพราะ Django ModelBackend ไม่คืน authenticated user ที่ถูกปิดใช้งาน ส่วน guard ที่ได้รับ authenticated inactive user โดยตรงมีสาขา 403 ACCOUNT_INACTIVE ตามพฤติกรรมที่ระบุใน US3-B API จึงไม่อ้างว่าชุดนี้ยืนยันนโยบาย 403 ของระบบมหาวิทยาลัยครบแล้ว

## วิธีรันและผลจริง

รันจาก root repository โดย Docker ต้องพร้อมและมี `.env` ตามคู่มือ development:

```bash
docker compose run --rm -T backend python backend/manage.py test parties.test_join_requests --noinput --verbosity 2
make verify
```

- ชุด US3: ผ่าน 29 tests (23 API/session tests และ 6 concurrency tests) เพิ่มจากเดิม 25 tests
- `make verify` รอบสุดท้าย: ผ่าน Django system checks, migration drift check, Ruff lint/format และ 152 tests ทั้ง repository ไม่มี skipped tests
- `make smoke`: ไม่ได้รัน เพราะรอบนี้เปลี่ยนเฉพาะเทสต์และเอกสาร ไม่มี runtime/หน้าเว็บเปลี่ยน
- ใช้ฐานข้อมูลทดสอบแยกและลบทิ้งเมื่อจบ fixtures สร้างเอง ไม่ขึ้นกับ BASE-03 seed หรือบัญชีมหาวิทยาลัยจริง
- ผลข้างต้นเป็น local validation ไม่ใช่ผล CI หรือ browser acceptance

## งานส่งต่อก่อนปิด parent

1. Review เทสต์และผลรันนี้ แล้วอัปเดตผู้รับผิดชอบ/สถานะใน Issue หรือ Trello ตามที่ทีมตกลง
2. BASE-04 integration: API คำขอยังใช้ `require_authenticated_api` และ session fixtures ผ่าน `force_login` การมี US1-B ใน main ยังไม่ได้ทำให้ API เหล่านี้บังคับ identity มหาวิทยาลัย ผลชุดนี้จึงไม่ยืนยันการปฏิเสธ local account ที่ไม่ได้ยืนยันมหาวิทยาลัย ต้องทดสอบเพิ่มหลังเชื่อม guard
3. US3-F: ตรวจผ่านหน้าเว็บจริงว่ากดส่งแล้วแสดง Pending, ปิดปุ่มระหว่างส่ง, โหลด state ใหม่หลัง 409/network error และไม่แสดงปุ่มขอเมื่อ Party ปิดรับ
4. เมื่อ US7 พร้อม ตรวจ race กับ cancellation endpoint จริงอีกครั้ง เทสต์ cancellation เดิมจำลอง transaction ตามกติกา Party lock

PR รอบนี้อ้าง `Refs #15` ได้ โดยยังไม่ใช้ `Closes #15` จนกว่าทีมตรวจรับ integration ของ parent ครบ
