from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    smart_purchase_order_ids = fields.Many2many(
        "purchase.order",
        compute="_compute_smart_purchase_documents",
    )
    smart_purchase_order_count = fields.Integer(
        compute="_compute_smart_purchase_documents"
    )
    smart_vendor_bill_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_purchase_documents",
    )
    smart_vendor_bill_count = fields.Integer(compute="_compute_smart_purchase_documents")
    smart_payment_ids = fields.Many2many(
        "account.payment",
        compute="_compute_smart_purchase_documents",
    )
    smart_payment_count = fields.Integer(compute="_compute_smart_purchase_documents")
    smart_account_move_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_account_moves",
    )
    smart_account_move_count = fields.Integer(compute="_compute_smart_account_moves")

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

    def _get_related_purchase_orders(self):
        self.ensure_one()
        if "purchase_id" in self._fields and self.purchase_id:
            return self.purchase_id
        return self.move_ids_without_package.mapped("purchase_line_id.order_id")

    def _get_related_vendor_bills(self):
        self.ensure_one()
        return self._get_related_purchase_orders().invoice_ids.filtered(
            lambda move: move.state != "cancel"
            and move.move_type in ("in_invoice", "in_refund")
        )

    def _get_related_payments(self):
        self.ensure_one()
        vendor_bills = self._get_related_vendor_bills()
        if not vendor_bills:
            return self.env["account.payment"]
        return vendor_bills._get_reconciled_payments().filtered(
            lambda payment: payment.state != "cancel"
        )

    def _get_related_account_moves(self):
        self.ensure_one()
        return self.sale_id.invoice_ids.filtered(
            lambda move: move.is_invoice(include_receipts=False)
        )

    def action_view_smart_purchase_orders(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_purchase_order_ids, "purchase.order", "Purchase Orders"
        )

    def action_view_smart_vendor_bills(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_vendor_bill_ids, "account.move", "Vendor Bills"
        )

    def action_view_smart_payments(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_payment_ids, "account.payment", "Payments"
        )

    def action_view_smart_account_moves(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_account_move_ids, "account.move", "Accounting Documents"
        )

    @api.depends(
        "purchase_id",
        "purchase_id.invoice_ids",
        "purchase_id.invoice_ids.move_type",
        "purchase_id.invoice_ids.state",
        "purchase_id.invoice_ids.line_ids.matched_debit_ids.debit_move_id.payment_id",
        "purchase_id.invoice_ids.line_ids.matched_debit_ids.debit_move_id.payment_id.state",
        "purchase_id.invoice_ids.line_ids.matched_credit_ids.credit_move_id.payment_id",
        "purchase_id.invoice_ids.line_ids.matched_credit_ids.credit_move_id.payment_id.state",
        "move_ids_without_package.purchase_line_id.order_id",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids.move_type",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids.state",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids.line_ids.matched_debit_ids.debit_move_id.payment_id",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids.line_ids.matched_debit_ids.debit_move_id.payment_id.state",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids.line_ids.matched_credit_ids.credit_move_id.payment_id",
        "move_ids_without_package.purchase_line_id.order_id.invoice_ids.line_ids.matched_credit_ids.credit_move_id.payment_id.state",
    )
    def _compute_smart_purchase_documents(self):
        for picking in self:
            purchase_orders = picking._get_related_purchase_orders()
            vendor_bills = picking._get_related_vendor_bills()
            payments = picking._get_related_payments()
            picking.smart_purchase_order_ids = purchase_orders
            picking.smart_purchase_order_count = len(purchase_orders)
            picking.smart_vendor_bill_ids = vendor_bills
            picking.smart_vendor_bill_count = len(vendor_bills)
            picking.smart_payment_ids = payments
            picking.smart_payment_count = len(payments)

    @api.depends("sale_id", "sale_id.invoice_ids")
    def _compute_smart_account_moves(self):
        for picking in self:
            account_moves = picking._get_related_account_moves()
            picking.smart_account_move_ids = account_moves
            picking.smart_account_move_count = len(account_moves)
