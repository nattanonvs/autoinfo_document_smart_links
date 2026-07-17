from lxml import etree

from odoo import fields
from odoo.addons.purchase_stock.tests.common import PurchaseTestCommon
from odoo.tests.common import Form
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPurchaseDocumentSmartLinks(PurchaseTestCommon):
    @classmethod
    def _ensure_purchase_journal(cls):
        journal = cls.env["account.journal"].search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", cls.env.company.id),
            ],
            limit=1,
        )
        if journal:
            return journal
        return cls.env["account.journal"].create(
            {
                "name": "Test Purchase Journal",
                "code": "TPJ1",
                "type": "purchase",
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _ensure_purchase_expense_account(cls):
        product_template = cls.product_1.product_tmpl_id.with_company(cls.env.company)
        expense_account = product_template.get_product_accounts()["expense"]
        if expense_account:
            return expense_account

        expense_account = cls.env["account.account"].search(
            [
                ("company_id", "=", cls.env.company.id),
                ("internal_group", "=", "expense"),
            ],
            limit=1,
        )
        if not expense_account:
            expense_account = cls.env["account.account"].create(
                {
                    "name": "Test Purchase Expense",
                    "code": "TPSL%s" % cls.env.company.id,
                    "user_type_id": cls.env.ref(
                        "account.data_account_type_expenses"
                    ).id,
                    "company_id": cls.env.company.id,
                }
            )

        product_category = cls.product_1.categ_id.with_company(cls.env.company)
        if not product_category.property_account_expense_categ_id:
            product_category.write(
                {"property_account_expense_categ_id": expense_account.id}
            )
        product_template.write({"property_account_expense_id": expense_account.id})
        return expense_account

    @classmethod
    def _post_move(cls, move):
        if move.state == "draft":
            move.invoice_date = move.invoice_date or fields.Date.today()
            move.action_post()
        return move

    @classmethod
    def _process_backorder(cls, validation_result):
        if isinstance(validation_result, dict) and validation_result.get(
            "res_model"
        ) == "stock.backorder.confirmation":
            backorder_wizard = Form(
                cls.env[validation_result["res_model"]].with_context(
                    validation_result["context"]
                )
            ).save()
            backorder_wizard.process()

    @classmethod
    def _validate_receipt(cls, receipt, quantity_done):
        receipt.move_lines.quantity_done = quantity_done
        validation_result = receipt.button_validate()
        cls._process_backorder(validation_result)
        return receipt

    @classmethod
    def _copy_vendor_bill(cls, source_bill):
        copied_bill = source_bill.copy({"invoice_date": fields.Date.today()})
        source_lines = source_bill.invoice_line_ids.filtered(lambda line: not line.display_type)
        copied_lines = copied_bill.invoice_line_ids.filtered(lambda line: not line.display_type)
        for copied_line, source_line in zip(copied_lines, source_lines):
            copied_line.purchase_line_id = source_line.purchase_line_id
        return cls._post_move(copied_bill)

    @classmethod
    def _create_vendor_credit_note(cls, bill):
        reversal = cls.env["account.move.reversal"].with_context(
            active_model="account.move",
            active_id=bill.id,
            active_ids=bill.ids,
        ).create(
            {
                "refund_method": "refund",
                "reason": "Purchase smart links vendor credit note regression test",
                "journal_id": bill.journal_id.id,
            }
        )
        action = reversal.reverse_moves()
        credit_note = cls.env["account.move"].browse(action["res_id"])
        source_lines = bill.invoice_line_ids.filtered(lambda line: not line.display_type)
        credit_lines = credit_note.invoice_line_ids.filtered(lambda line: not line.display_type)
        for credit_line, source_line in zip(credit_lines, source_lines):
            credit_line.purchase_line_id = source_line.purchase_line_id
        return cls._post_move(credit_note)

    @classmethod
    def _get_payments_from_action(cls, action):
        payment_model = cls.env["account.payment"]
        if action.get("res_id"):
            return payment_model.browse(action["res_id"])
        return payment_model.search(action.get("domain", []))

    @classmethod
    def _create_payment(cls, bills, amount=None):
        payment_register = cls.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=bills.ids,
        ).create({"payment_date": fields.Date.today()})
        if amount is not None:
            payment_register.write(
                {
                    "amount": amount,
                    "payment_difference_handling": "open",
                }
            )
        payment_action = payment_register.action_create_payments()
        return cls._get_payments_from_action(payment_action)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_journal = cls._ensure_purchase_journal()
        cls.purchase_expense_account = cls._ensure_purchase_expense_account()
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Vendor A", "supplier_rank": 1}
        )
        cls.po = cls.env["purchase.order"].create(
            {
                "partner_id": cls.vendor.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product_1.name,
                            "product_id": cls.product_1.id,
                            "product_qty": 10.0,
                            "product_uom": cls.product_1.uom_po_id.id,
                            "price_unit": 100.0,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        cls.po.button_confirm()
        cls.receipt = cls.po.picking_ids[:1]
        cls._validate_receipt(cls.receipt, 4.0)
        cls.second_receipt = (cls.po.picking_ids - cls.receipt)[:1]
        cls._validate_receipt(cls.second_receipt, 6.0)

        bill_action = cls.po.action_create_invoice()
        cls.bill = cls._post_move(cls.env["account.move"].browse(bill_action["res_id"]))
        cls.second_bill = cls._copy_vendor_bill(cls.bill)
        cls.partial_bill = cls._copy_vendor_bill(cls.bill)
        cls.vendor_credit_note = cls._create_vendor_credit_note(cls.bill)
        cls.grouped_payment = cls._create_payment(cls.bill | cls.second_bill)
        cls.partial_payment = cls._create_payment(
            cls.partial_bill,
            amount=cls.partial_bill.amount_total / 2.0,
        )

    def test_purchase_order_exposes_receipts_and_bills(self):
        self.assertIn("smart_receipt_ids", self.po._fields)
        self.assertIn("smart_vendor_bill_ids", self.po._fields)
        self.assertIn(self.receipt, self.po.smart_receipt_ids)
        self.assertIn(self.second_receipt, self.po.smart_receipt_ids)
        self.assertIn(self.bill, self.po.smart_vendor_bill_ids)
        self.assertIn(self.second_bill, self.po.smart_vendor_bill_ids)
        self.assertIn(self.partial_bill, self.po.smart_vendor_bill_ids)

    def test_receipt_exposes_purchase_order_and_bills(self):
        self.assertIn("smart_purchase_order_ids", self.receipt._fields)
        self.assertIn("smart_vendor_bill_ids", self.receipt._fields)
        self.assertIn(self.po, self.receipt.smart_purchase_order_ids)
        self.assertIn(self.bill, self.receipt.smart_vendor_bill_ids)
        self.assertIn(self.second_bill, self.receipt.smart_vendor_bill_ids)

    def test_receipt_exposes_payments_from_vendor_bill_chain(self):
        self.assertIn(
            "smart_payment_ids",
            self.receipt._fields,
            "stock.picking should expose smart_payment_ids for payments linked through related vendor bills.",
        )
        self.assertEqual(
            self.grouped_payment - self.receipt.smart_payment_ids,
            self.env["account.payment"],
            "receipt should include every grouped payment created from related vendor bills.",
        )
        self.assertIn(
            self.partial_payment,
            self.receipt.smart_payment_ids,
            "receipt should include partial payments created from related vendor bills.",
        )
        self.assertEqual(
            self.receipt.smart_payment_count,
            len(self.receipt.smart_payment_ids),
            "receipt smart payment count should match the payment recordset size.",
        )

    def test_vendor_bill_exposes_purchase_receipt_and_payment_links(self):
        self.assertIn("smart_purchase_order_ids", self.bill._fields)
        self.assertIn("smart_receipt_ids", self.bill._fields)
        self.assertIn("smart_payment_ids", self.bill._fields)
        self.assertIn(self.po, self.bill.smart_purchase_order_ids)
        self.assertIn(self.receipt, self.bill.smart_receipt_ids)
        self.assertIn(self.second_receipt, self.bill.smart_receipt_ids)

    def test_purchase_order_supports_multiple_receipts_and_bills(self):
        self.assertGreaterEqual(self.po.smart_receipt_count, 2)
        self.assertGreaterEqual(self.po.smart_vendor_bill_count, 3)
        self.assertEqual(
            self.po.smart_receipt_ids,
            self.receipt | self.second_receipt,
            "purchase.order should keep all related receipts in the smart link chain.",
        )
        self.assertEqual(
            self.po.smart_vendor_bill_ids,
            self.bill | self.second_bill | self.partial_bill,
            "purchase.order should keep all related vendor bills in the smart link chain.",
        )

    def test_purchase_order_exposes_payments_from_bill_chain(self):
        self.assertIn(
            "smart_payment_ids",
            self.po._fields,
            "purchase.order should expose smart_payment_ids for payments linked through vendor bills.",
        )
        self.assertEqual(
            self.grouped_payment - self.po.smart_payment_ids,
            self.env["account.payment"],
            "purchase.order should include every grouped payment created from related vendor bills.",
        )

    def test_purchase_order_exposes_vendor_credit_notes_from_bill_chain(self):
        self.assertIn(
            "smart_vendor_credit_note_ids",
            self.po._fields,
            "purchase.order should expose smart_vendor_credit_note_ids for related vendor credit notes.",
        )
        self.assertIn(
            self.vendor_credit_note,
            self.po.smart_vendor_credit_note_ids,
            "purchase.order should include vendor credit notes linked from the bill chain.",
        )

    def test_vendor_credit_note_exposes_purchase_links(self):
        self.assertEqual(self.vendor_credit_note.move_type, "in_refund")
        self.assertIn(
            "smart_purchase_order_ids",
            self.vendor_credit_note._fields,
            "vendor credit notes should expose smart_purchase_order_ids.",
        )
        self.assertIn(
            "smart_receipt_ids",
            self.vendor_credit_note._fields,
            "vendor credit notes should expose smart_receipt_ids.",
        )
        self.assertIn(
            self.po,
            self.vendor_credit_note.smart_purchase_order_ids,
            "vendor credit notes should link back to the originating purchase order.",
        )
        self.assertIn(
            self.receipt,
            self.vendor_credit_note.smart_receipt_ids,
            "vendor credit notes should link back to receipts from the originating purchase order.",
        )

    def test_payment_supports_multiple_bills(self):
        self.assertIn("smart_bill_ids", self.grouped_payment._fields)
        self.assertEqual(
            self.grouped_payment.smart_bill_ids,
            self.bill | self.second_bill,
            "grouped vendor payments should stay linked to every related bill.",
        )

    def test_partial_payment_exposes_bill_links(self):
        self.assertIn("smart_bill_ids", self.partial_payment._fields)
        self.assertTrue(
            self.partial_bill.amount_residual > 0,
            "the fixture must keep the vendor bill partially open after the payment.",
        )
        self.assertIn(
            self.partial_bill,
            self.partial_payment.smart_bill_ids,
            "partial vendor payments should still link back to the partially reconciled bill.",
        )

    def test_purchase_order_receipts_exclude_cancelled_pickings(self):
        cancelled_order = self.po.copy()
        cancelled_order.button_confirm()
        cancelled_receipt = cancelled_order.picking_ids[:1]
        cancelled_receipt.action_cancel()

        self.assertNotIn(cancelled_receipt, cancelled_order.smart_receipt_ids)
        self.assertEqual(
            cancelled_order.action_view_smart_vendor_bills()["domain"],
            [("id", "in", [])],
        )

    def test_purchase_order_form_view_exposes_all_purchase_smart_buttons(self):
        arch = self.env["purchase.order"].fields_view_get(view_type="form")["arch"]
        view = etree.fromstring(arch.encode())

        for button_name, count_field in (
            ("action_view_smart_receipts", "smart_receipt_count"),
            ("action_view_smart_vendor_bills", "smart_vendor_bill_count"),
            ("action_view_smart_payments", "smart_payment_count"),
            (
                "action_view_smart_vendor_credit_notes",
                "smart_vendor_credit_note_count",
            ),
        ):
            buttons = view.xpath("//button[@name='%s']" % button_name)
            self.assertTrue(
                buttons,
                "purchase.order form view should expose %s smart button." % button_name,
            )
            self.assertTrue(
                buttons[0].xpath(".//field[@name='%s']" % count_field),
                "purchase.order smart button %s should display %s."
                % (button_name, count_field),
            )

    def test_receipt_form_view_exposes_all_purchase_smart_buttons(self):
        arch = self.env["stock.picking"].fields_view_get(view_type="form")["arch"]
        view = etree.fromstring(arch.encode())

        for button_name, count_field in (
            ("action_view_smart_purchase_orders", "smart_purchase_order_count"),
            ("action_view_smart_vendor_bills", "smart_vendor_bill_count"),
            ("action_view_smart_payments", "smart_payment_count"),
            ("action_view_smart_account_moves", "smart_account_move_count"),
        ):
            buttons = view.xpath("//button[@name='%s']" % button_name)
            self.assertTrue(
                buttons,
                "stock.picking form view should expose %s smart button." % button_name,
            )
            self.assertTrue(
                buttons[0].xpath(".//field[@name='%s']" % count_field),
                "stock.picking smart button %s should display %s."
                % (button_name, count_field),
            )
