# autoinfo_document_smart_links (Odoo 15.0)

## โมดูลนี้คืออะไร

โมดูลนี้เพิ่ม Smart Button สำหรับเปิดเอกสารที่เชื่อมโยงกันใน flow การขาย การซื้อ การจ่ายเงิน และคู่ค้า โดยอิง relation ที่มีอยู่จริงใน Odoo 15 และไม่แก้ไฟล์ core ของระบบ

## โมดูลนี้ทำอะไรได้

### ฝั่งขาย

- หน้า `Sale Order`
  - `Credit Notes`
  - `Debit Notes`
- หน้า `Delivery` / `Stock Picking`
  - `Accounting Documents`
- หน้า `Invoice` / `Account Move`
  - `Sale Orders`
  - `Deliveries`
  - `Adjustments`

### ฝั่งซื้อ จ่ายเงิน และคู่ค้า

- หน้า `Purchase Order`
  - `Receipts`
  - `Vendor Bills`
  - `Payments`
  - `Vendor Credit Notes`
- หน้า `Receipt` / `Stock Picking`
  - `Purchase Orders`
  - `Vendor Bills`
  - `Payments`
- หน้า `Vendor Bill` / `Vendor Credit Note` / `Account Move`
  - `Purchase Orders`
  - `Receipts`
  - `Payments`
- หน้า `Payment` / `Account Payment`
  - `Bills`
- หน้า `Partner`
  - `Sale Orders`
  - `Deliveries`
  - `Customer Invoices`
  - `Customer Credit Notes`
  - `Customer Payments`
  - `Purchase Orders`
  - `Vendor Bills`
  - `Payments`

## พฤติกรรมหลักของปุ่ม

- ปุ่มจะซ่อนอัตโนมัติเมื่อจำนวนเอกสารที่เกี่ยวข้องเป็น `0`
- ถ้ามีเอกสารที่เกี่ยวข้อง `1` ใบ ระบบจะเปิดหน้า form ของใบนั้นทันที
- ถ้ามีหลายใบ ระบบจะเปิดเป็นรายการแบบ `tree,form`
- action ทุกตัวจำกัดผลลัพธ์ด้วย domain เฉพาะ record ที่เกี่ยวข้องจริง

## กติกาที่สำคัญของ purchase-side smart links

- `Purchase Order -> Receipts`
  - ดึงตรงจาก `picking_ids`
- `Purchase Order -> Vendor Bills`
  - ดึงจาก `order_line.invoice_lines.move_id`
  - นับเฉพาะ `move_type = in_invoice`
  - ตัดเอกสาร `state = cancel` ออก
- `Purchase Order -> Payments`
  - ดึงจาก payment ที่ reconcile กับ vendor bills ของ PO
  - ตัด payment ที่ `state = cancel` ออก
- `Purchase Order -> Vendor Credit Notes`
  - ดึงจาก `invoice_ids` ที่เป็น `in_refund`
  - และรวม credit note ที่ย้อนกลับมาจาก vendor bill ผ่าน `reversal_move_id`
  - ตัดเอกสาร `state = cancel` ออก
- `Receipt -> Purchase Orders`
  - ใช้ `purchase_id` ก่อนถ้ามี
  - ถ้าไม่มี จะ fallback ไปที่ `move_ids_without_package.purchase_line_id.order_id`
- `Receipt -> Vendor Bills`
  - หา Purchase Order ที่เกี่ยวข้องก่อน แล้วดึง `invoice_ids`
  - รวมทั้ง `in_invoice` และ `in_refund`
  - ตัดเอกสาร `state = cancel` ออก
- `Receipt -> Payments`
  - ดึงจาก payment ที่ reconcile กับ vendor bills / vendor credit notes ของ receipt chain
  - ตัด payment ที่ `state = cancel` ออก
- `Vendor Bill -> Purchase Orders / Receipts`
  - ทำงานจาก `purchase_line_id.order_id` และ `picking_ids`
- `Vendor Bill -> Payments`
  - ดึงจาก `_get_reconciled_payments()`
  - ตัด payment ที่ `state = cancel` ออก
- `Vendor Credit Note -> Purchase Orders / Receipts`
  - พยายามย้อนจาก `reversed_entry_id` ไปหา source vendor bill ก่อน
  - ถ้าไม่พบ จะ fallback ไปที่ `invoice_line_ids.purchase_line_id.order_id`
