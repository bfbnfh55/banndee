# แหล่งข้อมูลและส่วนที่พัฒนาเพิ่ม

## 1. ของอาจารย์ที่นำมาใช้จริง

| รายการ | จำนวน | ใช้ทำอะไร | สิ่งที่เปลี่ยน |
|---|---:|---|---|
| data/raw/products.csv | 82 แถว | รหัส ชื่อ หมวดสินค้า | raw ไม่เปลี่ยนแม้แต่ไบต์เดียว; cleaned ปรับตัวพิมพ์หมวด 5 แถว |
| data/raw/inventory_snapshot.csv | 82 แถว | สต็อกแต่ละสินค้า/คลังและเวลา | raw ไม่เปลี่ยนแม้แต่ไบต์เดียว; ไม่แก้เวลาสต็อกให้ดูใหม่ |
| บริบท BaanDee Living | — | บริษัทสมมติและข้อมูลสังเคราะห์ | เปลี่ยนโจทย์ธุรกิจเป็นการตรวจสต็อกและสร้างคำขอเติม |

หลักฐานเทียบ SHA-256: `docs/source_comparison.json` และหน้า “ที่มาและสิ่งที่เพิ่ม”

- products: `2d2a12e8c33a829a4cf909685cd8c1feedf7f8929289f01b09751fd96cd81cd5`
- inventory: `65c588f1c830dd761c74be1b6bf969b5fd593ce7988b95073608393d1139bfef`

ตัวอย่างอาจารย์เป็น Delayed Order Support Copilot ใช้ FastAPI, Gradio, pandas และ AI fixtures งาน StockGuard ใช้ Python standard library + SQLite + HTML/JavaScript เป็นแอปอีกชุด ไม่มีการใช้โค้ดตัวอย่าง Copilot เป็นแอปที่ส่งซ้ำ

ไฟล์ orders, order_lines, customers, support_tickets, delay_policy, ground_truth และ checkpoints ของอาจารย์ไม่ได้ใช้ในระบบนี้

## 2. องค์ประกอบหลักของ StockGuard

| สิ่งที่เพิ่มจากอาจารย์ | ตำแหน่ง | เหตุผล |
|---|---|---|
| ตารางนโยบายใหม่ 85 แถว | data/generated/replenishment_policy.csv | ให้ min_qty, target_qty, lead_days ที่ข้อมูลสต็อกเดิมไม่มี |
| กฎสร้างและทำความสะอาดนโยบาย | scripts/prepare_data.py | กำหนดซ้ำได้ แยกข้อมูลใช้ได้/กักกัน และ log ก่อน–หลัง |
| กฎ stock status / freshness | src/core.py | out, low, ok, review พร้อมหลักฐาน |
| REST API ใหม่ | src/server.py | Browser ส่ง HTTP JSON ไป backend |
| คำขอและประวัติใน SQLite | requests, audit | สร้าง บันทึก อ่านกลับ แก้ไข ยกเลิกแบบเก็บประวัติ |
| หน้าสต็อก/คำขอ/คุณภาพข้อมูล | web/ | ใช้งานผ่านเบราว์เซอร์ |
| ชุดทดสอบ 18 กรณีเดิม | tests/test_system.py 01–18 | CRUD, failure, raw integrity, concurrency |

ค่าขั้นต่ำ 10 เป้าหมาย 30 และ lead time 7 วันเป็นสมมติฐาน ไม่ได้คำนวณจากยอดขาย Lead time เป็นบริบทประกอบ ไม่ได้ใช้ทำนายวันที่รับของ

ตารางนโยบายมีบทบาทต่างจาก stock snapshot จึงเป็นแหล่งข้อมูลใหม่ ไม่ใช่แค่เพิ่มแถวในไฟล์เดิม เชื่อมด้วย product_id + location_id

## 3. ฟีเจอร์เพิ่มเติม

| ส่วนเพิ่ม | ไฟล์/ตารางหลัก | วิธีสาธิต |
|---|---|---|
| คิวรายการที่ต้องทบทวน | web/features.js | เปิดคิว เห็น SKU-0002, 0003, 0005 |
| บันทึกนโยบายพร้อมผู้ทบทวน เหตุผล version | core.py: review_policy; policy_reviews | SKU-0005 → กรอก 10/30/7 พร้อมเหตุผล → บันทึก → เปลี่ยน review เป็น low |
| ประวัตินโยบายก่อน–หลัง | policy_audit, policy_history | อ่านผู้ทบทวน เหตุผล ค่าเดิม/ใหม่ และเวลาบันทึกจริง |
| What-if ไม่เขียนทับ | core.py: what_if | SKU-0005 เป้าหมาย 30 → ทดลอง 40: เติม 29 → 39 แต่ค่าจริงยัง 30 |
| หน้าอธิบายธุรกิจและที่มาข้อมูล | GET /api/project, source_comparison.json | แสดงข้อมูลจากอาจารย์และ dataset ใหม่พร้อม hash |
| รายการกักกันบนหน้าจอ | web/features.js | หน้า “คุณภาพข้อมูล” มีทั้ง log และ 5 แถวกักกัน |
| โหมดซ้อมฐานข้อมูลแยก | run.py --demo-session | เริ่มใหม่ได้ทุกครั้งโดยไม่ลบฐานข้อมูลปกติ |
| แก้ connection ฐานข้อมูล | core.py: connect | ปิด connection แน่นอน แก้ไฟล์ถูกล็อกบน Windows |
| ตรวจนโยบายผิดขณะใช้งาน | core.py: risks | ข้อมูลเลขผิดไม่ทำให้หน้าสต็อกทั้งหมดล่ม ส่ง review |
| เก็บหลักฐานตอนแก้คำขอ | audit.payload.evaluated_evidence | ตรวจนโยบายที่ใช้ตอน update ย้อนหลังได้ |
| เพิ่ม tests 19–30 และตรวจ UI จริง | test_results/ | แสดง input/expected/actual และผลจริง |

ZIP ที่ผู้ใช้ส่งมี 18 tests และยังไม่มีฟีเจอร์ทบทวนนโยบาย/What-if แม้บทสนทนาเก่าจะกล่าวถึง 26 tests

## 4. ตัวอย่างปัญหาคุณภาพข้อมูล

1. SKU-0001 ในตารางใหม่เป็น ` sku-0001 `: strip และ uppercase ตามรูปแบบรหัส → join ได้
2. SKU-0002 ไม่มีขั้นต่ำ: ไม่เติมค่าเอง → quarantine + review
3. SKU-0005 เป้าหมาย 30 กับ 40 ใน key เดียว: กักกันทั้งคู่ → คนทบทวนพร้อมเหตุผล → ใช้นโยบายใหม่ใน SQLite

ทั้งสามกรณีเป็นกรณีทดสอบที่สร้างในข้อมูลนโยบายใหม่ ส่วนข้อมูลสินค้าต้นฉบับมีหมวดหมู่ตัวพิมพ์ต่างกัน เช่น kitchen/bedding/storage

นโยบาย 85 แถว = ใช้ได้ 79 + กักกัน 5 + ตัดแถวซ้ำ 1; สต็อกยังครบ 82 รายการ ไม่หายเพราะ join ไม่เจอ policy

