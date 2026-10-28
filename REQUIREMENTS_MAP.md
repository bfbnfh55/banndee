# ผูกข้อกำหนดกับหลักฐาน

| ข้อกำหนด | หลักฐานในชุดงาน |
|---|---|
| หัวข้อใหม่ ไม่ทำ delayed order ซ้ำ | README: StockGuard / inventory drafts |
| ข้อมูล BaanDee + แหล่งใหม่ | raw products/inventory + generated policy |
| key และ data map | README Mermaid + composite key product/location |
| คุณภาพข้อมูล ≥3 ปัญหา | DATA_RULES, correction_log, quarantine, quality page |
| raw/clean แยกและเหตุผลแก้ไข | data/raw, generated, cleaned + manifest |
| ไม่เดาข้อมูลกำกวม | conflicting/missing invalid → review และ POST 409 |
| ขอบเขตระหว่างระบบ | browser HTTP JSON → Python REST API |
| success/not found/unavailable | HTTP 200,404,503; tests 01–03 |
| ผู้ใช้ input/select | search, filter, mode, form |
| หลักฐาน/source/time | detail dialog, evidence snapshot |
| create/save/read/update ถาวร | POST/GET/PUT, SQLite, audit, test 06 restart |
| safe deletion (optional) | cancelled + history, test 10 |
| tests ≥5 พร้อมผลจริง | tests/test_system.py + test_results |
| AI use explanation | AI_USE.md และเหตุผลไม่ใช้ AI ในผลิตภัณฑ์ |
| environment/dependencies | .env.example, requirements.txt |
| GitHub + release | ขั้นตอน GITHUB_SUBMISSION; ทีมยังต้องเผยแพร่จริง |
| demo 8+4 และสมาชิก | DEMO_8_MINUTES; ทีมกรอกชื่อและฝึกจริง |

ความพร้อมของโค้ด/ผลทดสอบไม่เท่ากับการยืนยันส่งครบ สมาชิก การตรวจของทีม URL GitHub และ tag/release ต้องทำตามจริงก่อนส่ง

ผลตรวจรอบปรับปรุง: HTTP/backend 30 กรณีผ่านทั้งหมด (ดูเวลารันใน results.json); ตรวจหน้าจอจริงตาม ui_review.json แล้ว ทั้งสองผลมีขอบเขตต่างกัน ไม่กล่าวอ้างว่า Playwright runner ผ่าน

| ส่วนเพิ่มรอบนี้ | หลักฐาน / test |
|---|---|
| มนุษย์ทบทวนแล้วทำงานต่อ | คิวทบทวน, POST policy-reviews, test 19 |
| input validation และป้องกันเขียนทับ | tests 20–21 |
| ไม่ทำให้ข้อมูลเก่าดูใหม่ / แยก demo-live | tests 22–23 |
| What-if ไม่บันทึก และหยุดเมื่อกำกวม | tests 24–25 |
| นโยบายเสียหายระหว่างใช้งาน | test 26 |
| เก็บ raw/quarantine และเทียบแหล่งที่มา | tests 27–28 |
| กรณีไม่พบรายการทบทวน | test 29 |
| หลักฐาน ณ เวลาแก้คำขอใน audit | test 30 |

ยังต้องทำโดยทีม: กรอกสมาชิก/บทบาทจริง, ตรวจและเข้าใจโค้ด, นำขึ้น GitHub, สร้าง tag v1.0-final, ซ้อม 8 นาทีและนัดอาจารย์ ไม่สร้างประวัติ commit หรือผลทดลองผู้ใช้แทนทีม
