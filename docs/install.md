<span style="color:red">สำคัญมาก: ก่อนติดตั้งทุกครั้งให้สำรองฐานข้อมูล (backup) และทดสอบบนฐานทดสอบ (staging) ก่อน ถ้าติดตั้งผิดระบบอาจเปิดไม่ขึ้น หรือ user เข้าเมนูแล้วค้างได้</span>

# วิธีติดตั้ง (Installation)

## 1) วางโฟลเดอร์ให้ถูกที่

บนเครื่อง Linux ให้ใช้โฟลเดอร์นี้:

- `/var/odoo/custom15_autoinfo`

## 2) ดาวน์โหลดโค้ดด้วย Git

ถ้าติดตั้งเป็น “ชุดโมดูล link” ให้ clone ตามนี้:

```bash
cd /var/odoo/custom15_autoinfo
git clone https://github.com/nattanonvs/autoinfo_data_link_base.git
git clone https://github.com/nattanonvs/autoinfo_data_link_account.git
git clone https://github.com/nattanonvs/autoinfo_data_link_sale.git
git clone https://github.com/nattanonvs/autoinfo_data_link_purchase.git
git clone https://github.com/nattanonvs/autoinfo_data_link_project.git
git clone https://github.com/nattanonvs/autoinfo_data_link_diagnostics.git
git clone https://github.com/nattanonvs/autoinfo_document_smart_links.git
```

## 3) ตรวจ addons_path

ในไฟล์ config ของ Odoo (`odoo.conf`) ให้มี path นี้อยู่ใน `addons_path`:

- `/var/odoo/custom15_autoinfo`

## 4) ติดตั้งโมดูล

แนะนำติดตั้งตามลำดับ:

1. `autoinfo_data_link_base`
2. `autoinfo_data_link_account`
3. `autoinfo_data_link_sale`
4. `autoinfo_data_link_purchase`
5. `autoinfo_data_link_project`
6. `autoinfo_data_link_diagnostics` (ถ้าต้องการ)
7. `autoinfo_document_smart_links` (ถ้าต้องการปุ่ม smart links)

ตัวอย่างคำสั่ง:

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf \
  -d <database_name> \
  -i autoinfo_document_smart_links \
  --stop-after-init
```

## 5) อัปเดตโมดูล (ถ้าแก้โค้ดแล้ว)

```bash
/var/odoo/venv/bin/python /var/odoo/odoo-bin \
  -c /etc/odoo/odoo.conf \
  -d <database_name> \
  -u autoinfo_document_smart_links \
  --stop-after-init
```
