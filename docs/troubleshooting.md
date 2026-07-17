# คู่มือแก้ปัญหา (Troubleshooting)

## 1) ปุ่มไม่ขึ้นบนหน้าจอ

สาเหตุที่พบบ่อย:

- count ของปุ่มนั้นเป็น `0`
- เอกสารยังไม่ได้เชื่อม relation กันจริง
- เปิดอยู่คนละประเภทเอกสารกับที่โค้ดรองรับ

วิธีตรวจ:

1. ลอง refresh หน้า (กด `F5`)
2. เปิดเอกสารปลายทางที่ควรเชื่อมกัน แล้วตรวจว่ามี relation จริง
3. ตรวจชนิดเอกสารว่าตรงกับที่ปุ่มนั้นรองรับ

หมายเหตุ:

- ทุก Smart Button ในโมดูลนี้ตั้งใจซ่อนเมื่อ count เป็น `0`

## 2) `Purchase Order` ไม่มีปุ่ม `Receipts`, `Vendor Bills`, `Payments` หรือ `Vendor Credit Notes`

ตรวจตามนี้:

1. ใบสั่งซื้อถูกยืนยันแล้วหรือยัง
2. มี `Receipt` เกิดใน `picking_ids` แล้วหรือยัง
3. มี bill เชื่อมกับ `order_line.invoice_lines.move_id` แล้วหรือยัง
4. bill หรือ credit note ถูกยกเลิก (`cancel`) ไปแล้วหรือไม่
5. ถ้าคาดว่าต้องมี `Payments` ให้ตรวจว่ามีการ reconcile กับ bill แล้วหรือยัง
6. ถ้าคาดว่าต้องมี `Vendor Credit Notes` ให้ตรวจว่ามี `in_refund` อยู่ใน `invoice_ids` หรือมี credit note ย้อนมาจาก `reversal_move_id` หรือไม่

กติกาของโค้ด:

- `Receipts` ดึงตรงจาก `picking_ids`
- `Vendor Bills` ดึงจาก bill ที่โยงกับ PO line และนับเฉพาะ `move_type = in_invoice`
- `Payments` ดึงจาก payment ที่ reconcile กับ vendor bills ของ PO
- `Vendor Credit Notes` แยกอีกปุ่ม และนับเฉพาะ `move_type = in_refund`
- เอกสารหรือ payment ที่ `state = cancel` จะไม่ถูกนับ

## 3) `Receipt` ไม่มีปุ่ม `Purchase Orders`, `Vendor Bills` หรือ `Payments`

ตรวจตามนี้:

1. Receipt ใบนั้นมาจาก Purchase Order จริงหรือไม่
2. ฟิลด์ `purchase_id` มีค่าหรือไม่
3. ถ้า `purchase_id` ไม่มี ให้ตรวจว่ามี `move_ids_without_package.purchase_line_id.order_id` หรือไม่
4. มี bill/refund ที่โยงผ่าน Purchase Order แล้วหรือยัง
5. ถ้าคาดว่าต้องมี `Payments` ให้ตรวจว่ามี payment ที่ reconcile กับ bill/refund ใน chain นี้แล้วหรือยัง

กติกาของโค้ด:

- ระบบจะใช้ `purchase_id` ก่อน
- ถ้าไม่มี จึง fallback ไปดู purchase line บน stock move
- `Vendor Bills` ของ Receipt รวม `in_invoice` และ `in_refund`
- `Payments` ของ Receipt ดึงจาก reconciled payments ของเอกสารบัญชีที่เกี่ยวข้อง
- เอกสารที่ `cancel` จะไม่ถูกนับ
- payment ที่ `cancel` จะไม่ถูกนับ

## 4) `Vendor Bill` ไม่มีปุ่ม `Purchase Orders`, `Receipts` หรือ `Payments`

สาเหตุที่พบบ่อย:

