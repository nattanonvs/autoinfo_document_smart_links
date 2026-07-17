from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    smart_sale_order_ids = fields.Many2many(
        "sale.order",
        compute="_compute_smart_partner_links",
    )
    smart_sale_order_count = fields.Integer(compute="_compute_smart_partner_links")
    smart_delivery_ids = fields.Many2many(
        "stock.picking",
        compute="_compute_smart_partner_links",
    )
    smart_delivery_count = fields.Integer(compute="_compute_smart_partner_links")
    smart_customer_invoice_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_partner_links",
    )
    smart_customer_invoice_count = fields.Integer(
        compute="_compute_smart_partner_links"
    )
    smart_customer_credit_note_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_partner_links",
    )
    smart_customer_credit_note_count = fields.Integer(
        compute="_compute_smart_partner_links"
    )
    smart_customer_payment_ids = fields.Many2many(
        "account.payment",
        compute="_compute_smart_partner_links",
    )
    smart_customer_payment_count = fields.Integer(
        compute="_compute_smart_partner_links"
    )
    smart_purchase_order_ids = fields.Many2many(
        "purchase.order",
        compute="_compute_smart_partner_links",
    )
    smart_purchase_order_count = fields.Integer(compute="_compute_smart_partner_links")
    smart_vendor_bill_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_partner_links",
    )
    smart_vendor_bill_count = fields.Integer(compute="_compute_smart_partner_links")
    smart_payment_ids = fields.Many2many(
        "account.payment",
        compute="_compute_smart_partner_links",
    )
    smart_payment_count = fields.Integer(compute="_compute_smart_partner_links")

    def _get_related_purchase_orders(self):
        self.ensure_one()
        return self.env["purchase.order"].search([("partner_id", "=", self.id)])

    def _get_related_sale_orders(self):
        self.ensure_one()
        return self.env["sale.order"].search([("partner_id", "=", self.id)])

    def _get_related_deliveries(self):
        self.ensure_one()
        return self._get_related_sale_orders().mapped("picking_ids").filtered(
            lambda picking: picking.picking_type_code == "outgoing"
            and picking.state != "cancel"
        )

    def _get_related_vendor_bills(self):
        self.ensure_one()
        return self.env["account.move"].search(
            [
                ("partner_id", "=", self.id),
                ("move_type", "=", "in_invoice"),
                ("state", "!=", "cancel"),
            ]
        )

    def _get_related_customer_invoices(self):
        self.ensure_one()
        return self.env["account.move"].search(
            [
                ("partner_id", "=", self.id),
                ("move_type", "=", "out_invoice"),
                ("state", "!=", "cancel"),
            ]
        )

    def _get_related_customer_credit_notes(self):
        self.ensure_one()
        return self.env["account.move"].search(
            [
                ("partner_id", "=", self.id),
                ("move_type", "=", "out_refund"),
                ("state", "!=", "cancel"),
            ]
        )

    def _get_related_customer_payments(self, customer_moves=None):
        self.ensure_one()
        moves = customer_moves
        if moves is None:
            moves = (
                self._get_related_customer_invoices()
                | self._get_related_customer_credit_notes()
            )
        if not moves:
            return self.env["account.payment"]
        return moves._get_reconciled_payments().filtered(
            lambda payment: payment.state != "cancel"
        )

    def _get_related_payments(self):
        self.ensure_one()
        bills = self._get_related_vendor_bills()
        if not bills:
            return self.env["account.payment"]
        return bills._get_reconciled_payments().filtered(
            lambda payment: payment.state != "cancel"
        )

    def _build_smart_action(self, records, res_model, name):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": res_model,
            "target": "current",
            "domain": [("id", "in", records.ids)],
        }
        if len(records) == 1:
            action.update(
                {"view_mode": "form", "views": [(False, "form")], "res_id": records.id}
            )
            return action
        action["view_mode"] = "tree,form"
        return action

    def action_view_smart_purchase_orders(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_purchase_order_ids,
            "purchase.order",
            "Purchase Orders",
        )

    def action_view_smart_sale_orders(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_sale_order_ids,
            "sale.order",
            "Sale Orders",
        )

    def action_view_smart_deliveries(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_delivery_ids,
            "stock.picking",
            "Deliveries",
        )

    def action_view_smart_vendor_bills(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_vendor_bill_ids,
            "account.move",
            "Vendor Bills",
        )

    def action_view_smart_customer_invoices(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_customer_invoice_ids,
            "account.move",
            "Customer Invoices",
        )

    def action_view_smart_customer_credit_notes(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_customer_credit_note_ids,
            "account.move",
            "Customer Credit Notes",
        )

    def action_view_smart_customer_payments(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_customer_payment_ids,
            "account.payment",
            "Customer Payments",
        )

    def action_view_smart_payments(self):
        self.ensure_one()
        return self._build_smart_action(
            self.smart_payment_ids,
            "account.payment",
            "Payments",
        )

    def _compute_smart_partner_links(self):
        for partner in self:
            sale_orders = partner._get_related_sale_orders()
            customer_invoices = partner._get_related_customer_invoices()
            customer_credit_notes = partner._get_related_customer_credit_notes()
            customer_moves = customer_invoices | customer_credit_notes
            customer_payments = partner._get_related_customer_payments(customer_moves)
            deliveries = sale_orders.mapped("picking_ids").filtered(
                lambda picking: picking.picking_type_code == "outgoing"
                and picking.state != "cancel"
            )
            purchase_orders = partner._get_related_purchase_orders()
            vendor_bills = partner._get_related_vendor_bills()
            payments = partner._get_related_payments()
            partner.smart_sale_order_ids = sale_orders
            partner.smart_sale_order_count = len(sale_orders)
            partner.smart_delivery_ids = deliveries
            partner.smart_delivery_count = len(deliveries)
            partner.smart_purchase_order_ids = purchase_orders
            partner.smart_purchase_order_count = len(purchase_orders)
            partner.smart_customer_invoice_ids = customer_invoices
            partner.smart_customer_invoice_count = len(customer_invoices)
            partner.smart_customer_credit_note_ids = customer_credit_notes
            partner.smart_customer_credit_note_count = len(customer_credit_notes)
            partner.smart_customer_payment_ids = customer_payments
            partner.smart_customer_payment_count = len(customer_payments)
            partner.smart_vendor_bill_ids = vendor_bills
            partner.smart_vendor_bill_count = len(vendor_bills)
            partner.smart_payment_ids = payments
            partner.smart_payment_count = len(payments)
