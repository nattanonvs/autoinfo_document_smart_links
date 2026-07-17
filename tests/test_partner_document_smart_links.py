from lxml import etree

from odoo import fields
from odoo.addons.sale.tests.common import TestSaleCommon
from odoo.tests import Form, tagged


@tagged("post_install", "-at_install")
class TestPartnerDocumentSmartLinks(TestSaleCommon):
    @classmethod
    def _get_payments_from_action(cls, action):
        payment_model = cls.env["account.payment"]
        if action.get("res_id"):
            return payment_model.browse(action["res_id"])
        return payment_model.search(action.get("domain", []))

    @classmethod
    def _create_payment(cls, moves, amount=None):
        payment_register = cls.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=moves.ids,
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
    def _create_unmatched_customer_payment(cls, partner, amount=50.0):
        journal = cls.env["account.journal"].search(
            [
                ("company_id", "=", cls.env.company.id),
                ("type", "in", ("bank", "cash")),
            ],
            limit=1,
        )
        payment_method_line = journal.inbound_payment_method_line_ids[:1]
        payment = cls.env["account.payment"].create(
            {
                "payment_type": "inbound",
                "payment_method_line_id": payment_method_line.id,
                "partner_type": "customer",
                "partner_id": partner.id,
                "amount": amount,
                "currency_id": cls.env.company.currency_id.id,
                "journal_id": journal.id,
            }
        )
        payment.action_post()
        return payment

    @classmethod
    def _create_sale_order(cls, partner, quantity=1.0):
        sale_order = cls.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "partner_invoice_id": partner.id,
                "partner_shipping_id": partner.id,
                "pricelist_id": cls.company_data["default_pricelist"].id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.company_data["product_order_no"].name,
                            "product_id": cls.company_data["product_order_no"].id,
                            "product_uom_qty": quantity,
                            "product_uom": cls.company_data["product_order_no"].uom_id.id,
                            "price_unit": cls.company_data["product_order_no"].list_price,
                        },
                    )
                ],
            }
        )
        sale_order.action_confirm()
        return sale_order

    @classmethod
    def _validate_partial_delivery(cls, picking, quantity_done):
        picking.move_lines.write({"quantity_done": quantity_done})
        backorder_action = picking.button_validate()
        if backorder_action:
            backorder_wizard = Form(
                cls.env[backorder_action["res_model"]].with_context(
                    backorder_action["context"]
                )
            ).save()
            backorder_wizard.process()
        backorder = (
            picking.sale_id.picking_ids.filtered(
                lambda candidate: candidate != picking and candidate.state != "cancel"
            )
            - picking
        ).filtered(lambda candidate: candidate.state != "done")[:1]
        return backorder

    @classmethod
    def _create_return_picking(cls, picking):
        return_wizard = Form(
            cls.env["stock.return.picking"].with_context(
                active_id=picking.id,
                active_model="stock.picking",
            )
        ).save()
        action = return_wizard.create_returns()
        return cls.env["stock.picking"].browse(action["res_id"])

    @classmethod
    def _create_credit_note(cls, invoice):
        reversal = cls.env["account.move.reversal"].with_context(
            active_model="account.move",
            active_id=invoice.id,
            active_ids=invoice.ids,
        ).create(
            {
                "refund_method": "refund",
                "reason": "Partner smart links performance guard regression test",
                "journal_id": invoice.journal_id.id,
            }
        )
        action = reversal.reverse_moves()
        credit_note = cls.env["account.move"].browse(action["res_id"])
        if credit_note.state != "posted":
            credit_note.action_post()
        return credit_note

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendor = cls.env["res.partner"].create(
            {"name": "Partner Smart Link Vendor", "supplier_rank": 1}
        )
        cls.customer_partner = cls.env["res.partner"].create(
            {
                "name": "Partner Smart Link Customer",
                "customer_rank": 1,
                "property_product_pricelist": cls.company_data[
                    "default_pricelist"
                ].id,
            }
        )
        cls.sale_order = cls._create_sale_order(cls.customer_partner)
        cls.delivery = cls.sale_order.picking_ids[:1]
        cls.customer_invoice = cls.sale_order._create_invoices()
        cls.customer_invoice.action_post()
        cls.customer_credit_note = cls._create_credit_note(cls.customer_invoice)
        cls.matched_customer_payment = cls._create_payment(
            cls.customer_invoice,
            amount=cls.customer_invoice.amount_total / 2.0,
        )
        cls.unmatched_customer_payment = cls._create_unmatched_customer_payment(
            cls.customer_partner
        )
        cls.cancelled_sale_order = cls._create_sale_order(cls.customer_partner)
        cls.cancelled_delivery = cls.cancelled_sale_order.picking_ids[:1]
        cls.cancelled_delivery.action_cancel()
        cls.partial_sale_order = cls._create_sale_order(
            cls.customer_partner,
            quantity=3.0,
        )
        cls.partial_delivery = cls.partial_sale_order.picking_ids[:1]
        cls.partial_backorder_delivery = cls._validate_partial_delivery(
            cls.partial_delivery,
            quantity_done=1.0,
        )
        cls.return_delivery = cls._create_return_picking(cls.partial_delivery)

    def test_partner_exposes_purchase_fields(self):
        self.assertIn(
            "smart_purchase_order_ids",
            self.vendor._fields,
            "res.partner should expose smart_purchase_order_ids for the Purchase Orders smart link.",
        )
        self.assertIn(
            "smart_purchase_order_count",
            self.vendor._fields,
            "res.partner should expose smart_purchase_order_count for the Purchase Orders smart link.",
        )

    def test_partner_exposes_vendor_bill_fields(self):
        self.assertIn(
            "smart_vendor_bill_ids",
            self.vendor._fields,
            "res.partner should expose smart_vendor_bill_ids for the Vendor Bills smart link.",
        )
        self.assertIn(
            "smart_vendor_bill_count",
            self.vendor._fields,
            "res.partner should expose smart_vendor_bill_count for the Vendor Bills smart link.",
        )

    def test_partner_exposes_payment_fields(self):
        self.assertIn(
            "smart_payment_ids",
            self.vendor._fields,
            "res.partner should expose smart_payment_ids for the Payments smart link.",
        )
        self.assertIn(
            "smart_payment_count",
            self.vendor._fields,
            "res.partner should expose smart_payment_count for the Payments smart link.",
        )

    def test_partner_exposes_sale_order_fields(self):
        self.assertIn(
            "smart_sale_order_ids",
            self.vendor._fields,
            "res.partner should expose smart_sale_order_ids for the Sale Orders smart link.",
        )
        self.assertIn(
            "smart_sale_order_count",
            self.vendor._fields,
            "res.partner should expose smart_sale_order_count for the Sale Orders smart link.",
        )

    def test_partner_exposes_delivery_fields(self):
        self.assertIn(
            "smart_delivery_ids",
            self.vendor._fields,
            "res.partner should expose smart_delivery_ids for the Deliveries smart link.",
        )
        self.assertIn(
            "smart_delivery_count",
            self.vendor._fields,
            "res.partner should expose smart_delivery_count for the Deliveries smart link.",
        )

    def test_partner_exposes_customer_invoice_fields(self):
        self.assertIn(
            "smart_customer_invoice_ids",
            self.vendor._fields,
            "res.partner should expose smart_customer_invoice_ids for the Customer Invoices smart link.",
        )
        self.assertIn(
            "smart_customer_invoice_count",
            self.vendor._fields,
            "res.partner should expose smart_customer_invoice_count for the Customer Invoices smart link.",
        )

    def test_partner_exposes_customer_credit_note_fields(self):
        self.assertIn(
            "smart_customer_credit_note_ids",
            self.vendor._fields,
            "res.partner should expose smart_customer_credit_note_ids for the Customer Credit Notes smart link.",
        )
        self.assertIn(
            "smart_customer_credit_note_count",
            self.vendor._fields,
            "res.partner should expose smart_customer_credit_note_count for the Customer Credit Notes smart link.",
        )

    def test_partner_exposes_customer_payment_fields(self):
        self.assertIn(
            "smart_customer_payment_ids",
            self.vendor._fields,
            "res.partner should expose smart_customer_payment_ids for the Customer Payments smart link.",
        )
        self.assertIn(
            "smart_customer_payment_count",
            self.vendor._fields,
            "res.partner should expose smart_customer_payment_count for the Customer Payments smart link.",
        )

    def test_partner_related_purchase_helpers_exist(self):
        self.assertTrue(
            hasattr(self.vendor, "_get_related_purchase_orders"),
            "res.partner should expose _get_related_purchase_orders() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_vendor_bills"),
            "res.partner should expose _get_related_vendor_bills() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_payments"),
            "res.partner should expose _get_related_payments() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_sale_orders"),
            "res.partner should expose _get_related_sale_orders() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_deliveries"),
            "res.partner should expose _get_related_deliveries() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_customer_invoices"),
            "res.partner should expose _get_related_customer_invoices() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_customer_credit_notes"),
            "res.partner should expose _get_related_customer_credit_notes() for partner smart links.",
        )
        self.assertTrue(
            hasattr(self.vendor, "_get_related_customer_payments"),
            "res.partner should expose _get_related_customer_payments() for partner smart links.",
        )

    def test_partner_action_methods_exist(self):
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_purchase_orders"),
            "res.partner should expose action_view_smart_purchase_orders() for the Purchase Orders smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_vendor_bills"),
            "res.partner should expose action_view_smart_vendor_bills() for the Vendor Bills smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_payments"),
            "res.partner should expose action_view_smart_payments() for the Payments smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_sale_orders"),
            "res.partner should expose action_view_smart_sale_orders() for the Sale Orders smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_deliveries"),
            "res.partner should expose action_view_smart_deliveries() for the Deliveries smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_customer_invoices"),
            "res.partner should expose action_view_smart_customer_invoices() for the Customer Invoices smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_customer_credit_notes"),
            "res.partner should expose action_view_smart_customer_credit_notes() for the Customer Credit Notes smart button.",
        )
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_customer_payments"),
            "res.partner should expose action_view_smart_customer_payments() for the Customer Payments smart button.",
        )

    def test_partner_purchase_orders_builder_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "_build_smart_action"),
            "res.partner should expose a shared smart action builder for partner smart links.",
        )
        fake_orders = self.env["purchase.order"].browse([101])
        action = self.vendor._build_smart_action(
            fake_orders,
            "purchase.order",
            "Purchase Orders",
        )

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "purchase.order")
        self.assertEqual(
            action["views"][0][1],
            "form",
            "A single related Purchase Order should open directly in form view.",
        )
        self.assertEqual(
            action["res_id"],
            101,
            "The smart action should open the only related Purchase Order.",
        )
        self.assertEqual(
            action.get("domain"),
            [("id", "in", fake_orders.ids)],
            "Single-record partner actions should still keep the restricted domain.",
        )

    def test_partner_vendor_bills_builder_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "_build_smart_action"),
            "res.partner should expose a shared smart action builder for partner smart links.",
        )
        fake_bills = self.env["account.move"].browse([201, 202])
        action = self.vendor._build_smart_action(
            fake_bills,
            "account.move",
            "Vendor Bills",
        )

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", fake_bills.ids)],
            "Partner Vendor Bills actions should stay restricted to the related record ids.",
        )
        self.assertFalse(
            action.get("res_id"),
            "Multi-record partner Vendor Bills actions should not force a single res_id.",
        )

    def test_partner_payments_builder_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "_build_smart_action"),
            "res.partner should expose a shared smart action builder for partner smart links.",
        )
        fake_payments = self.env["account.payment"].browse([301, 302])
        action = self.vendor._build_smart_action(
            fake_payments,
            "account.payment",
            "Payments",
        )

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.payment")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", fake_payments.ids)],
            "Partner Payments actions should stay restricted to the related record ids.",
        )
        self.assertFalse(
            action.get("res_id"),
            "Multi-record partner Payments actions should not force a single res_id.",
        )

    def test_partner_sale_orders_action_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_sale_orders"),
            "res.partner should expose action_view_smart_sale_orders() for the Sale Orders smart button.",
        )
        action = self.vendor.action_view_smart_sale_orders()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.vendor.smart_sale_order_ids.ids)],
            "Partner Sale Orders actions should stay restricted to the related record ids.",
        )

    def test_partner_deliveries_action_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_deliveries"),
            "res.partner should expose action_view_smart_deliveries() for the Deliveries smart button.",
        )
        action = self.vendor.action_view_smart_deliveries()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "stock.picking")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.vendor.smart_delivery_ids.ids)],
            "Partner Deliveries actions should stay restricted to the related record ids.",
        )

    def test_partner_customer_invoices_action_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_customer_invoices"),
            "res.partner should expose action_view_smart_customer_invoices() for the Customer Invoices smart button.",
        )
        action = self.vendor.action_view_smart_customer_invoices()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.vendor.smart_customer_invoice_ids.ids)],
            "Partner Customer Invoices actions should stay restricted to the related record ids.",
        )

    def test_partner_customer_credit_notes_action_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.vendor, "action_view_smart_customer_credit_notes"),
            "res.partner should expose action_view_smart_customer_credit_notes() for the Customer Credit Notes smart button.",
        )
        action = self.vendor.action_view_smart_customer_credit_notes()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.move")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.vendor.smart_customer_credit_note_ids.ids)],
            "Partner Customer Credit Notes actions should stay restricted to the related record ids.",
        )

    def test_partner_deliveries_only_include_outgoing_non_cancelled_sale_flow_pickings(
        self,
    ):
        sale_flow_pickings = self.customer_partner.smart_sale_order_ids.mapped(
            "picking_ids"
        )

        self.assertIn(
            self.delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should include the active outgoing delivery created from the partner sale flow.",
        )
        self.assertNotIn(
            self.cancelled_delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should exclude cancelled deliveries from the partner sale flow.",
        )
        self.assertFalse(
            self.customer_partner.smart_delivery_ids - sale_flow_pickings,
            "smart_delivery_ids should only include pickings reached from the related sale orders.",
        )
        self.assertTrue(
            all(
                picking.picking_type_code == "outgoing"
                and picking.state != "cancel"
                for picking in self.customer_partner.smart_delivery_ids
            ),
            "smart_delivery_ids should only keep outgoing and non-cancelled deliveries.",
        )

    def test_partner_deliveries_include_all_partial_outgoing_pickings(self):
        self.assertTrue(
            self.partial_backorder_delivery,
            "the test fixture must create a backorder delivery from the partial validation flow.",
        )
        self.assertIn(
            self.partial_delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should keep the done outgoing picking from a partial delivery flow.",
        )
        self.assertIn(
            self.partial_backorder_delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should also keep the remaining outgoing backorder from a partial delivery flow.",
        )

    def test_partner_deliveries_exclude_return_pickings(self):
        self.assertIn(
            self.return_delivery,
            self.partial_sale_order.picking_ids,
            "the test fixture must attach the return picking to the same sale-order chain.",
        )
        self.assertNotIn(
            self.return_delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should exclude return pickings even when they belong to the same sale-order chain.",
        )

    def test_partner_customer_invoices_only_include_out_invoices(self):
        self.assertIn(
            self.customer_invoice,
            self.customer_partner.smart_customer_invoice_ids,
            "smart_customer_invoice_ids should include posted customer invoices from the partner sale flow.",
        )
        self.assertNotIn(
            self.customer_credit_note,
            self.customer_partner.smart_customer_invoice_ids,
            "smart_customer_invoice_ids should not mix customer credit notes into the invoice smart link.",
        )
        self.assertTrue(
            all(
                move.move_type == "out_invoice" and move.state != "cancel"
                for move in self.customer_partner.smart_customer_invoice_ids
            ),
            "smart_customer_invoice_ids should only keep non-cancelled customer invoices.",
        )

    def test_partner_customer_credit_notes_only_include_out_refunds(self):
        self.assertIn(
            self.customer_credit_note,
            self.customer_partner.smart_customer_credit_note_ids,
            "smart_customer_credit_note_ids should include posted customer credit notes from the partner sale flow.",
        )
        self.assertNotIn(
            self.customer_invoice,
            self.customer_partner.smart_customer_credit_note_ids,
            "smart_customer_credit_note_ids should not mix customer invoices into the credit note smart link.",
        )
        self.assertTrue(
            all(
                move.move_type == "out_refund" and move.state != "cancel"
                for move in self.customer_partner.smart_customer_credit_note_ids
            ),
            "smart_customer_credit_note_ids should only keep non-cancelled customer credit notes.",
        )

    def test_partner_customer_payments_only_include_matched_customer_payments(self):
        self.assertIn(
            self.matched_customer_payment,
            self.customer_partner.smart_customer_payment_ids,
            "smart_customer_payment_ids should include customer payments reconciled from related customer moves.",
        )
        self.assertNotIn(
            self.unmatched_customer_payment,
            self.customer_partner.smart_customer_payment_ids,
            "smart_customer_payment_ids should exclude customer payments that are still unmatched.",
        )
        self.assertEqual(
            self.customer_partner.smart_customer_payment_count,
            len(self.customer_partner.smart_customer_payment_ids),
            "smart_customer_payment_count should match the number of related matched customer payments.",
        )
        self.assertTrue(
            all(
                payment.state != "cancel"
                for payment in self.customer_partner.smart_customer_payment_ids
            ),
            "smart_customer_payment_ids should only keep non-cancelled matched customer payments.",
        )

    def test_partner_related_customer_payments_only_include_matched_customer_payments(
        self,
    ):
        self.assertTrue(
            hasattr(self.customer_partner, "_get_related_customer_payments"),
            "res.partner should expose _get_related_customer_payments() for matched customer payments.",
        )
        payments = self.customer_partner._get_related_customer_payments()

        self.assertIn(
            self.matched_customer_payment,
            payments,
            "_get_related_customer_payments() should include customer payments matched to related customer moves.",
        )
        self.assertNotIn(
            self.unmatched_customer_payment,
            payments,
            "_get_related_customer_payments() should exclude unmatched customer payments.",
        )

    def test_partner_customer_payments_are_deduplicated_when_customer_moves_repeat(
        self,
    ):
        duplicated_customer_moves = self.env["account.move"].browse(
            self.customer_invoice.ids
            + self.customer_invoice.ids
            + self.customer_credit_note.ids
        )
        payments = self.customer_partner._get_related_customer_payments(
            duplicated_customer_moves
        )

        self.assertEqual(
            payments.ids.count(self.matched_customer_payment.id),
            1,
            "_get_related_customer_payments() should deduplicate matched customer payments even when related customer moves repeat.",
        )
        self.assertEqual(
            len(payments.ids),
            len(set(payments.ids)),
            "smart customer payment helpers should only return unique payment ids.",
        )

    def test_partner_customer_payment_count_excludes_unmatched_customer_payments(self):
        matched_customer_payments = self.customer_partner._get_related_customer_payments()

        self.assertNotIn(
            self.unmatched_customer_payment,
            matched_customer_payments,
            "Unmatched customer payments should stay excluded from the matched customer payment helper used by the smart count.",
        )
        self.assertEqual(
            self.customer_partner.smart_customer_payment_count,
            len(matched_customer_payments),
            "smart_customer_payment_count should only count matched customer payments.",
        )

    def test_partner_sales_actions_use_id_in_domains_with_related_records(self):
        deliveries_action = self.customer_partner.action_view_smart_deliveries()
        invoices_action = self.customer_partner.action_view_smart_customer_invoices()
        credit_notes_action = (
            self.customer_partner.action_view_smart_customer_credit_notes()
        )
        customer_payments_action = (
            self.customer_partner.action_view_smart_customer_payments()
        )

        self.assertEqual(
            deliveries_action.get("domain"),
            [("id", "in", self.customer_partner.smart_delivery_ids.ids)],
            "Partner Deliveries actions should keep an id in domain tied to the computed delivery ids.",
        )
        self.assertEqual(
            invoices_action.get("domain"),
            [("id", "in", self.customer_partner.smart_customer_invoice_ids.ids)],
            "Partner Customer Invoices actions should keep an id in domain tied to the computed invoice ids.",
        )
        self.assertEqual(
            credit_notes_action.get("domain"),
            [
                (
                    "id",
                    "in",
                    self.customer_partner.smart_customer_credit_note_ids.ids,
                )
            ],
            "Partner Customer Credit Notes actions should keep an id in domain tied to the computed credit note ids.",
        )
        self.assertEqual(
            customer_payments_action.get("domain"),
            [
                (
                    "id",
                    "in",
                    self.customer_partner.smart_customer_payment_ids.ids,
                )
            ],
            "Partner Customer Payments actions should keep an id in domain tied to the computed customer payment ids.",
        )

    def test_partner_customer_payments_action_uses_id_in_domain(self):
        action = self.customer_partner.action_view_smart_customer_payments()

        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.customer_partner.smart_customer_payment_ids.ids)],
            "action_view_smart_customer_payments() should stay restricted to an id in domain built from the matched customer payment ids.",
        )

    def test_partner_customer_payments_action_keeps_restricted_domain(self):
        self.assertTrue(
            hasattr(self.customer_partner, "action_view_smart_customer_payments"),
            "res.partner should expose action_view_smart_customer_payments() for the Customer Payments smart button.",
        )
        action = self.customer_partner.action_view_smart_customer_payments()

        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "account.payment")
        self.assertEqual(
            action.get("domain"),
            [("id", "in", self.customer_partner.smart_customer_payment_ids.ids)],
            "Partner Customer Payments actions should stay restricted to the related record ids.",
        )

    def test_partner_deliveries_depth_keeps_expected_outgoing_sale_chain(self):
        expected_deliveries = (
            self.delivery | self.partial_delivery | self.partial_backorder_delivery
        )

        self.assertTrue(
            self.partial_backorder_delivery,
            "the test fixture must keep the outgoing backorder delivery created from the partial validation flow.",
        )
        self.assertEqual(
            set(self.customer_partner.smart_delivery_ids.ids),
            set(expected_deliveries.ids),
            "smart_delivery_ids should keep the full outgoing sale-order delivery chain without reintroducing cancelled or return pickings.",
        )
        self.assertNotIn(
            self.cancelled_delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should continue excluding cancelled deliveries after the delivery-depth expansion.",
        )
        self.assertNotIn(
            self.return_delivery,
            self.customer_partner.smart_delivery_ids,
            "smart_delivery_ids should continue excluding return pickings after the delivery-depth expansion.",
        )

    def test_partner_form_view_exposes_purchase_smart_buttons(self):
        arch = self.env["res.partner"].fields_view_get(view_type="form")["arch"]
        view = etree.fromstring(arch.encode())

        for button_name, count_field in (
            ("action_view_smart_purchase_orders", "smart_purchase_order_count"),
            ("action_view_smart_vendor_bills", "smart_vendor_bill_count"),
            ("action_view_smart_payments", "smart_payment_count"),
        ):
            buttons = view.xpath("//button[@name='%s']" % button_name)
            self.assertTrue(
                buttons,
                "res.partner form view should expose %s smart button." % button_name,
            )
            self.assertTrue(
                buttons[0].xpath(".//field[@name='%s']" % count_field),
                "res.partner smart button %s should display %s."
                % (button_name, count_field),
            )

    def test_partner_smart_links_view_arch_exposes_sales_buttons(self):
        smart_links_view = self.env.ref(
            "autoinfo_document_smart_links.view_partner_form_document_smart_links"
        )
        view = etree.fromstring(smart_links_view.arch_db.encode())

        for button_name in (
            "action_view_smart_sale_orders",
            "action_view_smart_deliveries",
            "action_view_smart_customer_invoices",
            "action_view_smart_customer_credit_notes",
        ):
            self.assertTrue(
                view.xpath("//button[@name='%s']" % button_name),
                "view_partner_form_document_smart_links should expose %s in its arch."
                % button_name,
            )

    def test_partner_smart_links_view_arch_exposes_customer_payments_button(self):
        smart_links_view = self.env.ref(
            "autoinfo_document_smart_links.view_partner_form_document_smart_links"
        )

        self.assertIn(
            "action_view_smart_customer_payments",
            smart_links_view.arch_db,
            "view_partner_form_document_smart_links should expose action_view_smart_customer_payments in its arch.",
        )
