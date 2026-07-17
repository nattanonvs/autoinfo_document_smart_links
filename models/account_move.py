from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    smart_sale_order_ids = fields.Many2many(
        "sale.order",
        compute="_compute_smart_links",
    )
    smart_sale_order_count = fields.Integer(compute="_compute_smart_links")
    smart_delivery_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_smart_links",
    )
    smart_delivery_count = fields.Integer(compute="_compute_smart_links")
    smart_adjustment_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_links",
    )
    smart_adjustment_count = fields.Integer(compute="_compute_smart_links")
    smart_purchase_order_ids = fields.Many2many(
        "purchase.order",
        compute="_compute_smart_links",
    )
    smart_purchase_order_count = fields.Integer(compute="_compute_smart_links")
    smart_receipt_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_smart_links",
    )
    smart_receipt_count = fields.Integer(compute="_compute_smart_links")
    smart_payment_ids = fields.Many2many(
        "account.payment",
        compute="_compute_smart_links",
    )
    smart_payment_count = fields.Integer(compute="_compute_smart_links")

    def _is_vendor_bill_for_smart_links(self):
        self.ensure_one()
        return self.move_type == "in_invoice"

    def _is_vendor_credit_note_for_smart_links(self):
        self.ensure_one()
        return self.move_type == "in_refund"

    def _get_related_sale_orders(self):
        self.ensure_one()
        return self.invoice_line_ids.mapped("sale_line_ids.order_id")

    def _get_related_deliveries(self):
        self.ensure_one()
        return self._get_related_sale_orders().mapped("picking_ids")

    def _get_related_adjustments(self):
        self.ensure_one()
        adjustments = self.reversal_move_id | self.reversed_entry_id
        move_model = self.env["account.move"]

        if "child_ids" in move_model._fields:
            debit_notes = self.child_ids
            if "dncn" in move_model._fields:
                debit_notes = debit_notes.filtered(lambda move: move.dncn == "dn")
            adjustments |= debit_notes

        return adjustments.filtered(lambda move: move.is_invoice(include_receipts=False))

    def _get_vendor_credit_note_source_bills(self):
        self.ensure_one()
        if not self._is_vendor_credit_note_for_smart_links():
            return self.env["account.move"]
        source_bills = self.reversed_entry_id.filtered(
            lambda move: move.move_type == "in_invoice"
        )
        if source_bills:
            return source_bills
        return self._get_related_adjustments().filtered(
            lambda move: move.move_type == "in_invoice"
        )

    def _get_related_purchase_orders(self):
        self.ensure_one()
        if self._is_vendor_bill_for_smart_links():
            return self.invoice_line_ids.mapped("purchase_line_id.order_id")
        if not self._is_vendor_credit_note_for_smart_links():
            return self.env["purchase.order"]

        purchase_orders = self.env["purchase.order"]
        for source_bill in self._get_vendor_credit_note_source_bills():
            purchase_orders |= source_bill._get_related_purchase_orders()
        if purchase_orders:
            return purchase_orders
        return self.invoice_line_ids.mapped("purchase_line_id.order_id")

    def _get_related_receipts(self):
        self.ensure_one()
        if self._is_vendor_bill_for_smart_links():
            return self._get_related_purchase_orders().mapped("picking_ids").filtered(
                lambda picking: picking.state != "cancel"
                and picking.picking_type_id.code == "incoming"
            )
        if not self._is_vendor_credit_note_for_smart_links():
            return self.env["stock.picking"]

        receipts = self.env["stock.picking"]
        for source_bill in self._get_vendor_credit_note_source_bills():
            receipts |= source_bill._get_related_receipts()
        if receipts:
            return receipts
        return self._get_related_purchase_orders().mapped("picking_ids").filtered(
            lambda picking: picking.state != "cancel"
            and picking.picking_type_id.code == "incoming"
        )

    def _get_related_payments(self):
        self.ensure_one()
        if not self._is_vendor_bill_for_smart_links():
            return self.env["account.payment"]
        return self._get_reconciled_payments().filtered(lambda payment: payment.state != "cancel")

    def _build_smart_action(self, records, res_model, name):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "target": "current",
        }

        if not records:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", [])],
                }
            )
            return action

        action["domain"] = [("id", "in", records.ids)]
        if len(records) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "views": [(False, "form")],
                    "res_id": records.id,
                }
            )
            return action

        action["view_mode"] = "tree,form"
        return action

    def action_view_smart_sale_orders(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_sale_order_ids, "sale.order", "Sale Orders"
        )

    def action_view_smart_deliveries(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_delivery_ids, "stock.picking", "Deliveries"
        )

    def action_view_smart_adjustments(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_adjustment_ids, "account.move", "Adjustments"
        )

    def action_view_smart_purchase_orders(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_purchase_order_ids, "purchase.order", "Purchase Orders"
        )

    def action_view_smart_receipts(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_receipt_ids, "stock.picking", "Receipts"
        )

    def action_view_smart_payments(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_payment_ids, "account.payment", "Payments"
        )

    @api.depends(
        "invoice_line_ids.sale_line_ids.order_id",
        "invoice_line_ids.sale_line_ids.order_id.picking_ids",
        "invoice_line_ids.purchase_line_id.order_id",
        "invoice_line_ids.purchase_line_id.order_id.picking_ids",
        "reversal_move_id",
        "reversed_entry_id",
        "reversed_entry_id.invoice_line_ids.purchase_line_id.order_id",
        "reversed_entry_id.invoice_line_ids.purchase_line_id.order_id.picking_ids",
        "line_ids.matched_debit_ids.debit_move_id.payment_id",
        "line_ids.matched_debit_ids.debit_move_id.payment_id.state",
        "line_ids.matched_credit_ids.credit_move_id.payment_id",
        "line_ids.matched_credit_ids.credit_move_id.payment_id.state",
    )
    def _compute_smart_links(self):
        for move in self:
            sale_orders = move._get_related_sale_orders()
            deliveries = move._get_related_deliveries()
            adjustments = move._get_related_adjustments()
            purchase_orders = move._get_related_purchase_orders()
            receipts = move._get_related_receipts()
            payments = move._get_related_payments()

            move.smart_sale_order_ids = sale_orders
            move.smart_sale_order_count = len(sale_orders)
            move.smart_delivery_ids = deliveries
            move.smart_delivery_count = len(deliveries)
            move.smart_adjustment_ids = adjustments
            move.smart_adjustment_count = len(adjustments)
            move.smart_purchase_order_ids = purchase_orders
            move.smart_purchase_order_count = len(purchase_orders)
            move.smart_receipt_ids = receipts
            move.smart_receipt_count = len(receipts)
            move.smart_payment_ids = payments
            move.smart_payment_count = len(payments)
