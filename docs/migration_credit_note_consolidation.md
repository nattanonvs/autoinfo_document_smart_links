# Migration Guide: Credit Note Consolidation

## วัตถุประสงค์

เอกสารนี้ใช้สำหรับย้ายการดูแลปุ่ม `Credit Notes` บน `sale.order` จากโมดูล `autoinfo_sale_credit_note_button` ไปยังโมดูล `autoinfo_document_smart_links` เพื่อให้เหลือโมดูลศูนย์กลางเพียงตัวเดียวสำหรับ Smart Links ของเอกสารที่เกี่ยวข้อง

## ขอบเขตของการเปลี่ยนแปลง

- `autoinfo_document_smart_links` จะเป็นผู้ดูแลปุ่ม `Credit Notes` และ `Debit Notes` บน `sale.order`
- `autoinfo_sale_credit_note_button` จะถูกถอนการติดตั้งหลังจากตรวจสอบว่า UI ใหม่ทำงานถูกต้องแล้ว
- ลำดับงานต้องเป็นแบบ upgrade โมดูลใหม่ก่อน แล้วจึงถอนโมดูลเก่า เพื่อหลีกเลี่ยงความเสี่ยงที่ปุ่ม `Credit Notes` จะหายหรือแสดงซ้ำ

## สิ่งที่ต้องเตรียม

- สิทธิ์ผู้ดูแลระบบ Odoo
- สิทธิ์เข้าถึง PostgreSQL สำหรับสำรองฐานข้อมูล
- โค้ดเวอร์ชันล่าสุดของทั้ง `autoinfo_document_smart_links` และ `autoinfo_sale_credit_note_button` อยู่ใน addons path เดียวกัน
- ควรหยุดงาน deploy อื่นชั่วคราวระหว่าง migration เพื่อลดความเสี่ยงจากการเปลี่ยนแปลงพร้อมกัน

## ขั้นตอนที่ 1: Backup ฐานข้อมูล

สำรองฐานข้อมูลก่อนทุกครั้ง โดยแนะนำให้ใช้ `pg_dump`

```bash
pg_dump -Fc -f /var/odoo/backup/<database_name>_before_credit_note_consolidation.dump <database_name>
```

ถ้าต้องการสำรองโค้ดเพิ่มเติม ให้สำรองโฟลเดอร์ custom addons ที่เกี่ยวข้องด้วย

- `/var/odoo/custom15_autoinfo/autoinfo_document_smart_links`
- `/var/odoo/custom15_autoinfo/autoinfo_sale_credit_note_button`

## ขั้นตอนที่ 2: Deploy โค้ดใหม่

นำโค้ดล่าสุดขึ้นเครื่องปลายทางให้เรียบร้อยก่อน upgrade โดยตรวจสอบว่าโมดูลใหม่อยู่ใน addons path ที่ Odoo ใช้งานจริง เช่น

- `/var/odoo/custom15_autoinfo/autoinfo_document_smart_links`
- `/var/odoo/custom15_autoinfo/autoinfo_sale_credit_note_button`

หมายเหตุ:

- ห้ามถอน `autoinfo_sale_credit_note_button` ก่อน upgrade โมดูลใหม่
- หากทั้งสองโมดูลยัง active พร้อมกันในช่วงรอยต่อ อาจเกิดปุ่ม `Credit Notes` ซ้ำได้ชั่วคราว ดังนั้นต้องรีบทำขั้นตอนตรวจสอบและถอนโมดูลเก่าต่อทันที

## ขั้นตอนที่ 3: Upgrade โมดูลใหม่

Upgrade เฉพาะ `autoinfo_document_smart_links` ก่อน เพื่อให้ logic ของ `Credit Notes` และ `Debit Notes` พร้อมใช้งานในโมดูลใหม่

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf \
  -d <database_name> \
  -u autoinfo_document_smart_links \
  --stop-after-init
