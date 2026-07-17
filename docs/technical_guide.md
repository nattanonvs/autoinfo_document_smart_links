# คู่มือช่าง (Technical Guide)

## 1) โมดูลนี้ทำงานกับอะไร

- Odoo `15.0`
- โมดูลนี้เป็นแบบ EXTENDED
- dependency ตาม `__manifest__.py`
  - `sale_stock`
  - `purchase`
  - `purchase_stock`
  - `account`

## 2) ตำแหน่งโฟลเดอร์ (Production)

วางโมดูลไว้ที่:

- `/var/odoo/custom15_autoinfo/autoinfo_document_smart_links`

## 3) ติดตั้ง (Installation)

### A) ผ่านหน้าเว็บ Odoo

1. เปิด Odoo
2. ไปที่ `Apps`
3. กด `Update Apps List`
4. ค้นหา `autoinfo_document_smart_links`
5. กด `Install`

### B) ผ่านคำสั่ง (สำหรับช่าง)

คำว่า `-d` แปลว่า "ชื่อฐานข้อมูล"

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf \
  -d <database_name> \
  -i autoinfo_document_smart_links \
  --stop-after-init
```

## 4) อัปเดตโมดูล (Update / Upgrade)

ใช้เมื่อมีการเปลี่ยนโค้ด

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf \
  -d <database_name> \
  -u autoinfo_document_smart_links \
  --stop-after-init
```

## 5) ถอนโมดูล (Uninstall)

แนะนำถอนผ่าน Odoo Shell

เปิด Odoo Shell:

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  shell \
  -c /etc/odoo/odoo.conf \
  -d <database_name>
```

แล้วรัน:

```python
module = env["ir.module.module"].search([("name", "=", "autoinfo_document_smart_links")], limit=1)
if module and module.state == "installed":
    module.button_immediate_uninstall()
