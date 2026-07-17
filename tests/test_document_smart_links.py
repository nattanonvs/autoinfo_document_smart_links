from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestDocumentSmartLinks(TestSaleCommon):
    @classmethod
    def _create_sale_order_with_posted_invoice(cls):
        sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "partner_invoice_id": cls.partner_a.id,
                "partner_shipping_id": cls.partner_a.id,
                "pricelist_id": cls.company_data["default_pricelist"].id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.company_data["product_order_no"].name,
                            "product_id": cls.company_data["product_order_no"].id,
                            "product_uom_qty": 1.0,
                            "product_uom": cls.company_data["product_order_no"].uom_id.id,
                            "price_unit": cls.company_data["product_order_no"].list_price,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        invoice = sale_order._create_invoices()
        invoice.action_post()
        return sale_order, invoice

    @classmethod
    def _create_credit_note(cls, invoice):
        reversal = cls.env["account.move.reversal"].with_context(
            active_model="account.move",
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create(
            {
                "refund_method": "refund",
                "reason": "Document smart links relation regression test",
                "journal_id": invoice.journal_id.id,
            }
        )
        action = reversal.reverse_moves()
        credit_note = cls.env["account.move"].browse(action["res_id"])
        if credit_note.state != "posted":
            credit_note.action_post()
        return credit_note

    @classmethod
    def _duplicate_credit_note(cls, credit_note, state="draft"):
        duplicated_credit_note = credit_note.copy()
        for duplicated_line, original_line in zip(
            duplicated_credit_note.invoice_line_ids, credit_note.invoice_line_ids
        ):
            duplicated_line.sale_line_ids = [(6, 0, original_line.sale_line_ids.ids)]
        if state == "cancel":
            duplicated_credit_note.button_cancel()
        return duplicated_credit_note

    @classmethod
    def _has_dtr_dncn_fields(cls):
        move_model = cls.env["account.move"]
        required_fields = {"dncn", "parent_id", "child_ids"}
        return required_fields.issubset(move_model._fields)

    @classmethod
    def _create_debit_note_with_parent_relation_only(cls, invoice):
        source_line = invoice.invoice_line_ids.filtered(lambda line: not line.display_type)[:1]
        debit_note = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": invoice.partner_id.id,
                "journal_id": invoice.journal_id.id,
                "invoice_date": invoice.invoice_date,
                "invoice_origin": False,
                "dncn": "dn",
                "parent_id": invoice.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "%s debit note" % source_line.name,
                            "product_id": source_line.product_id.id,
                            "quantity": 1.0,
                            "product_uom_id": source_line.product_uom_id.id,
                            "price_unit": source_line.price_unit or 1.0,
                            "account_id": source_line.account_id.id,
                            "tax_ids": [(6, 0, source_line.tax_ids.ids)],
                        },
                    )
                ],
            }
        )
        debit_note.action_post()
        return debit_note

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order, cls.invoice = cls._create_sale_order_with_posted_invoice()
        cls.picking = cls.sale_order.picking_ids[:1]
        cls.credit_note = cls._create_credit_note(cls.invoice)
        cls.draft_credit_note = cls._duplicate_credit_note(cls.credit_note, state="draft")
        cls.cancelled_credit_note = cls._duplicate_credit_note(cls.credit_note, state="cancel")
        cls.has_dtr_dncn_fields = cls._has_dtr_dncn_fields()
        cls.debit_note = cls.env["account.move"]
        if cls.has_dtr_dncn_fields:
            cls.debit_note = cls._create_debit_note_with_parent_relation_only(cls.invoice)
        (
            cls.sale_order_without_debit_note,
            cls.invoice_without_debit_note,
        ) = cls._create_sale_order_with_posted_invoice()
        (
            cls.sale_order_without_posted_credit_note,
            cls.invoice_without_posted_credit_note,
        ) = cls._create_sale_order_with_posted_invoice()
        cls.only_draft_or_cancel_credit_note = cls._create_credit_note(
            cls.invoice_without_posted_credit_note
        )
        cls.draft_only_credit_note = cls._duplicate_credit_note(
            cls.only_draft_or_cancel_credit_note, state="draft"
        )
        cls.only_draft_or_cancel_credit_note.button_draft()
        cls.cancelled_only_credit_note = cls.only_draft_or_cancel_credit_note
        cls.cancelled_only_credit_note.button_cancel()

    def _skip_if_missing_dtr_dncn_fields(self):
        if not self.has_dtr_dncn_fields:
            self.skipTest("dtr_dncn fields are not available in this database")

    def test_account_move_exposes_sale_order_links(self):
        self.assertIn(
            "smart_sale_order_ids",
            self.invoice._fields,
            "account.move should expose smart_sale_order_ids for the Sale Orders smart link.",
        )
        self.assertIn(
            "smart_sale_order_count",
            self.invoice._fields,
            "account.move should expose smart_sale_order_count for the Sale Orders smart link.",
        )
        self.assertEqual(self.invoice.smart_sale_order_ids, self.sale_order)
        self.assertEqual(self.invoice.smart_sale_order_count, 1)

    def test_account_move_related_sale_order_helper_exists(self):
        self.assertTrue(
            hasattr(self.invoice, "_get_related_sale_orders"),
            "account.move should expose _get_related_sale_orders() for relation-based smart links.",
        )
        self.assertEqual(self.invoice._get_related_sale_orders(), self.sale_order)

    def test_account_move_exposes_delivery_links(self):
        self.assertIn(
            "smart_delivery_ids",
            self.invoice._fields,
            "account.move should expose smart_delivery_ids for the Deliveries smart link.",
        )
        self.assertIn(
            "smart_delivery_count",
            self.invoice._fields,
            "account.move should expose smart_delivery_count for the Deliveries smart link.",
        )
        self.assertEqual(self.invoice.smart_delivery_count, len(self.sale_order.picking_ids))
        self.assertIn(self.picking, self.invoice.smart_delivery_ids)

    def test_account_move_related_delivery_helper_exists(self):
        self.assertTrue(
            hasattr(self.invoice, "_get_related_deliveries"),
            "account.move should expose _get_related_deliveries() for relation-based smart links.",
        )
        self.assertIn(self.picking, self.invoice._get_related_deliveries())

    def test_stock_picking_exposes_accounting_links(self):
        self.assertIn(
            "smart_account_move_ids",
            self.picking._fields,
            "stock.picking should expose smart_account_move_ids for the Accounting Documents smart link.",
        )
        self.assertIn(
            "smart_account_move_count",
            self.picking._fields,
            "stock.picking should expose smart_account_move_count for the Accounting Documents smart link.",
        )
        self.assertGreaterEqual(self.picking.smart_account_move_count, 1)
        self.assertIn(self.invoice, self.picking.smart_account_move_ids)

    def test_stock_picking_related_account_move_helper_exists(self):
        self.assertTrue(
            hasattr(self.picking, "_get_related_account_moves"),
            "stock.picking should expose _get_related_account_moves() for relation-based smart links.",
        )
        self.assertIn(self.invoice, self.picking._get_related_account_moves())

    def test_account_move_adjustments_include_credit_note(self):
        self.assertIn(
            "smart_adjustment_ids",
            self.invoice._fields,
            "account.move should expose smart_adjustment_ids for the Adjustments smart link.",
        )
        self.assertIn(
            "smart_adjustment_count",
            self.invoice._fields,
            "account.move should expose smart_adjustment_count for the Adjustments smart link.",
        )
        self.assertIn(self.credit_note, self.invoice.smart_adjustment_ids)
        self.assertGreaterEqual(self.invoice.smart_adjustment_count, 1)

    def test_account_move_related_adjustment_helper_exists(self):
        self.assertTrue(
            hasattr(self.invoice, "_get_related_adjustments"),
            "account.move should expose _get_related_adjustments() for relation-based smart links.",
        )
        self.assertIn(self.credit_note, self.invoice._get_related_adjustments())

    def test_empty_sale_side_actions_use_restricted_empty_domain(self):
        credit_action = self.sale_order_without_posted_credit_note.action_view_smart_credit_notes()
        debit_action = self.sale_order_without_debit_note.action_view_smart_debit_notes()

        self.assertEqual(credit_action["domain"], [("id", "in", [])])
        self.assertEqual(debit_action["domain"], [("id", "in", [])])

    def test_account_move_adjustments_ignore_dtr_dncn_fallback_when_fields_absent(self):
        if self.has_dtr_dncn_fields:
            self.skipTest("This assertion targets databases without dtr_dncn fields")
        self.assertNotIn("dncn", self.invoice._fields)
        self.assertNotIn("parent_id", self.invoice._fields)
        self.assertNotIn("child_ids", self.invoice._fields)
        self.assertEqual(
            self.invoice.smart_adjustment_ids,
            self.credit_note,
            "smart_adjustment_ids should keep standard reversal relations when dtr_dncn fields are absent.",
        )
        self.assertEqual(self.invoice.smart_adjustment_count, 1)

    def test_account_move_adjustments_include_dtr_dncn_debit_note(self):
        self._skip_if_missing_dtr_dncn_fields()
        self.assertEqual(
            self.debit_note.parent_id,
            self.invoice,
            "Debit note fixture should be linked to the invoice through parent_id.",
        )
        self.assertIn(
            self.debit_note,
            self.invoice.child_ids,
            "Debit note fixture should be reachable from the invoice through child_ids.",
        )
        self.assertEqual(
            self.debit_note.dncn,
            "dn",
            "Debit note fixture should exercise the dtr_dncn debit note flow.",
        )
        self.assertNotIn(
            self.debit_note,
            self.invoice.reversal_move_id | self.invoice.reversed_entry_id,
            "Debit note fixture must not rely on Odoo reversal links for this adjustment test.",
        )
        self.assertIn(
            self.debit_note,
            self.invoice.smart_adjustment_ids,
            "smart_adjustment_ids should include debit notes linked through dtr_dncn parent_id/child_ids.",
        )

    def test_account_move_related_adjustments_include_dtr_dncn_debit_note(self):
        self._skip_if_missing_dtr_dncn_fields()
        adjustments = self.invoice._get_related_adjustments()
        self.assertEqual(
            self.debit_note.parent_id,
            self.invoice,
            "Debit note fixture should be linked to the invoice through parent_id.",
        )
        self.assertIn(
            self.debit_note,
            self.invoice.child_ids,
            "Debit note fixture should be reachable from the invoice through child_ids.",
        )
        self.assertEqual(
            self.debit_note.dncn,
            "dn",
            "Debit note fixture should exercise the dtr_dncn debit note flow.",
        )
        self.assertIn(
            self.debit_note,
            adjustments,
            "_get_related_adjustments() should include debit notes linked through dtr_dncn parent_id/child_ids.",
        )

    def test_sale_order_debit_notes_stay_empty_when_dtr_dncn_fields_absent(self):
        if self.has_dtr_dncn_fields:
            self.skipTest("This assertion targets databases without dtr_dncn fields")
        self.assertEqual(
            self.sale_order.smart_debit_note_count,
            0,
            "smart_debit_note_count should stay empty when dtr_dncn fields are absent.",
        )
        self.assertFalse(
            self.sale_order.smart_debit_note_ids,
            "smart_debit_note_ids should stay empty when dtr_dncn fields are absent.",
        )
        self.assertFalse(
            self.sale_order._get_related_debit_notes(),
            "_get_related_debit_notes() should return an empty recordset when dtr_dncn fields are absent.",
        )

    def test_sale_order_exposes_debit_note_links(self):
        self._skip_if_missing_dtr_dncn_fields()
        self.assertIn(
            "smart_debit_note_ids",
            self.sale_order._fields,
            "sale.order should expose smart_debit_note_ids for the Debit Notes smart link.",
        )
        self.assertIn(
            "smart_debit_note_count",
            self.sale_order._fields,
            "sale.order should expose smart_debit_note_count for the Debit Notes smart link.",
        )
        self.assertEqual(
            self.debit_note.parent_id,
            self.invoice,
            "Debit note test fixture should be linked only through dtr_dncn parent_id.",
        )
        self.assertFalse(
            self.debit_note.invoice_line_ids.mapped("sale_line_ids"),
            "Debit note fixture must not keep sale line relations so the fallback depends on parent_id/child_ids only.",
        )
        self.assertEqual(self.sale_order.smart_debit_note_count, 1)
        self.assertEqual(self.sale_order.smart_debit_note_ids, self.debit_note)

    def test_sale_order_related_debit_note_helper_exists(self):
        self._skip_if_missing_dtr_dncn_fields()
        self.assertTrue(
            hasattr(self.sale_order, "_get_related_debit_notes"),
            "sale.order should expose _get_related_debit_notes() for relation-based smart links.",
        )
        self.assertEqual(
            self.sale_order._get_related_debit_notes(),
            self.debit_note,
        )

    def test_sale_order_exposes_credit_note_links(self):
        self.assertIn(
            "smart_credit_note_ids",
            self.sale_order._fields,
            "sale.order should expose smart_credit_note_ids for the Credit Notes smart link.",
        )
        self.assertIn(
            "smart_credit_note_count",
            self.sale_order._fields,
            "sale.order should expose smart_credit_note_count for the Credit Notes smart link.",
        )
        self.assertEqual(self.credit_note.state, "posted")
        self.assertEqual(self.draft_credit_note.state, "draft")
        self.assertEqual(self.cancelled_credit_note.state, "cancel")
        self.assertEqual(self.sale_order.smart_credit_note_count, 1)
        self.assertEqual(self.sale_order.smart_credit_note_ids, self.credit_note)
        self.assertNotIn(
            self.draft_credit_note,
            self.sale_order.smart_credit_note_ids,
            "smart_credit_note_ids should exclude draft credit notes.",
        )
        self.assertNotIn(
            self.cancelled_credit_note,
            self.sale_order.smart_credit_note_ids,
            "smart_credit_note_ids should exclude cancelled credit notes.",
        )

    def test_sale_order_related_credit_note_helper_exists(self):
        self.assertTrue(
            hasattr(self.sale_order, "_get_related_credit_notes"),
            "sale.order should expose _get_related_credit_notes() for relation-based smart links.",
        )
        self.assertEqual(
            self.sale_order._get_related_credit_notes(),
            self.credit_note,
        )
        self.assertNotIn(
            self.draft_credit_note,
            self.sale_order._get_related_credit_notes(),
            "_get_related_credit_notes() should exclude draft credit notes.",
        )
        self.assertNotIn(
            self.cancelled_credit_note,
            self.sale_order._get_related_credit_notes(),
            "_get_related_credit_notes() should exclude cancelled credit notes.",
        )

    def test_sale_order_credit_notes_action_opens_form_when_one_related_record(self):
        self.assertTrue(
            hasattr(self.sale_order, "action_view_smart_credit_notes"),
            "sale.order should expose action_view_smart_credit_notes() for the Credit Notes smart button.",
        )
        action = self.sale_order.action_view_smart_credit_notes()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action["views"][0][1],
            "form",
            "A single related Credit Note should open directly in form view.",
        )
        self.assertEqual(
            action["res_id"],
            self.credit_note.id,
            "The action should open only the related posted Credit Note.",
        )
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.credit_note.ids)],
            "Single-record actions should still keep the restricted domain.",
        )

    def test_sale_order_credit_notes_action_returns_empty_domain_when_only_draft_or_cancelled_exist(
        self,
    ):
        self.assertEqual(self.draft_only_credit_note.state, "draft")
        self.assertEqual(self.cancelled_only_credit_note.state, "cancel")
        self.assertIn(
            "smart_credit_note_count",
            self.sale_order_without_posted_credit_note._fields,
            "sale.order should expose smart_credit_note_count for the Credit Notes smart link.",
        )
        self.assertEqual(
            self.sale_order_without_posted_credit_note.smart_credit_note_count,
            0,
            "smart_credit_note_count should ignore draft and cancelled credit notes.",
        )
        self.assertFalse(
            self.sale_order_without_posted_credit_note.smart_credit_note_ids,
            "smart_credit_note_ids should stay empty when only draft or cancelled credit notes exist.",
        )
        self.assertTrue(
            hasattr(
                self.sale_order_without_posted_credit_note,
                "action_view_smart_credit_notes",
            ),
            "sale.order should expose action_view_smart_credit_notes() for the Credit Notes smart button.",
        )
        action = self.sale_order_without_posted_credit_note.action_view_smart_credit_notes()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain", []),
            [("id", "in", [])],
            "When no posted related credit note exists, the action should stay restricted to an empty id-domain.",
        )

    def test_account_move_sale_orders_action_opens_form_when_one_related_order(self):
        self.assertTrue(
            hasattr(self.invoice, "action_view_smart_sale_orders"),
            "account.move should expose action_view_smart_sale_orders() for the Sale Orders smart button.",
        )
        action = self.invoice.action_view_smart_sale_orders()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(
            action["views"][0][1],
            "form",
            "A single related Sale Order should open directly in form view.",
        )
        self.assertEqual(
            action["res_id"],
            self.sale_order.id,
            "The action should open the only related Sale Order.",
        )
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.sale_order.ids)],
            "Single-record actions should still keep the restricted domain.",
        )

    def test_account_move_deliveries_action_opens_form_when_one_related_delivery(self):
        self.assertEqual(
            self.invoice.smart_delivery_count,
            1,
            "The delivery fixture should exercise the single-delivery action path.",
        )
        self.assertTrue(
            hasattr(self.invoice, "action_view_smart_deliveries"),
            "account.move should expose action_view_smart_deliveries() for the Deliveries smart button.",
        )
        action = self.invoice.action_view_smart_deliveries()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "stock.picking")
        self.assertEqual(
            action["views"][0][1],
            "form",
            "A single related Delivery should open directly in form view.",
        )
        self.assertEqual(
            action["res_id"],
            self.picking.id,
            "The action should open the only related Delivery.",
        )
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.picking.ids)],
            "Single-record actions should still keep the restricted domain.",
        )

    def test_sale_order_debit_notes_action_returns_empty_domain_when_none_exist(self):
        self.assertEqual(
            self.sale_order_without_debit_note.smart_debit_note_count,
            0,
            "The zero-related fixture should not expose any debit notes.",
        )
        self.assertFalse(
            self.sale_order_without_debit_note.smart_debit_note_ids,
            "The zero-related fixture should have an empty debit note recordset.",
        )
        self.assertTrue(
            hasattr(self.sale_order_without_debit_note, "action_view_smart_debit_notes"),
            "sale.order should expose action_view_smart_debit_notes() for the Debit Notes smart button.",
        )
        action = self.sale_order_without_debit_note.action_view_smart_debit_notes()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain", []),
            [("id", "in", [])],
            "When no related debit note exists, the action should stay restricted to an empty id-domain.",
        )

    def test_account_move_adjustments_action_opens_list_for_multiple_related_records(self):
        self._skip_if_missing_dtr_dncn_fields()
        related_adjustments = self.credit_note | self.debit_note
        self.assertEqual(
            self.invoice.smart_adjustment_ids,
            related_adjustments,
            "The many-related fixture should include both credit and debit note adjustments.",
        )
        self.assertEqual(self.invoice.smart_adjustment_count, 2)
        self.assertTrue(
            hasattr(self.invoice, "action_view_smart_adjustments"),
            "account.move should expose action_view_smart_adjustments() for the Adjustments smart button.",
        )
        action = self.invoice.action_view_smart_adjustments()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", related_adjustments.ids)],
            "Multiple related adjustments should open a restricted list action.",
        )
        self.assertFalse(
            action.get("res_id"),
            "List actions for multiple related adjustments should not force a single res_id.",
        )

    def test_stock_picking_account_moves_action_returns_act_window(self):
        self.assertGreaterEqual(
            self.picking.smart_account_move_count,
            2,
            "The picking fixture should exercise the multiple-account-move action path.",
        )
        self.assertTrue(
            hasattr(self.picking, "action_view_smart_account_moves"),
            "stock.picking should expose action_view_smart_account_moves() for the Accounting Documents smart button.",
        )
        action = self.picking.action_view_smart_account_moves()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.picking.smart_account_move_ids.ids)],
            "The picking action should stay restricted to the related accounting documents.",
        )
