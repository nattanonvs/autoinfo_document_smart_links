# Release Note 15.0.1.2.4

วันที่: 2026-07-17

## สรุปสั้น

รุ่นนี้แก้ปัญหาฝั่ง Purchase เป็นหลัก

- ตัด smart button `Receipts` ที่ขึ้นซ้ำในหน้า `Purchase Order`
- ตัด smart button `Vendor Bills` ที่ขึ้นซ้ำในหน้า `Purchase Order`
- คงปุ่มมาตรฐานของ Odoo เอาไว้
- เพิ่ม test กันปุ่มซ้ำในอนาคต
- ปรับ purchase test fixture ให้รันผ่านบน clean DB ได้จริง

## ปัญหาที่แก้

ก่อนหน้านี้หน้า `Purchase Order` อาจเห็นปุ่ม `Receipts` และ `Vendor Bills` ซ้ำอย่างละ 2 ปุ่ม

สาเหตุคือ

- Odoo เดิมมีปุ่มมาตรฐานอยู่แล้ว
- โมดูล `autoinfo_document_smart_links` เพิ่มปุ่มชื่อใกล้กันเข้าไปอีกชุด

ผลคือ

- หน้าจอดูซ้ำ
- ผู้ใช้สับสน
- ตัวเลขนับอาจยังถูก แต่ UX ไม่ดี

## การเปลี่ยนแปลง

ในรุ่น `15.0.1.2.4`

- เอาปุ่มซ้ำของโมดูลออกจากหน้า `Purchase Order`
- เหลือเฉพาะปุ่มที่โมดูลนี้ควรเพิ่มจริง
- เพิ่ม test ตรวจว่า form view ของ `purchase.order` ไม่ inject ปุ่มซ้ำ
- เติมข้อมูลบัญชีขั้นต่ำใน test เพื่อให้สร้าง `Vendor Bill` และ `Payment` ได้ในฐานทดสอบใหม่

## ผลลัพธ์หลังอัปเดต

- หน้า `Purchase Order` เห็น `Receipt` ชุดเดียว
- หน้า `Purchase Order` เห็น `Vendor Bills` ชุดเดียว
- ปุ่ม `Payments` และ `Vendor Credit Notes` ของโมดูลยังใช้งานได้
- purchase test suite ผ่านบน clean DB

## การทดสอบที่ผ่าน

- regression test สำหรับปุ่มซ้ำบน `purchase.order`
- full purchase suite ของ `autoinfo_document_smart_links`

ผลทดสอบ

- `0 failed, 0 error(s) of 1 tests`
- `0 failed, 0 error(s) of 13 tests`

## คำแนะนำตอนอัปเดต

1. อัปเกรดโมดูล `autoinfo_document_smart_links`
2. ล้าง cache หน้าเว็บ
3. เปิดหน้า `Purchase Order`
4. ตรวจว่าปุ่ม `Receipt` และ `Vendor Bills` ไม่ซ้ำ

ตัวอย่างคำสั่ง

```bash
python odoo-bin -c odoo.conf -d <db_name> -u autoinfo_document_smart_links --stop-after-init
```

## เครดิต

Development Team: The Auto-Info Co., Ltd. : Dev Team / Mr. Nattanon Vinyangkoon - Project conception, implementation, and thorough review of all deliverables.

AI Coding Assistant: TRAE SOLO / MICROSOFT 365 COPILOT - Utilized to support code generation and productivity improvements under human oversight.
