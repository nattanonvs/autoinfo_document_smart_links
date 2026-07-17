# คู่มือผู้ใช้ (User Guide)

## 1) โมดูลนี้คืออะไร

โมดูลนี้เพิ่ม Smart Button เพื่อให้ผู้ใช้เปิดเอกสารที่เกี่ยวข้องกันได้เร็วขึ้นจากหน้าเอกสารหลัก โดยไม่ต้องสลับเมนูไปค้นหาเอง ทั้งฝั่งขาย ฝั่งซื้อ ฝั่งจ่ายเงิน และหน้า Partner

## 2) ตอนนี้มีปุ่มอะไรบ้าง

### ฝั่งขาย

- `Sale Order`
  - `Credit Notes`
  - `Debit Notes`
- `Delivery`
  - `Accounting Documents`
- `Invoice`
  - `Sale Orders`
  - `Deliveries`
  - `Adjustments`

### ฝั่งซื้อ จ่ายเงิน และคู่ค้า

- `Purchase Order`
  - `Receipts`
  - `Vendor Bills`
  - `Payments`
  - `Vendor Credit Notes`
- `Receipt`
  - `Purchase Orders`
  - `Vendor Bills`
  - `Payments`
- `Vendor Bill` / `Vendor Credit Note`
  - `Purchase Orders`
  - `Receipts`
  - `Payments`
- `Payment`
  - `Bills`
- `Partner`
  - `Sale Orders`
  - `Deliveries`
  - `Customer Invoices`
  - `Customer Credit Notes`
  - `Customer Payments`
  - `Purchase Orders`
  - `Vendor Bills`
  - `Payments`

## 3) ต้องเตรียมอะไร ก่อนเริ่ม

- ต้องติดตั้งโมดูลนี้แล้ว
- ผู้ใช้ต้องมีสิทธิ์เปิดเอกสารปลายทาง
- ปุ่มจะขึ้นเฉพาะเมื่อมีเอกสารที่เกี่ยวข้องจริง

## 4) วิธีใช้งานแบบทีละขั้น

### A) ดู `Receipts`, `Vendor Bills`, `Payments` และ `Vendor Credit Notes` จาก `Purchase Order`

1. ไปที่เมนู `Purchase`
2. เปิด `Purchase Orders`
3. เลือกใบสั่งซื้อที่ต้องการ
4. ดูบริเวณ Smart Button ด้านบนของฟอร์ม
5. ถ้ามีเอกสารเกี่ยวข้อง จะเห็นปุ่ม
   - `Receipts`
   - `Vendor Bills`
   - `Payments`
   - `Vendor Credit Notes`
6. กดปุ่มที่ต้องการ
7. ระบบจะเปิดเอกสารที่เชื่อมกับ Purchase Order ใบนั้น

หมายเหตุ:

- ปุ่ม `Vendor Bills` ของ `Purchase Order` นับเฉพาะ `Vendor Bill` (`in_invoice`) ที่ยังไม่ถูกยกเลิก
- ปุ่ม `Vendor Credit Notes` แยกออกมาอีกปุ่มสำหรับ `in_refund`
- ปุ่ม `Payments` จะขึ้นเมื่อมี payment ที่ reconcile กับ vendor bill ของ PO แล้ว

### B) ดู `Purchase Orders`, `Vendor Bills` และ `Payments` จาก `Receipt`

1. ไปที่เมนู `Inventory`
2. เปิด `Operations`
3. เลือกเอกสารรับของ (`Receipt`)
4. ดูบริเวณ Smart Button
5. ถ้ามีเอกสารเชื่อมโยง จะเห็นปุ่ม
   - `Purchase Orders`
   - `Vendor Bills`
   - `Payments`
6. กดปุ่มเพื่อเปิดเอกสารต้นทางหรือเอกสารบัญชีที่เกี่ยวข้อง

หมายเหตุ:

- ถ้า Receipt ใบนั้นเชื่อมจาก Purchase Order ตาม flow ปกติ ระบบจะเปิดย้อนกลับไปยังใบสั่งซื้อได้
- ปุ่ม `Vendor Bills` ของ Receipt รวมทั้ง `Vendor Bill` และ `Vendor Credit Note` ที่ยังไม่ถูกยกเลิก
- ปุ่ม `Payments` ดึงจาก payment ที่ reconcile กับเอกสารบัญชีใน chain ของ receipt ใบนั้น

### C) ดู `Purchase Orders`, `Receipts` และ `Payments` จาก `Vendor Bill`

