# เริ่มต้นใช้งาน BaanDee StockGuard

1. แตก ZIP แล้วเปิดโฟลเดอร์ BaanDee_StockGuard
2. ดับเบิลคลิก START_WINDOWS.bat (ต้องมี Python 3.10+) หรือเปิด VS Code Terminal แล้วพิมพ์ `python run.py`
3. เปิด http://127.0.0.1:8000 ใน Chrome/Edge และเปิด Terminal ทิ้งไว้

ตัวอย่าง: ค้น SKU-0001 → ดูหลักฐาน → บันทึกคำขอ 25 → เปิดแก้เป็น 28 → ปิดเปิดระบบแล้วเรียกดูอีกครั้ง

อ่าน README.md สำหรับรายละเอียดทั้งหมด และ docs/DEMO_8_MINUTES.md สำหรับลำดับนำเสนอ

ผลทดสอบ backend/API: 30/30 ผ่าน มีผล Input/Expected/Actual ใน test_results/results.csv
โหมดสาธิตย้อนหลัง: 82 รายการ = เพียงพอ 59 + ต่ำ 18 + หมด 2 + ต้องทบทวน 3
โหมดปัจจุบัน: ข้อมูลจาก 31 ก.ค. 2026 เก่าเกินเกณฑ์ ระบบจึงหยุดเพื่อทบทวน

ตรวจหน้าจอจริงผ่าน Codex in-app browser 13 กรณีแล้ว ดู test_results/ui_review.json; เป็นคนละวิธีกับสคริปต์ Playwright เดิม ยังต้องซ้อมบนเครื่องนำเสนอของทีม

ยังต้องกรอกชื่อสมาชิก/รหัส ตรวจและเข้าใจโค้ด อัปโหลด GitHub และสร้าง tag v1.0-final ตาม docs/GITHUB_SUBMISSION.md จึงจะส่งครบข้อกำหนด ไม่มีการสร้าง repository online ให้แล้วใน ZIP นี้

เริ่มอ่าน docs/WHAT_WE_ADDED.md เพื่อแยกของอาจารย์/โครงงานเดิม/สิ่งที่เพิ่มรอบนี้
ฟีเจอร์ใหม่: คิวทบทวนพร้อมแก้นโยบายและประวัติ, What-if, แสดง quarantine, หน้าที่มาของข้อมูล
ซ้อมโดยไม่แตะฐานข้อมูลปกติ: START_DEMO_WINDOWS.bat หรือ python run.py --demo-session (ข้อมูลซ้อมถูกทิ้งเมื่อปิดเซิร์ฟเวอร์)