- `Vendor Credit Note -> Payments`
  - โค้ดปัจจุบันตั้งใจไม่คำนวณ payment links ให้ `in_refund`
  - ดังนั้นปุ่ม `Payments` บน credit note จะมี count เป็น `0`
- `Payment -> Bills`
  - หา bill จากคู่รายการทางบัญชีที่จับคู่ reconciliation กัน
  - กรองเฉพาะ account type `receivable` และ `payable`
  - นับเฉพาะ `in_invoice` และ `in_refund` ที่ไม่ถูกยกเลิก
- `Partner -> Sale Orders`
  - ค้นจาก `sale.order` ด้วย `partner_id`
- `Partner -> Deliveries`
  - ดึงจาก `sale.order` ของ partner ก่อน
  - แล้วตาม `picking_ids` ของ sale order chain ทั้งชุด
  - นับเฉพาะ picking ที่ `picking_type_code = outgoing`
  - และ `state != cancel`
  - จึงรวม outgoing backorder / partial-delivery chain ที่ยังเกี่ยวข้อง
  - และไม่รวม return pickings
- `Partner -> Customer Invoices`
  - ค้นจาก `account.move` ด้วย `partner_id`
  - นับเฉพาะ `move_type = out_invoice`
  - ตัดเอกสาร `state = cancel` ออก
- `Partner -> Customer Credit Notes`
  - ค้นจาก `account.move` ด้วย `partner_id`
  - นับเฉพาะ `move_type = out_refund`
  - ตัดเอกสาร `state = cancel` ออก
- `Partner -> Customer Payments`
  - ดึงจาก `_get_reconciled_payments()` ของ `Customer Invoices` และ `Customer Credit Notes`
  - นับเฉพาะ payment ฝั่งลูกหนี้ที่ถูกจับคู่ reconciliation แล้วจริง
  - payment ที่ยัง unmatched จะไม่ถูกนับ
  - ตัด payment ที่ `state = cancel` ออก
  - ผลลัพธ์เป็น recordset แบบ unique จึง dedupe อัตโนมัติ แม้ payment เดิมจะอ้างถึง customer moves ซ้ำหรือหลายใบ
- `Partner -> Purchase Orders`
  - ค้นจาก `purchase.order` ด้วย `partner_id`
- `Partner -> Vendor Bills`
  - ค้นจาก `account.move` ด้วย `partner_id`
  - นับเฉพาะ `move_type = in_invoice`
  - ตัดเอกสาร `state = cancel` ออก
- `Partner -> Payments`
  - ดึงจาก payment ที่ reconcile กับ vendor bills ของ partner
  - จึงไม่ใช่ปุ่มรวม payment ของ vendor credit note โดยตรง

## หมายเหตุเรื่อง performance guard ตามโค้ดจริง

- ฝั่ง `purchase.order`, `stock.picking`, `account.move` และ `account.payment` ใช้ relation traversal เป็นหลัก เช่น `mapped()`, `filtered()`, `picking_ids`, `purchase_line_id.order_id` และข้อมูล reconciliation
- `stock.picking` ใช้ `purchase_id` ก่อน แล้วค่อย fallback ไปที่ stock move เพื่อเลี่ยงการไล่ relation ที่ไม่จำเป็น
- action ทุกตัวจำกัด `domain` ไว้ที่ `id` ของ record ที่เกี่ยวข้องจริง
- ฟิลด์ smart links เป็น compute field แบบไม่เก็บลงฐานข้อมูล จึงแสดงข้อมูลสดตาม relation ปัจจุบัน
- สำหรับ `res.partner` final code state ใช้ `search()` แบบมี domain แคบที่ `partner_id = self.id` เพื่อหา `Sale Orders`, `Purchase Orders`, `Customer Invoices`, `Customer Credit Notes` และ `Vendor Bills`
- ใน `_compute_smart_partner_links()` มีการ reuse `sale_orders`, `customer_invoices` และ `customer_credit_notes` ที่หาได้แล้ว แทนการค้นซ้ำในรอบ compute เดียว
- `Deliveries` ของ partner ไม่ได้ `search()` ตรงบน `stock.picking`; โค้ดจะ reuse `sale_orders` ที่ compute หาไว้ แล้ว derive จาก `picking_ids` ของ sale-order chain และกรองเฉพาะ `outgoing` กับ `state != cancel`
- `Customer Payments` ของ partner มี helper ที่รับ `customer_moves` เข้ามาได้ เพื่อ reuse ชุด `Customer Invoices + Customer Credit Notes` ที่ compute รวมไว้แล้ว แล้วค่อยดึงเฉพาะ reconciled payments
- `Payments` ของ partner ไม่ได้ `search()` ตรงบน `account.payment`; โค้ดจะ derive จาก `_get_reconciled_payments()` ของ `Vendor Bills` ที่หาได้ แล้วตัด payment ที่ `state = cancel` ออก
- performance guard ของ `res.partner` ตามของจริงจึงอยู่ที่การใช้ domain แคบด้วย `partner_id`, การ derive relation ต่อจาก recordset ที่หาไว้แล้วในจุดที่เหมาะสม, และการหลีกเลี่ยง broad search บน `stock.picking` / `account.payment`
- ในงานจริง หน้าจอจะตอบสนองได้ดีเมื่อจำนวน relation ต่อเอกสารไม่สูงผิดปกติ แต่ถ้า partner หนึ่งรายผูกกับ sale orders, deliveries, invoices, PO, bills หรือ payments จำนวนมาก เวลา compute อาจเพิ่มขึ้นตามปริมาณ relation