1. ไปที่เมนู `Accounting`
2. เปิด `Vendors`
3. เข้า `Bills`
4. เลือก Vendor Bill ที่ต้องการ
5. ดู Smart Button ด้านบน
6. ถ้ามีข้อมูลเชื่อมโยง จะเห็นปุ่ม
   - `Purchase Orders`
   - `Receipts`
   - `Payments`
7. กดปุ่มที่ต้องการเพื่อเปิดเอกสารที่เกี่ยวข้อง

หมายเหตุ:

- `Purchase Orders` และ `Receipts` อิงจาก `purchase_line_id` ของ invoice line
- ปุ่ม `Payments` จะแสดงเมื่อ bill นั้นถูกชำระและมีการ reconcile แล้ว
- payment ที่ถูกยกเลิกจะไม่ถูกนับ

### D) พฤติกรรมของ `Vendor Credit Note`

1. ไปที่เมนู `Accounting`
2. เปิด `Vendors`
3. เข้าเอกสารประเภท `Vendor Credit Note`
4. ดู Smart Button ด้านบน

สิ่งที่ควรรู้:

- `Vendor Credit Note` ยังสามารถมีปุ่ม `Purchase Orders` และ `Receipts` ได้
- ระบบจะพยายามย้อนจาก source vendor bill ผ่าน `reversed_entry_id` ก่อน
- ถ้าย้อนไม่ได้ จะ fallback ไปที่ `purchase_line_id` บน credit note เอง
- ปุ่ม `Payments` บน `Vendor Credit Note` จะไม่ขึ้นตาม behavior ปัจจุบันของโค้ด เพราะระบบคำนวณ payment links เฉพาะ `Vendor Bill`

### E) ดู `Bills` จาก `Payment`

1. ไปที่เมนู `Accounting`
2. เปิดหน้ารายการ `Payment`
3. ดู Smart Button `Bills`
4. กดปุ่มเพื่อเปิด bill ที่ payment ใบนั้นไปตัดชำระ

หมายเหตุ:

- ปุ่มนี้อิงจากข้อมูล reconciliation จริง
- ถ้า payment ยังไม่ได้ตัดกับ bill ระบบจะยังไม่เห็นรายการในปุ่มนี้
- ปุ่ม `Bills` สามารถเชื่อมได้ทั้ง `Vendor Bill` และ `Vendor Credit Note` ที่ยังไม่ถูกยกเลิก

### F) ดู `Sale Orders`, `Deliveries`, `Customer Invoices`, `Customer Credit Notes` และ `Customer Payments` จาก `Partner`

1. เปิดหน้า `Contacts`
2. เข้า Partner ที่เป็นลูกค้า
3. ดู Smart Button ด้านบน
4. ถ้ามีข้อมูล จะเห็นปุ่ม
   - `Sale Orders`
   - `Deliveries`
   - `Customer Invoices`
   - `Customer Credit Notes`
   - `Customer Payments`
5. กดปุ่มที่ต้องการเพื่อเปิดรายการที่เกี่ยวข้อง

หมายเหตุ:

- ปุ่ม `Sale Orders` หาเอกสารจาก `sale.order` ด้วย `partner_id`
- ปุ่ม `Deliveries` ไม่ได้ดึง picking ทั้งหมดของ partner โดยตรง แต่จะย้อนจาก sale orders ของ partner ก่อน
- `Deliveries` จะนับเฉพาะ picking ใน sale-order chain ที่เป็น `outgoing` และ `state != cancel`
- ถ้ามี partial delivery หรือ backorder ที่ยังเป็น outgoing อยู่ ระบบจะรวมอยู่ใน `Deliveries`
- return pickings จะไม่ถูกนับ แม้อยู่ใน sale-order chain เดียวกัน
- ปุ่ม `Customer Invoices` นับเฉพาะ `account.move` ที่ `move_type = out_invoice` และ `state != cancel`
- ปุ่ม `Customer Credit Notes` แยกอีกปุ่มสำหรับ `move_type = out_refund` และ `state != cancel`
- ปุ่ม `Customer Payments` นับเฉพาะ payment ของลูกค้าที่ถูกจับคู่ reconciliation กับ `Customer Invoices` หรือ `Customer Credit Notes` ของ partner แล้ว
- payment ลูกค้าที่สร้างไว้แต่ยัง unmatched จะไม่ขึ้นในปุ่ม `Customer Payments`
- ถ้า payment เดิมไปเชื่อมกับ customer moves หลายใบ ระบบจะแสดงเป็นรายการเดียว ไม่ซ้ำ
- ถ้า partner มีแค่ credit note อย่างเดียว ปุ่ม `Customer Invoices` จะไม่ขึ้น เพราะระบบแยก invoices กับ credit notes คนละปุ่ม

