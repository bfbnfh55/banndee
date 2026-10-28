# เตรียมขึ้น GitHub

ชื่อ repository ที่แนะนำ: BaanDee-StockGuard

## วิธีผ่านเว็บไซต์
1. เข้าบัญชี GitHub และสร้าง repository ให้ผู้สอนเข้าถึงได้
2. เลือก Upload files แล้วลากไฟล์และโฟลเดอร์ภายในชุดนี้ขึ้นไป ไม่ใช่ ZIP หรือโฟลเดอร์ครอบ ให้ README.md และ run.py อยู่หน้าหลัก
3. รวม .gitignore, .gitattributes และ .github ด้วย แต่ไม่อัปโหลดโฟลเดอร์ .git
4. กด Commit changes แล้วตรวจหน้า README และผลในแท็บ Actions
5. ส่ง URL repository จริง และนำไปแทนช่อง GitHub ในสไลด์

## วิธี Git
โฟลเดอร์ที่เตรียมไว้บนเครื่องมี Git สาขา main แต่ยังไม่มี commit/remote ส่วน ZIP ไม่รวม .git ให้รัน git init -b main ก่อนหากแตก ZIP
ตั้งชื่อและอีเมลสำหรับ commit ของตัวเอง ไม่สร้างประวัติแทนสมาชิก:

```powershell
git config user.name "YOUR-NAME"
git config user.email "YOUR-EMAIL"
git add .
git diff --cached --stat
git commit -m "Prepare StockGuard final project"
git remote add origin https://github.com/YOUR-USERNAME/BaanDee-StockGuard.git
git push -u origin main
```
สร้าง repository เปล่าก่อน push (ไม่เพิ่ม README/license อัตโนมัติ) และแทน URL ตัวอย่างด้วย URL จริง

## ก่อนส่ง
- ยืนยันบทบาทสมาชิกและ AI_USE.md ตามการทำงานจริง
- ตรวจ Actions และทดสอบบนเครื่องนำเสนอ
- test_results เป็นผลตรวจรอบก่อนหน้า ไม่ใช่ผลรัน GitHub รอบใหม่
- ไม่มีฐานข้อมูลใช้งานจริง .env หรือ cache ในชุดส่ง
- GitHub Pages รัน Python/SQLite backend นี้ไม่ได้ ให้รันด้วย Python ตาม README
- ยังไม่ได้เพิ่ม license ครอบข้อมูลอาจารย์หรือโค้ดต้นทาง
- ชุดนี้ยังไม่ได้เผยแพร่ขึ้น GitHub และยังไม่มี URL จริง