- เอกสารนี้ไม่ใช่ `Vendor Bill` แต่เป็น `Vendor Credit Note`
- บรรทัด invoice ไม่มี `purchase_line_id`
- bill ยังไม่ถูกจ่ายหรือยังไม่ reconcile

กติกาของโค้ด:

- ถ้าเป็น `Vendor Bill` (`move_type = in_invoice`)
  - `Purchase Orders` ดึงจาก `invoice_line_ids.purchase_line_id.order_id`
  - `Receipts` ดึงจาก `purchase orders.mapped("picking_ids")`
  - `Payments` ดึงจาก `_get_reconciled_payments()`
- ถ้าเป็น `Vendor Credit Note` (`move_type = in_refund`)
  - `Purchase Orders` และ `Receipts` ยังสามารถขึ้นได้
  - แต่ `Payments` จะไม่ถูกคำนวณ

วิธีตรวจ:

1. เปิดดูชนิดเอกสาร (`move_type`)
2. ถ้าเป็น `Vendor Bill` ให้ตรวจบรรทัดสินค้า/บริการว่ามาจาก PO line หรือไม่
3. ถ้าปุ่ม `Payments` ไม่ขึ้น ให้ตรวจว่ามี payment และ reconcile แล้วหรือยัง
4. ถ้าเป็น `Vendor Credit Note` และไม่มี `Purchase Orders` / `Receipts` ให้ตรวจว่า credit note นี้ย้อนกลับไป source bill ได้หรือมี `purchase_line_id` บน invoice lines หรือไม่

## 5) `Vendor Credit Note` ไม่มีปุ่ม `Purchase Orders` หรือ `Receipts`

สาเหตุที่พบบ่อย:

- credit note นี้ไม่ได้ย้อนมาจาก `Vendor Bill` ที่มี PO relation
- `reversed_entry_id` ไม่พาไปยัง source bill ที่เกี่ยวข้อง
- บรรทัด credit note ไม่มี `purchase_line_id`

กติกาของโค้ด:

- ระบบจะพยายามหา source bills จาก `reversed_entry_id` ก่อน
- ถ้าพบ source bill จะ reuse purchase links จาก bill ต้นทาง
- ถ้าไม่พบ จะ fallback ไปที่ `invoice_line_ids.purchase_line_id.order_id`
- `Payments` จะไม่ถูกนับสำหรับ `Vendor Credit Note`

วิธีตรวจ:

1. เปิด credit note และดูว่าเอกสารนี้ reverse มาจาก bill ใด
2. ตรวจว่าต้นทางมี PO / Receipt links จริงหรือไม่
3. ถ้าไม่ใช่ credit note ที่ reverse มา ให้ตรวจ `purchase_line_id` ของบรรทัดเอกสาร

## 6) `Payment` ไม่มีปุ่ม `Bills`

สาเหตุที่พบบ่อย:

- payment ยังไม่ถูกจับคู่กับ bill ผ่าน reconciliation
- bill ที่จับคู่ถูกยกเลิก
- payment นี้ไม่ใช่การจ่ายที่โยงกับ vendor bill/refund

กติกาของโค้ด:

- ระบบหา bill จากคู่รายการบัญชีที่ `matched_debit_ids` / `matched_credit_ids`
- กรองเฉพาะ account type ที่เป็น `receivable` หรือ `payable`
- นับเฉพาะ `in_invoice` และ `in_refund` ที่ไม่ถูกยกเลิก

วิธีตรวจ:

1. เปิด journal entry ของ payment
2. ตรวจว่ามีการ match กับบรรทัดของ bill จริงหรือไม่
3. ตรวจว่าบิลปลายทางยังไม่เป็น `cancel`

## 7) `Partner` ไม่มีปุ่ม `Sale Orders`, `Deliveries`, `Customer Invoices`, `Customer Credit Notes`, `Customer Payments`, `Purchase Orders`, `Vendor Bills` หรือ `Payments`

สาเหตุที่พบบ่อย:

