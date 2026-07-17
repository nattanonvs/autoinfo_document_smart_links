from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    smart_receipt_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_smart_purchase_links",
    )
    smart_receipt_count = fields.Integer(compute="_compute_smart_purchase_links")
    smart_vendor_bill_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_purchase_links",
    )
    smart_vendor_bill_count = fields.Integer(compute="_compute_smart_purchase_links")
    smart_payment_ids = fields.Many2many(
        "account.payment",
        compute="_compute_smart_purchase_links",
    )
    smart_payment_count = fields.Integer(compute="_compute_smart_purchase_links")
    smart_vendor_credit_note_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_purchase_links",
    )
    smart_vendor_credit_note_count = fields.Integer(
        compute="_compute_smart_purchase_links"
    )

    def _get_related_receipts(self):
        self.ensure_one()
        return self.picking_ids.filtered(
            lambda picking: picking.state != "cancel"
            and picking.picking_type_id.code == "incoming"
        )

    def _get_related_vendor_bills(self):
        self.ensure_one()
        bill_lines = self.order_line.mapped("invoice_lines")
        return bill_lines.mapped("move_id").filtered(
            lambda move: move.move_type == "in_invoice" and move.state != "cancel"
        )

    def _get_related_payments(self):
        self.ensure_one()
        bills = self._get_related_vendor_bills()
        if not bills:
            return self.env["account.payment"]
        return bills._get_reconciled_payments().filtered(
            lambda payment: payment.state != "cancel"
        )

    def _get_related_vendor_credit_notes(self):
        self.ensure_one()
        bills = self._get_related_vendor_bills()
        credit_notes = self.invoice_ids.filtered(
            lambda move: move.move_type == "in_refund" and move.state != "cancel"
        )
        credit_notes |= bills.mapped("reversal_move_id").filtered(
            lambda move: move.move_type == "in_refund" and move.state != "cancel"
        )
        return credit_notes

    def _build_purchase_smart_action(self, records, res_model, name):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "target": "current",
        }
        if not records:
            action.update({"view_mode": "tree,form", "domain": [("id", "in", [])]})
            return action
        action["domain"] = [("id", "in", records.ids)]
        if len(records) == 1:
            action.update(
                {"view_mode": "form", "views": [(False, "form")], "res_id": records.id}
            )
            return action
        action["view_mode"] = "tree,form"
        return action

    def action_view_smart_receipts(self):
        self.ensure_one()
        return self._build_purchase_smart_action(
            self.smart_receipt_ids, "stock.picking", "Receipts"
        )

    def action_view_smart_vendor_bills(self):
        self.ensure_one()
        return self._build_purchase_smart_action(
            self.smart_vendor_bill_ids, "account.move", "Vendor Bills"
        )

    def action_view_smart_payments(self):
        self.ensure_one()
        return self._build_purchase_smart_action(
            self.smart_payment_ids, "account.payment", "Payments"
        )

    def action_view_smart_vendor_credit_notes(self):
        self.ensure_one()
        return self._build_purchase_smart_action(
            self.smart_vendor_credit_note_ids,
            "account.move",
            "Vendor Credit Notes",
        )

    @api.depends(
        "picking_ids",
        "invoice_ids",
        "invoice_ids.move_type",
        "invoice_ids.state",
        "invoice_ids.reversal_move_id",
        "order_line.invoice_lines.move_id",
        "order_line.invoice_lines.move_id.reversal_move_id",
        "order_line.invoice_lines.move_id.line_ids.matched_debit_ids.debit_move_id.payment_id",
        "order_line.invoice_lines.move_id.line_ids.matched_debit_ids.debit_move_id.payment_id.state",
        "order_line.invoice_lines.move_id.line_ids.matched_credit_ids.credit_move_id.payment_id",
        "order_line.invoice_lines.move_id.line_ids.matched_credit_ids.credit_move_id.payment_id.state",
    )
    def _compute_smart_purchase_links(self):
        for order in self:
            receipts = order._get_related_receipts()
            bills = order._get_related_vendor_bills()
            payments = order._get_related_payments()
            vendor_credit_notes = order._get_related_vendor_credit_notes()
            order.smart_receipt_ids = receipts
            order.smart_receipt_count = len(receipts)
            order.smart_vendor_bill_ids = bills
            order.smart_vendor_bill_count = len(bills)
            order.smart_payment_ids = payments
            order.smart_payment_count = len(payments)
            order.smart_vendor_credit_note_ids = vendor_credit_notes
            order.smart_vendor_credit_note_count = len(vendor_credit_notes)