### G) ดู `Purchase Orders`, `Vendor Bills` และ `Payments` จาก `Partner`

1. เปิดหน้า `Contacts`
2. เข้า Partner ที่เป็น vendor
3. ดู Smart Button ด้านบน
4. ถ้ามีข้อมูล จะเห็นปุ่ม
   - `Purchase Orders`
   - `Vendor Bills`
   - `Payments`
5. กดปุ่มที่ต้องการเพื่อเปิดรายการที่เกี่ยวข้อง

หมายเหตุ:

- ปุ่ม `Purchase Orders` หาเอกสารจาก `partner_id` ของ PO
- ปุ่ม `Vendor Bills` นับเฉพาะ `Vendor Bill` (`in_invoice`) ที่ยังไม่ถูกยกเลิก
- ปุ่ม `Payments` ดึงจาก payment ที่ reconcile กับ vendor bills ของ partner
- ถ้า partner มีแต่ `Vendor Credit Note` อย่างเดียว ปุ่ม `Vendor Bills` และ `Payments` อาจไม่ขึ้นตาม logic ปัจจุบัน

### H) พฤติกรรมเวลาเปิดจาก Smart Button

- ถ้ามีเอกสารที่เกี่ยวข้อง `1` ใบ ระบบจะเปิดหน้า form ของใบนั้นทันที
- ถ้ามีหลายใบ ระบบจะเปิดเป็นรายการให้เลือก
- ถ้า count เป็น `0` ปุ่มจะไม่แสดง

## 5) ตัวอย่างการใช้งานจริง

### ตัวอย่างที่ 1: ซื้อสินค้าแบบ flow ปกติ

1. สร้าง `Purchase Order`
2. ยืนยันใบสั่งซื้อ
3. รับของจนเกิด `Receipt`
4. สร้าง `Vendor Bill`

ผลที่ควรเห็น:

- บน `Purchase Order` มีปุ่ม `Receipts` และ `Vendor Bills`
- บน `Receipt` มีปุ่ม `Purchase Orders` และ `Vendor Bills`
- บน `Vendor Bill` มีปุ่ม `Purchase Orders` และ `Receipts`

### ตัวอย่างที่ 2: จ่ายชำระ Vendor Bill แล้ว

1. เปิด `Vendor Bill`
2. ลงทะเบียนชำระเงิน
3. ให้ระบบสร้าง `Payment` และ reconcile สำเร็จ

ผลที่ควรเห็น:

- บน `Purchase Order` มีปุ่ม `Payments`
- บน `Receipt` มีปุ่ม `Payments`
- บน `Vendor Bill` มีปุ่ม `Payments`
- บน `Payment` มีปุ่ม `Bills`

### ตัวอย่างที่ 3: ออก `Vendor Credit Note`

1. เปิด `Vendor Bill` ต้นทาง
2. สร้าง `Vendor Credit Note`
3. เปิดเอกสาร credit note ที่สร้างขึ้น

ผลที่ควรเห็น:

- บน `Purchase Order` มีปุ่ม `Vendor Credit Notes`
- บน `Vendor Credit Note` อาจมีปุ่ม `Purchase Orders` และ `Receipts`
- บน `Vendor Credit Note` จะไม่เห็นปุ่ม `Payments` ถ้า count เป็น `0`

### ตัวอย่างที่ 4: เปิดจากหน้า `Partner`

1. เปิด Contact ของ customer
2. ตรวจ smart buttons ด้านบน

ผลที่ควรเห็น:

- มีปุ่ม `Sale Orders` ถ้า partner มี sale order
- มีปุ่ม `Deliveries` เฉพาะ picking ที่มาจาก sale-order chain, เป็น `outgoing` และไม่ถูกยกเลิก
- partial deliveries / outgoing backorders ยังถูกนับ แต่ return pickings จะไม่ถูกนับ
- มีปุ่ม `Customer Invoices` เฉพาะ customer invoices ที่ยังไม่ถูกยกเลิก
- มีปุ่ม `Customer Credit Notes` เฉพาะ customer credit notes ที่ยังไม่ถูกยกเลิก
- มีปุ่ม `Customer Payments` เฉพาะ matched customer payments ที่ reconcile กับ invoices / credit notes แล้ว

### ตัวอย่างที่ 5: เปิดจากหน้า `Partner` ฝั่ง vendor

1. เปิด Contact ของ vendor
2. ตรวจ smart buttons ด้านบน