- partner นี้ไม่มี sale order ที่ `partner_id` ตรงกัน
- partner นี้ไม่มี delivery ที่มาจาก sale-order chain แบบ `outgoing` และยังไม่ถูกยกเลิก
- partner นี้ไม่มี `Customer Invoice` (`out_invoice`) ที่ยังไม่ถูกยกเลิก
- partner นี้ไม่มี `Customer Credit Note` (`out_refund`) ที่ยังไม่ถูกยกเลิก
- partner นี้ยังไม่มี payment ลูกหนี้ที่ reconcile กับ `Customer Invoice` หรือ `Customer Credit Note` ของตน
- มี customer payment อยู่จริง แต่ยัง unmatched จึงไม่ขึ้นใน `Customer Payments`
- partner นี้ไม่มี PO ที่ `partner_id` ตรงกัน
- partner นี้ไม่มี `Vendor Bill` (`in_invoice`) ที่ยังไม่ถูกยกเลิก
- partner มีแต่ `Vendor Credit Note` จึงไม่ขึ้นในปุ่ม `Vendor Bills`
- ยังไม่มี payment ที่ reconcile กับ vendor bills ของ partner นี้

กติกาของโค้ด:

- `Sale Orders` ค้นจาก `sale.order` ด้วย `partner_id = self.id`
- `Deliveries` ดึงจาก `sale_order_ids.mapped("picking_ids")`
- `Deliveries` จะนับเฉพาะ `picking_type_code = outgoing` และ `state != cancel`
- `Deliveries` จึงไม่รวม return pickings แม้อยู่ใน sale-order chain เดียวกัน
- `Customer Invoices` ค้นจาก `account.move` ด้วย `partner_id = self.id`, `move_type = out_invoice`, `state != cancel`
- `Customer Credit Notes` ค้นจาก `account.move` ด้วย `partner_id = self.id`, `move_type = out_refund`, `state != cancel`
- `Customer Payments` ดึงจาก `_get_reconciled_payments()` ของ `Customer Invoices` และ `Customer Credit Notes`
- `Customer Payments` นับเฉพาะ payment ที่ matched แล้ว, ตัด unmatched ออก, ตัด `cancel` ออก และ dedupe รายการซ้ำอัตโนมัติ
- `Purchase Orders` ค้นจาก `purchase.order` ด้วย `partner_id = self.id`
- `Vendor Bills` ค้นจาก `account.move` ด้วย `partner_id = self.id`, `move_type = in_invoice`, `state != cancel`
- `Payments` ดึงจาก reconciled payments ของ vendor bills ที่หาได้

วิธีตรวจ:

1. เปิด `Sale Order` หรือ `Purchase Order` ที่เกี่ยวข้อง แล้วตรวจ `partner_id`
2. ถ้าปุ่ม `Deliveries` ไม่ขึ้น ให้ตรวจว่า picking นั้นอยู่ใน sale-order chain ของ partner จริงหรือไม่
3. ตรวจว่า picking เป็น `outgoing` และไม่ได้ถูก `cancel`
4. ถ้าคาดว่าควรมี `Customer Payments` ให้เปิด invoice / credit note ของลูกค้าแล้วตรวจว่ามี reconciliation กับ payment แล้วจริงหรือไม่
5. ถ้ามี payment ลูกค้าแต่ยัง unmatched การไม่ขึ้นของปุ่ม `Customer Payments` ถือว่าตรงตามโค้ดปัจจุบัน
6. เปิดเอกสารบัญชีแล้วตรวจ `move_type` ว่าเป็น `out_invoice`, `out_refund` หรือ `in_invoice` ให้ตรงกับปุ่มที่คาด
7. ถ้ามีแต่ `Vendor Credit Note` การไม่ขึ้นของปุ่ม `Vendor Bills` ถือว่าตรงตามโค้ดปัจจุบัน
8. ถ้าคาดว่าควรมี `Payments` ให้ตรวจ reconciliation ของ vendor bills เหล่านั้น

