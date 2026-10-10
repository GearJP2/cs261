# Seeds

BASE-03 จะเพิ่มข้อมูลทดสอบตาม Story โดยใช้ Django management command หรือ fixture ที่ทำซ้ำได้ และอ้างอิง custom User ของแอป

BASE-01 ยังไม่สร้างบัญชีนักศึกษาหรือ Party จำลองให้อัตโนมัติ หากต้องเข้าหน้า admin ให้สร้างบัญชี local ด้วย `make superuser` ข้อมูลสำหรับ UAT ต้องระบุว่าเป็นตัวอย่างและห้ามใช้ credentials มหาวิทยาลัยจริงใน repository