```

## 6) โครงสร้างหลักของโมดูล

- `models/sale_order.py`
  - smart links ฝั่งขายสำหรับ `Credit Notes` และ `Debit Notes`
- `models/purchase_order.py`
  - smart links ฝั่งซื้อจาก `Purchase Order` ไป `Receipts`, `Vendor Bills`, `Payments`, `Vendor Credit Notes`
- `models/stock_picking.py`
  - smart links จาก `Receipt` ไป `Purchase Orders`, `Vendor Bills`, `Payments`
  - smart links เดิมจาก `Delivery` ไป `Accounting Documents`
- `models/account_move.py`
  - smart links ฝั่งขายจาก `Invoice` ไป `Sale Orders`, `Deliveries`, `Adjustments`
  - smart links ฝั่งซื้อจาก `Vendor Bill` / `Vendor Credit Note` ไป `Purchase Orders`, `Receipts`, `Payments`
- `models/account_payment.py`
  - smart links จาก `Payment` ไป `Bills`
- `models/res_partner.py`
  - smart links จาก `Partner` ไป `Sale Orders`, `Deliveries`, `Customer Invoices`, `Customer Credit Notes`, `Customer Payments`, `Purchase Orders`, `Vendor Bills`, `Payments`
- `views/`
  - ปุ่ม Smart Button บน form view
- `tests/`
  - regression tests ฝั่งขาย ฝั่งซื้อ และ partner smart links
- `docs/`
  - คู่มือและเอกสารประกอบ

## 7) Mapping ของ purchase-side smart links

### A) `purchase.order`

- ฟิลด์
  - `smart_receipt_ids`
  - `smart_receipt_count`
  - `smart_vendor_bill_ids`
  - `smart_vendor_bill_count`
  - `smart_payment_ids`
  - `smart_payment_count`
  - `smart_vendor_credit_note_ids`
  - `smart_vendor_credit_note_count`
- helper
  - `_get_related_receipts()`
  - `_get_related_vendor_bills()`
  - `_get_related_payments()`
  - `_get_related_vendor_credit_notes()`
- action
  - `action_view_smart_receipts()`
  - `action_view_smart_vendor_bills()`
  - `action_view_smart_payments()`
  - `action_view_smart_vendor_credit_notes()`
- source relation
  - receipt ใช้ `picking_ids`
  - vendor bill ใช้ `order_line.invoice_lines.mapped("move_id")`
  - payment ใช้ reconciled payments ของ vendor bills
  - vendor credit note ใช้ทั้ง `invoice_ids` และ `bills.mapped("reversal_move_id")`
- filter ของ vendor bill
  - `state != "cancel"`
  - `move_type == "in_invoice"`
- filter ของ vendor credit note
  - `state != "cancel"`
  - `move_type == "in_refund"`

### B) `stock.picking`

- ฟิลด์ฝั่งซื้อ
  - `smart_purchase_order_ids`
  - `smart_purchase_order_count`
  - `smart_vendor_bill_ids`
  - `smart_vendor_bill_count`
  - `smart_payment_ids`
  - `smart_payment_count`
- helper
  - `_get_related_purchase_orders()`
  - `_get_related_vendor_bills()`
  - `_get_related_payments()`
- action
  - `action_view_smart_purchase_orders()`
  - `action_view_smart_vendor_bills()`
  - `action_view_smart_payments()`
- source relation
  - ใช้ `purchase_id` ก่อน
  - ถ้าไม่มี `purchase_id` ใช้ `move_ids_without_package.mapped("purchase_line_id.order_id")`
- filter ของ vendor bill
  - `state != "cancel"`
  - `move_type in ("in_invoice", "in_refund")`
- payment relation
  - ใช้ `_get_reconciled_payments()` จาก vendor bills / credit notes ที่เกี่ยวข้อง
  - ตัด `state = "cancel"` ออก

### C) `account.move` ฝั่งซื้อ

- ฟิลด์
  - `smart_purchase_order_ids`
  - `smart_purchase_order_count`
  - `smart_receipt_ids`
  - `smart_receipt_count`
  - `smart_payment_ids`
  - `smart_payment_count`
- helper
  - `_is_vendor_bill_for_smart_links()`
  - `_is_vendor_credit_note_for_smart_links()`
  - `_get_vendor_credit_note_source_bills()`
  - `_get_related_purchase_orders()`
  - `_get_related_receipts()`
  - `_get_related_payments()`
- action
  - `action_view_smart_purchase_orders()`
  - `action_view_smart_receipts()`
  - `action_view_smart_payments()`
- gating rule
  - `Payments` ทำงานเฉพาะเมื่อ `move_type == "in_invoice"`
  - `Purchase Orders` และ `Receipts` รองรับทั้ง `in_invoice` และ `in_refund`
  - ถ้าเป็น `in_refund` ระบบจะพยายามย้อนจาก `reversed_entry_id` ไปหา source bill ก่อน
  - ถ้าย้อนไม่ได้ จะ fallback ไปใช้ `invoice_line_ids.purchase_line_id.order_id`
- source relation
  - purchase order ของ vendor bill ใช้ `invoice_line_ids.mapped("purchase_line_id.order_id")`
  - purchase order ของ vendor credit note ใช้ source bill หรือ fallback ไปที่ invoice line ของ credit note
  - receipt ใช้ purchase orders แล้ว `mapped("picking_ids")`
  - payment ใช้ `_get_reconciled_payments()` และตัด `state = "cancel"`

### D) `res.partner`

- ฟิลด์
  - `smart_sale_order_ids`
  - `smart_sale_order_count`
  - `smart_delivery_ids`
  - `smart_delivery_count`
  - `smart_customer_invoice_ids`
  - `smart_customer_invoice_count`
  - `smart_customer_credit_note_ids`
  - `smart_customer_credit_note_count`
  - `smart_customer_payment_ids`
  - `smart_customer_payment_count`
  - `smart_purchase_order_ids`
  - `smart_purchase_order_count`
  - `smart_vendor_bill_ids`
  - `smart_vendor_bill_count`
  - `smart_payment_ids`
  - `smart_payment_count`
- helper
  - `_get_related_sale_orders()`
  - `_get_related_deliveries()`
  - `_get_related_customer_invoices()`
  - `_get_related_customer_credit_notes()`
  - `_get_related_customer_payments()`
  - `_get_related_purchase_orders()`
  - `_get_related_vendor_bills()`
  - `_get_related_payments()`
- action
  - `action_view_smart_sale_orders()`
  - `action_view_smart_deliveries()`
  - `action_view_smart_customer_invoices()`
  - `action_view_smart_customer_credit_notes()`
  - `action_view_smart_customer_payments()`
  - `action_view_smart_purchase_orders()`
  - `action_view_smart_vendor_bills()`
  - `action_view_smart_payments()`
- source relation
  - sale order ใช้ `search([("partner_id", "=", self.id)])`
  - deliveries ใช้ `sale_orders.mapped("picking_ids")` แล้วกรอง `picking_type_code == "outgoing"` และ `state != "cancel"`
  - customer payments ใช้ `_get_reconciled_payments()` จาก `customer invoices | customer credit notes` แล้วกรอง `state != "cancel"`
  - customer invoices ใช้ `search([("partner_id", "=", self.id), ("move_type", "=", "out_invoice"), ("state", "!=", "cancel")])`
  - customer credit notes ใช้ `search([("partner_id", "=", self.id), ("move_type", "=", "out_refund"), ("state", "!=", "cancel")])`
  - purchase order ใช้ `search([("partner_id", "=", self.id)])`
  - vendor bills ใช้ `search([("partner_id", "=", self.id), ("move_type", "=", "in_invoice"), ("state", "!=", "cancel")])`
  - payments ใช้ reconciled payments ของ vendor bills ที่หาได้
- หมายเหตุ
  - partner smart links ฝั่งขายแยก `Customer Invoices` ออกจาก `Customer Credit Notes` ตาม `move_type`
  - partner deliveries มาจาก sale-order chain เท่านั้น และไม่รวม pickings ที่ไม่ใช่ `outgoing`, pickings ที่ถูกยกเลิก หรือ return pickings
  - partner deliveries จึงยังรวม outgoing backorders / partial-delivery chain ที่เกี่ยวข้องอยู่
  - partner customer payments เป็น matched-only payments; unmatched payments จะไม่ถูกนับ
  - customer payment helper คืน recordset แบบ unique จึง dedupe payment ซ้ำอัตโนมัติ แม้ customer moves ซ้ำหรือ payment เดิม reconcile หลายใบ
  - partner smart links ไม่รวม `Vendor Credit Note` ในปุ่ม `Vendor Bills`
  - payment ฝั่งลูกหนี้จึงอิง customer move reconciliation chain ส่วน payment ฝั่งเจ้าหนี้ยังอิง vendor bill chain ของ partner เป็นหลัก

### E) `account.payment`

- ฟิลด์
  - `smart_bill_ids`
  - `smart_bill_count`
- helper
  - `_get_related_bills()`
- action
  - `action_view_smart_bills()`
- source relation
  - เริ่มจาก `move_id.line_ids`
  - กรองเฉพาะบัญชี `receivable` และ `payable`
  - ตาม `matched_debit_ids` และ `matched_credit_ids` ไปหา counterpart lines
  - map กลับเป็น `move_id`
- filter ของ bill
  - `state != "cancel"`
  - `move_type in ("in_invoice", "in_refund")`

## 8) พฤติกรรมของ action

- `purchase.order` ใช้ `_build_purchase_smart_action()`
- `stock.picking`, `account.move`, `account.payment`, `res.partner` ใช้ `_build_smart_action()`
- รูปแบบหลักของ action เหมือนกัน คือจำกัด `domain` ไว้ที่ record ที่เกี่ยวข้องจริง
- ถ้าไม่มี record ที่เกี่ยวข้อง
  - คืน `ir.actions.act_window`
  - `view_mode = "tree,form"`
  - `domain = []`
- ถ้ามี `1` record
  - เปิด `form`
  - ใส่ `res_id`
  - ยังคงจำกัด `domain` ไว้ที่ record เดิม
- ถ้ามีหลาย record
  - เปิด `tree,form`
  - จำกัด `domain` เป็น `[("id", "in", records.ids)]`

## 9) Smart Button labels จาก view จริง

- `purchase.order`
  - `Receipts`
  - `Vendor Bills`
  - `Payments`
  - `Vendor Credit Notes`
- `stock.picking`
  - `Purchase Orders`
  - `Vendor Bills`
  - `Payments`
  - `Accounting Documents`
- `account.move`
  - `Sale Orders`
  - `Deliveries`
  - `Adjustments`
  - `Purchase Orders`
  - `Receipts`
  - `Payments`
- `account.payment`
  - `Bills`
- `res.partner`
  - `Sale Orders`
  - `Deliveries`
  - `Customer Invoices`
  - `Customer Credit Notes`
  - `Customer Payments`
  - `Purchase Orders`
  - `Vendor Bills`
  - `Payments`

หมายเหตุ:

- ทุกปุ่มใช้ `attrs="{'invisible': [('..._count', '=', 0)]}"` เพื่อซ่อนเมื่อ count เป็น `0`
- `res.partner` ไม่มี branch พิเศษสำหรับกรณี `0` records ใน action builder แต่ใน view ปุ่มจะถูกซ่อนก่อนอยู่แล้ว

## 10) Notes เรื่อง performance แบบใช้งานจริง

- final code state ใช้ relation traversal เป็นหลัก เช่น `mapped()` และ `filtered()` บน recordset ที่เชื่อมอยู่แล้ว สำหรับ `purchase.order`, `stock.picking`, `account.move`, `account.payment`
- `stock.picking` ใช้ `purchase_id` ก่อน แล้วค่อย fallback ไปที่ stock move chain
- ไม่มีการ `search()` แบบกว้างข้ามทั้งโมเดลเพื่อสร้าง document smart links บน document models
- ข้อยกเว้นคือ `res.partner` ซึ่งใช้ `search()` แบบมี domain แคบที่ `partner_id = self.id` เพื่อหา `sale.order`, `purchase.order` และ `account.move` ตาม `move_type` ที่ต้องการ
- ภายใน `_compute_smart_partner_links()` มีการ reuse `sale_orders`, `customer_invoices` และ `customer_credit_notes` ที่หาได้แล้วในรอบ compute เดียว
- `res.partner -> Deliveries` ไม่ได้ `search()` ตรงบน `stock.picking`; โค้ดจะ reuse `sale_orders` ที่เพิ่งหาได้ แล้ว derive จาก sale-order chain โดยกรองเฉพาะ `outgoing` และ `state != "cancel"`
- `res.partner -> Customer Payments` ไม่ได้ `search()` ตรงบน `account.payment`; โค้ดจะรวม `customer_invoices | customer_credit_notes` แล้วส่งเข้า `_get_related_customer_payments(customer_moves)` เพื่อ reuse ชุด customer moves ก่อนดึงเฉพาะ reconciled payments
- `res.partner -> Payments` ไม่ได้ `search()` ตรงบน `account.payment`; โค้ดจะ derive จาก `_get_reconciled_payments()` ของ vendor bills ที่หาได้ แล้วกรอง `state != "cancel"`
- compute ทุกชุดเป็น non-stored field จึงไม่เพิ่มภาระ migration หรือการเก็บข้อมูลซ้ำในฐานข้อมูล
- trade-off คือการเปิด form จะคำนวณ count และ recordset ตาม relation ปัจจุบันทันที ทำให้ข้อมูลสด แต่เวลาตอบสนองจะโตตามจำนวน relation ของเอกสารหรือคู่ค้านั้น
- จุดที่ช่วยลดภาระในงานจริง
  - `stock.picking` ใช้ `purchase_id` ก่อน fallback
  - action จำกัด domain เฉพาะเอกสารที่เกี่ยวข้อง
  - กรอง `cancel` ออกตั้งแต่ชั้น helper
  - `res.partner` จำกัด scope การค้นหาด้วย `partner_id`
  - `res.partner` reuse customer/sales recordsets บางชุดใน compute เพื่อไม่ค้นซ้ำโดยไม่จำเป็น
  - `res.partner` derive `Deliveries` จาก sale-order chain, derive `Customer Payments` จาก customer-move reconciliation chain, และ derive `Payments` จาก vendor bill chain แทนการ query กว้างข้ามโมเดล

## 11) Regression coverage ที่มีอยู่

- `tests/test_purchase_document_smart_links.py`
  - ตรวจว่าฟิลด์และ helper ฝั่งซื้อถูกประกาศครบ
  - ตรวจ count และ relation ของ `PO`, `Receipt`, `Vendor Bill`, `Vendor Credit Note`, `Payment`
  - ตรวจ action กรณีมี record เดียวให้เปิด form และยังคุม domain
- `tests/test_document_smart_links.py`
  - ครอบคลุม smart links ฝั่งขายเดิม
- `tests/test_partner_document_smart_links.py`
  - ตรวจ field, helper, action builder และ form buttons ของ partner smart links
  - ตรวจ matched-only customer payments, การตัด unmatched payments, การ dedupe payment ids และ deliveries depth ที่ไม่รวม return pickings

## 12) Notes เรื่อง dependency

- ถ้าฐานทดสอบไม่มีผังบัญชี (Chart of Accounts)
  - เทสที่อิง `TestSaleCommon` อาจไม่รัน
- โมดูลนี้รองรับการมีหรือไม่มี `dtr_dncn`
  - ถ้าไม่มี โมดูลยังทำงานได้
  - แต่ฟีเจอร์ debit note แบบ fallback จะไม่ทำงาน

## Credits

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon - Project conception, implementation, and thorough review of all deliverables.

AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight.