## 8) กดปุ่มแล้วเปิดไม่ได้

สาเหตุที่พบบ่อย:

- ผู้ใช้ไม่มีสิทธิ์ (Access Right) ของเอกสารปลายทาง

วิธีแก้:

1. ให้ Admin ตรวจสิทธิ์ของผู้ใช้
2. ทดลองด้วยผู้ใช้ที่เป็น Admin
3. ตรวจว่าปลายทางเป็น model ไหน เช่น `purchase.order`, `stock.picking`, `account.move`, `account.payment`

## 9) เปิดแล้วเห็นรายการไม่ครบตามที่คาด

สาเหตุที่พบบ่อย:

- โค้ดกรองเอกสารบางประเภทออกโดยตั้งใจ
- เอกสารถูกยกเลิก
- เอกสารยังไม่โยง relation หรือยังไม่ reconcile

ตัวอย่างที่ต้องรู้:

- `Purchase Order -> Vendor Bills` และ `Receipt -> Vendor Bills`
  - พฤติกรรมไม่เหมือนกัน
  - `Purchase Order -> Vendor Bills` นับเฉพาะ `Vendor Bill`
  - `Receipt -> Vendor Bills` รวม `Vendor Bill` และ `Vendor Credit Note`
  - `Purchase Order -> Vendor Credit Notes` มีปุ่มแยกต่างหาก
  - ตัด `cancel` ออก
- `Purchase Order -> Payments` และ `Receipt -> Payments`
  - แสดงเฉพาะ payment ที่ reconcile แล้ว
  - ตัด payment ที่ `cancel` ออก
- `Vendor Bill -> Payments`
  - แสดงเฉพาะ payment ที่ reconcile แล้ว
  - ตัด payment ที่ `cancel` ออก
- `Vendor Credit Note`
  - ยังสามารถแสดง `Purchase Orders` และ `Receipts` ได้
  - แต่ไม่แสดง `Payments`
- `Partner -> Deliveries`
  - รวมเฉพาะ picking ที่ derive มาจาก sale-order chain
  - และต้องเป็น `outgoing` + ไม่ถูกยกเลิก
  - จึงไม่รวม return pickings แต่ยังรวม outgoing backorders จาก partial delivery
- `Partner -> Customer Invoices`
  - รวมเฉพาะ `out_invoice`
  - ไม่รวม `Customer Credit Note`
- `Partner -> Customer Credit Notes`
  - รวมเฉพาะ `out_refund`
  - ไม่รวม `Customer Invoice`
- `Partner -> Customer Payments`
  - รวมเฉพาะ matched customer payments ที่ reconcile กับ customer invoices / credit notes แล้ว
  - ไม่รวม payment ลูกค้าที่ unmatched
  - ไม่รวม payment ที่ `cancel`
  - ถ้า payment เดิมเชื่อมกับ customer moves หลายใบ ระบบจะแสดงเพียงครั้งเดียว
- `Partner -> Vendor Bills`
  - รวมเฉพาะ `Vendor Bill`
  - ไม่รวม `Vendor Credit Note`

## 10) หน้าเอกสารโหลดช้ากว่าที่คาด

สิ่งที่ควรเข้าใจก่อน:

- ฟิลด์ smart links เหล่านี้เป็น compute field แบบไม่เก็บลงฐานข้อมูล
- เวลาที่เปิดฟอร์ม ระบบจะคำนวณจาก relation ปัจจุบันทันที

แนวทางตรวจแบบใช้งานจริง:

