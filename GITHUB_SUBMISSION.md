# เตรียมส่งบน GitHub

## งานที่ทีมต้องทำก่อนส่ง

- [ ] กรอกชื่อกลุ่ม ชื่อสมาชิก 3–4 คน และรหัสใน README ตามความจริง
- [ ] รันแอปและ tests บนเครื่องที่จะนำเสนอ แล้วอ่าน expected/actual
- [ ] ทุกคนอธิบาย raw/generated/cleaned, join keys, review และ CRUD ได้
- [ ] ตรวจสมมติฐานและปรับ AI_USE.md ตามสิ่งที่ทีมทำจริง
- [ ] สร้าง GitHub repository ให้ผู้สอนเข้าถึงได้
- [ ] ใช้ commits/issues แสดงการแก้ไขและแบ่งงานจริง ไม่สร้างประวัติย้อนหลังปลอม
- [ ] ตรวจไม่มี .env, key, log, virtual environment หรือฐานข้อมูล runtime ถูกเพิ่ม
- [ ] push tag หรือสร้าง release ชื่อ v1.0-final
- [ ] ส่ง URL repository และนัดนำเสนอ 3 ตัวเลือกคนละวันตามกรอบ 19–30 ตุลาคม

## คำสั่งตัวอย่าง

เปิด terminal ในโฟลเดอร์ที่มี README และ run.py ติดตั้ง Git ก่อนถ้ายังไม่มี ตั้งค่า Git name/email เป็นข้อมูลที่เจ้าของต้องการใช้เอง ไม่ใช้ชื่อที่ระบบสร้างแทน

```bash
git init
git add .
git status
```

อ่านรายการ staged files ก่อน commit `.gitignore` ไม่ป้องกันไฟล์ที่เคย track แล้ว

```bash
git commit -m "Initial StockGuard prototype reviewed by team"
git branch -M main
```

สร้าง empty repository ในบัญชี GitHub ของทีม คัดลอก URL จริงมาแทน `YOUR-REPOSITORY-URL`:

```bash
git remote add origin YOUR-REPOSITORY-URL
git push -u origin main
```

ทำการแก้ไขและ commits ของสมาชิกตามจริง เมื่อพร้อมส่งและตรวจครบ:

```bash
python tests/test_system.py
git add README.md AI_USE.md test_results
git commit -m "Record final verification and team details"
git tag -a v1.0-final -m "Final project submission"
git push origin main
git push origin v1.0-final
```

ถ้าไม่มีไฟล์เปลี่ยน `git commit` รอบสุดท้ายไม่จำเป็น อย่าสร้าง tag ใหม่ซ้ำหากมีแล้ว; ตรวจ `git tag` ก่อน ส่ง URL จริงหลัง push สำเร็จ GitHub Pages อย่างเดียวรัน Python/SQLite backend ของชุดนี้ไม่ได้ สาธิตระบบบนเครื่อง local ตามคู่มือได้ตามโจทย์