## ขอบเขต

- ใช้กับ Odoo `15.0`
- เป็นโมดูลแบบ EXTENDED
- ไม่แก้ไฟล์ core ของ Odoo

## สิ่งที่ต้องมี ก่อนเริ่ม

- ติดตั้งโมดูลมาตรฐาน
  - `sale_stock`
  - `purchase`
  - `purchase_stock`
  - `account`
- ผู้ใช้ต้องมีสิทธิ์ดูเอกสารปลายทางที่กดเปิดจากปุ่ม

## ติดตั้งแบบสรุป

1. วางโฟลเดอร์โมดูลไว้ที่
   - Production (Linux): `/var/odoo/custom15_autoinfo/autoinfo_document_smart_links`
2. อัปเดตรายการแอป (Update Apps List)
3. ติดตั้งโมดูล `autoinfo_document_smart_links`

## เจ้าของงาน

- Original Owner (จาก manifest เดิม): AutoInfo
- Current Owner: The Auto-Info Co., Ltd.

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon - Project conception, implementation, and thorough review of all deliverables.

AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight.

## Change Log (สรุป)

- 2026-06-30
  - เพิ่มเอกสาร README และคู่มือในโฟลเดอร์ `docs`
  - ปรับข้อมูลใน manifest ให้ตรงกับการใช้งานจริง
- 2026-07-10
  - อัปเดตเอกสารให้ครอบคลุม purchase-side smart links และ note เรื่อง performance ตาม final code state
- 2026-07-11
  - อัปเดตเอกสารให้ตรงกับ deep purchase/accounting links และ partner smart links
  - เพิ่มรายละเอียด `Purchase Order -> Payments / Vendor Credit Notes`
  - เพิ่มรายละเอียด `Receipt -> Payments`
  - เพิ่ม behavior ของ `Vendor Credit Note`
  - เพิ่ม note เรื่อง `res.partner` performance guard ตาม implementation จริง
- 2026-07-16
  - อัปเดตเอกสารให้ครอบคลุม partner sales-side smart links
  - แยก `Customer Invoices` ออกจาก `Customer Credit Notes` ตาม `move_type`
  - ระบุว่า `Partner -> Deliveries` มาจาก sale-order chain, outgoing และ non-cancelled เท่านั้น
  - ทบทวน note เรื่อง performance guard ของ `res.partner` ให้ตรงกับ final code state
- 2026-07-17
  - อัปเดตเอกสารให้ครอบคลุม `Partner -> Customer Payments`
  - ระบุว่า customer payments นับเฉพาะ matched payments และไม่รวม unmatched payments
  - เพิ่มหมายเหตุเรื่อง dedupe ของ customer payments และ deliveries depth ที่ไม่รวม return pickings
  - ปรับ note เรื่อง compute reuse / performance guard บน `res.partner` ให้ตรงกับโค้ดจริง
  - ตัด smart button `Receipts` และ `Vendor Bills` ที่ซ้ำบนหน้า `Purchase Order`
  - คงปุ่มมาตรฐานของ Odoo สำหรับ `Receipt` และ `Vendor Bills` เอาไว้
  - เพิ่ม regression test กันปุ่มซ้ำบนหน้า `Purchase Order`