ผลที่ควรเห็น:

- มีปุ่ม `Purchase Orders` ถ้า partner มี PO
- มีปุ่ม `Vendor Bills` ถ้า partner มี vendor bill ที่ยังไม่ถูกยกเลิก
- มีปุ่ม `Payments` ถ้ามี payment ที่ reconcile กับ vendor bills ของ partner

## 6) เรื่องที่ต้องระวัง

- ปุ่มจะไม่ขึ้น ถ้าจำนวนเป็น `0`
- ถ้ากดแล้วเปิดไม่ได้ มักเป็นเรื่องสิทธิ์ของผู้ใช้
- `Vendor Bill` กับ `Vendor Credit Note` ไม่ได้มีพฤติกรรมเหมือนกันทุกปุ่ม
- `Customer Invoice` กับ `Customer Credit Note` ก็ไม่ได้ถูกรวมปุ่มเดียวกัน ระบบแยกตาม `move_type`
- `Customer Payments` บน `Partner` แสดงเฉพาะ payment ที่ matched แล้วเท่านั้น
- payment ลูกค้าที่ unmatched จะไม่ถูกนับในปุ่ม `Customer Payments`
- payment เดิมจะไม่แสดงซ้ำแม้ reconcile กับ customer moves หลายใบ
- ปุ่ม `Payments` และ `Bills` อาศัยการ reconcile ถ้ายังไม่ reconcile ปุ่มอาจไม่ขึ้น
- ปุ่ม `Deliveries` ฝั่ง `Partner` จะไม่รวม picking ที่ไม่ใช่ `outgoing` หรือถูก `cancel`
- ปุ่ม `Deliveries` ฝั่ง `Partner` ก็จะไม่รวม return pickings เช่นกัน
- ปุ่มฝั่ง `Partner` ไม่ได้รวม `Vendor Credit Note` ใน `Vendor Bills`

## 7) หมายเหตุเรื่อง performance guard ตามของจริง

- ปุ่มส่วนใหญ่ฝั่ง `Purchase Order`, `Receipt`, `Vendor Bill / Credit Note` และ `Payment` อาศัย relation ที่มีอยู่แล้วในเอกสาร
- เมื่อกดปุ่ม ระบบจะเปิดเฉพาะเอกสารที่เชื่อมกับใบปัจจุบัน ไม่ได้เปิดรายการกว้างทั้งระบบ
- `Receipt` จะใช้ `purchase_id` ก่อน แล้วค่อย fallback ไปที่ stock move
- ฟิลด์เหล่านี้เป็น compute field แบบไม่เก็บลงฐานข้อมูล จึงคำนวณใหม่เมื่อเปิดฟอร์ม
- สำหรับหน้า `Partner` โค้ดจะค้น `Sale Orders`, `Purchase Orders`, `Customer Invoices`, `Customer Credit Notes` และ `Vendor Bills` แบบระบุ `partner_id` ให้ตรงกับคู่ค้าปัจจุบัน
- ระหว่าง compute หน้า `Partner` โค้ดจะ reuse ชุด `sale orders`, `customer invoices` และ `customer credit notes` ที่หาได้แล้วในรอบเดียวกัน
- `Deliveries` ของ partner จะ derive จาก sale orders ที่หาได้ ไม่ได้ค้น picking ทั้งระบบโดยตรง
- `Customer Payments` ของ partner จะ derive จาก customer invoices + credit notes ที่ compute รวมไว้ แล้วดึงเฉพาะ reconciled payments
- `Payments` ของ partner จะ derive จาก payment ที่ reconcile กับ vendor bills ของ partner เท่านั้น
- ถ้าเอกสารหรือ partner หนึ่งรายเชื่อมกับ sale orders, deliveries, invoices, PO, bills หรือ payments จำนวนมากผิดปกติ หน้าเอกสารอาจใช้เวลาคำนวณเพิ่มขึ้นบ้าง

## 8) ถ้าเกิดปัญหา

ดูไฟล์ `docs/troubleshooting.md`

## 9) สรุปสั้น ๆ

โมดูลนี้ช่วยให้ผู้ใช้ไล่เส้นทางเอกสารจาก `PO -> Receipt -> Vendor Bill -> Payment`, ตามรอย `Vendor Credit Note`, เปิดเอกสารจากหน้า `Partner` ได้ทั้งฝั่งขายและฝั่งซื้อ, แยก `Customer Invoices` ออกจาก `Customer Credit Notes`, และดู `Customer Payments` แบบ matched-only ตามพฤติกรรมจริงของโค้ด