1. ตรวจว่าเอกสารใบเดียวเชื่อมกับ receipt, bill หรือ payment จำนวนมากผิดปกติหรือไม่
2. ถ้าช้าที่หน้า partner ให้ตรวจว่าคู่ค้ารายนั้นมี PO หรือ bills จำนวนมากหรือไม่
3. ตรวจว่ามี customization อื่นซ้อนบน model เดียวกันหรือไม่
4. ทดสอบด้วย Admin เพื่อแยกว่าเป็นเรื่องสิทธิ์หรือเวลาคำนวณ
5. ถ้าช้าเฉพาะบางเอกสาร ให้ไล่ดูจำนวน relation ของใบนั้นก่อน
6. ถ้าช้าที่หน้า partner ให้แยกว่าเกิดจากฝั่ง sales (`Sale Orders`, `Deliveries`, `Customer Invoices`, `Customer Credit Notes`, `Customer Payments`) หรือฝั่ง purchasing (`Purchase Orders`, `Vendor Bills`, `Payments`)

หมายเหตุ:

- final code state ไม่มี `search()` แบบกว้างข้ามทั้งโมเดลสำหรับ document smart links ฝั่ง purchase/accounting
- `Receipt` มี guard โดยใช้ `purchase_id` ก่อน fallback
- `Partner` เป็นข้อยกเว้นที่ใช้ `search()` แบบระบุ `partner_id` โดยตรงกับ `sale.order`, `purchase.order` และ `account.move`
- ใน compute ของ `Partner` มีการ reuse `sale orders`, `customer invoices` และ `customer credit notes` ที่หาได้แล้วบางชุด เพื่อลดงานซ้ำในรอบคำนวณเดียวกัน
- `Partner -> Deliveries` จะ derive ต่อจาก sale orders ที่หาได้ ไม่ได้ query `stock.picking` ตรงแบบกว้าง
- `Partner -> Customer Payments` จะ derive จาก customer moves ที่ compute รวมไว้แล้ว ไม่ได้ query `account.payment` ตรงแบบกว้าง
- `Partner -> Payments` จะ derive จาก reconciled payments ของ vendor bills ที่หาได้ ไม่ได้ query `account.payment` ตรงแบบกว้าง
- ถ้าช้า มักสัมพันธ์กับจำนวน relation ที่ต้อง `mapped()` / `filtered()` หรือจำนวน sale orders, invoices, customer payments, PO, bills และ payments ของ partner นั้น

## 11) นับ `Credit Notes` ไม่ถูก

กติกาของโมดูล:

- นับเฉพาะ Credit Note ที่เป็น
  - `move_type = out_refund`
  - `state = posted`

ดังนั้น:

- `draft` ไม่นับ
- `cancelled` ไม่นับ

## 12) `Debit Notes` ไม่ขึ้น (เฉพาะบางระบบ)

สาเหตุ:

- ระบบบางที่ไม่มีโมดูล `dtr_dncn`
- โมดูลนี้รองรับแบบ "มี ก็ใช้ / ไม่มี ก็ไม่พัง"

วิธีตรวจแบบง่าย:

1. ให้ Admin เปิด `Apps`
2. ค้นหา `dtr_dncn`
3. ถ้าไม่มี ก็เป็นไปได้ว่า debit note แบบ fallback จะไม่ขึ้น

## 13) ติดตั้งไม่ได้ / อัปเดตไม่ได้

สาเหตุที่พบบ่อย:

- addons path ไม่เจอโมดูล
- มี error ใน XML หรือ Python
- dependency ไม่ครบ โดยเฉพาะ `purchase_stock`

วิธีแก้:

1. ตรวจว่าโฟลเดอร์อยู่ที่ถูกที่
   - `/var/odoo/custom15_autoinfo/autoinfo_document_smart_links`
2. ตรวจ dependency ให้ครบ
3. อัปเดต Apps List แล้วลองติดตั้งใหม่
4. ถ้ายังไม่ผ่าน ให้ดู log ของ Odoo

## 14) ถอนโมดูลแล้วมี error

แนวทางที่แนะนำ:

1. ถอนผ่าน Odoo Shell
2. ใช้คำสั่ง `button_immediate_uninstall()`

ดูตัวอย่างในไฟล์ `docs/technical_guide.md`
