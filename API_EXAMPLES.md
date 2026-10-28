# ทดสอบ REST API ด้วย PowerShell

เปิด `python run.py` ใน terminal แรก แล้วใช้ terminal ที่สอง

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod 'http://127.0.0.1:8000/api/risks/SKU-0001?mode=demo'

$body = @{product_id='SKU-0001'; location_id='BKK-DC'; quantity=25; note='demo'; mode='demo'} | ConvertTo-Json
$created = Invoke-RestMethod http://127.0.0.1:8000/api/requests -Method Post -ContentType 'application/json' -Body $body
$created

$edit = @{quantity=28; note='edited'; version=$created.version; status='draft'} | ConvertTo-Json
Invoke-RestMethod "http://127.0.0.1:8000/api/requests/$($created.id)" -Method Put -ContentType 'application/json' -Body $edit
Invoke-RestMethod "http://127.0.0.1:8000/api/requests/$($created.id)"
Invoke-RestMethod "http://127.0.0.1:8000/api/requests/$($created.id)/history"
```

หากมีฉบับร่าง SKU-0001 เดิม POST จะตอบ 409 ให้แก้ไขหรือยกเลิกของเดิมผ่านหน้าจอก่อน ไม่ควรลบฐานข้อมูลเพื่อแก้ปัญหาคำขอซ้ำ

กรณี failure (PowerShell จะแสดง HTTP error ซึ่งเป็นผลคาดหวัง):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/risks/UNKNOWN
Invoke-RestMethod 'http://127.0.0.1:8000/api/risks?unavailable=1'
```

ได้ 404 และ 503 ตามลำดับ หน้าเว็บตรวจ `response.ok`, อ่าน `error`, แสดงข้อความ และล้างตารางสต็อกเพื่อไม่ให้ผู้ใช้ทำงานต่อจากข้อมูลเก่าเมื่ออ่านล้มเหลว