```

หลัง upgrade เสร็จ ให้ restart service ของ Odoo ตามวิธีที่ใช้งานใน environment นั้น

## ขั้นตอนที่ 4: ตรวจ UI ของ Credit Notes และ Debit Notes

ก่อนถอนโมดูลเก่า ให้ตรวจสอบที่หน้า `Sales > Orders > Quotations / Sales Orders` แล้วเปิด Sale Order ที่มีข้อมูลเกี่ยวข้อง

ตรวจสอบรายการต่อไปนี้

- ปุ่ม `Credit Notes` แสดงผลบน `sale.order`
- ปุ่ม `Debit Notes` แสดงผลบน `sale.order`
- จำนวนในปุ่ม `Credit Notes` ตรงกับเอกสารประเภท `out_refund` ที่อยู่ในสถานะ `posted`
- จำนวนในปุ่ม `Debit Notes` ยังแสดงผลตาม logic ที่ระบบอนุมัติไว้
- เมื่อกดปุ่มแล้วเปิดเอกสารที่เกี่ยวข้องได้ถูกต้อง
- ไม่มีพฤติกรรมผิดปกติกับปุ่มมาตรฐานอื่น เช่น `Invoices` หรือปุ่มเอกสารที่เกี่ยวข้องตัวอื่น

จุดที่ต้องระวัง

- ถ้ายังเห็นปุ่ม `Credit Notes` ซ้ำมากกว่า 1 ปุ่ม แปลว่ายังไม่ควรถอนโมดูลเก่าจนกว่าจะยืนยันว่าโมดูลใหม่ทำงานครบและเข้าใจแหล่งที่มาของปุ่มแต่ละตัว
- ถ้าไม่เห็นปุ่ม `Credit Notes` หรือ `Debit Notes` ทั้งที่ควรมีข้อมูล ให้หยุด migration และ rollback จาก backup หากจำเป็น

## ขั้นตอนที่ 5: ถอนโมดูลเก่าผ่าน Odoo Shell

เมื่อยืนยันแล้วว่า `autoinfo_document_smart_links` ทำงานถูกต้อง ให้ถอน `autoinfo_sale_credit_note_button` ผ่าน Odoo Shell โดยใช้ `button_immediate_uninstall()`

เปิด Odoo Shell

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  shell \
  -c /etc/odoo/odoo.conf \
  -d <database_name>
```

จากนั้นรันคำสั่งต่อไปนี้ใน Odoo Shell

```python
module = env["ir.module.module"].search(
    [("name", "=", "autoinfo_sale_credit_note_button")],
    limit=1,
)
if module and module.state == "installed":
    module.button_immediate_uninstall()
```

หลังถอนโมดูลเก่าแล้ว ให้ออกจาก Shell และ restart Odoo service อีกครั้งถ้า environment ของคุณต้องการ

## ขั้นตอนที่ 6: ตรวจ UI ซ้ำหลังถอนโมดูลเก่า

กลับไปตรวจที่หน้า `sale.order` อีกครั้ง

- ต้องเหลือปุ่ม `Credit Notes` จาก `autoinfo_document_smart_links` เพียงชุดเดียว
- ปุ่ม `Debit Notes` ยังต้องใช้งานได้ตามปกติ
- การเปิดดูรายการ `Credit Notes` และ `Debit Notes` ต้องยังถูกต้อง
- ต้องไม่เกิด error จาก view inheritance หรือ action ของโมดูลเดิม

## Validation Checklist

ใช้ checklist นี้สำหรับ sign-off หลัง migration

- สำรองฐานข้อมูลเรียบร้อยก่อนเริ่มงาน
- Deploy โค้ดเวอร์ชันล่าสุดของโมดูลใหม่เรียบร้อย
- Upgrade `autoinfo_document_smart_links` สำเร็จโดยไม่มี error
- หน้า `sale.order` แสดง `Credit Notes` ถูกต้อง
- หน้า `sale.order` แสดง `Debit Notes` ถูกต้อง
- จำนวน `Credit Notes` ตรงกับเอกสาร `out_refund` ที่ `posted`
- การกดปุ่ม `Credit Notes` เปิดเอกสารที่เกี่ยวข้องได้ถูกต้อง
- การกดปุ่ม `Debit Notes` เปิดเอกสารที่เกี่ยวข้องได้ถูกต้อง
- ไม่พบปุ่ม `Credit Notes` ซ้ำบน `sale.order`
- ปุ่มมาตรฐานอื่น เช่น `Invoices` และส่วนของ document links อื่นยังทำงานปกติ
- ถอน `autoinfo_sale_credit_note_button` สำเร็จผ่าน Odoo Shell
- ตรวจสอบหลังถอนโมดูลเก่าแล้วไม่พบ error ใน UI

## Rollback เบื้องต้น

ถ้าระหว่าง migration พบปัญหารุนแรง เช่น ปุ่มหาย, ปุ่มซ้ำ, หรือเปิดเอกสารไม่ได้ ให้ใช้แนวทางดังนี้

1. หยุดการเปลี่ยนแปลงเพิ่มเติม
2. กู้คืนฐานข้อมูลจาก backup ที่สร้างไว้ก่อนเริ่มงาน
3. คืนโค้ดกลับไปยังเวอร์ชันก่อน migration
4. ตรวจสอบสาเหตุให้ชัดเจนก่อนเริ่ม rollout ใหม่
