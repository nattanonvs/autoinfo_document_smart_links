from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    smart_credit_note_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_credit_notes",
    )
    smart_credit_note_count = fields.Integer(compute="_compute_smart_credit_notes")
    smart_debit_note_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_debit_notes",
    )
    smart_debit_note_count = fields.Integer(compute="_compute_smart_debit_notes")

    def _get_related_credit_notes(self):
        self.ensure_one()
        return self.invoice_ids.filtered(
            lambda move: move.state == "posted" and move.move_type == "out_refund"
        )

    def action_view_smart_credit_notes(self):
        self.ensure_one()
        credit_notes = self.smart_credit_note_ids
        action = {
            "type": "ir.actions.act_window",
            "name": "Credit Notes",
            "res_model": "account.move",
            "target": "current",
        }

        if not credit_notes:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", [])],
                }
            )
            return action

        action["domain"] = [("id", "in", credit_notes.ids)]
        if len(credit_notes) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "views": [(False, "form")],
                    "res_id": credit_notes.id,
                }
            )
            return action

        action["view_mode"] = "tree,form"
        return action

    def _get_related_debit_notes(self):
        self.ensure_one()
        move_model = self.env["account.move"]
        if "child_ids" not in move_model._fields:
            return move_model

        parent_invoices = self.invoice_ids.filtered(
            lambda move: move.state == "posted" and move.move_type == "out_invoice" and not move.dncn
            if "dncn" in move._fields
            else move.state == "posted" and move.move_type == "out_invoice"
        )
        debit_notes = parent_invoices.mapped("child_ids").filtered(lambda move: move.state == "posted")
        if "dncn" in move_model._fields:
            debit_notes = debit_notes.filtered(lambda move: move.dncn == "dn")
        return debit_notes

    def action_view_smart_debit_notes(self):
        self.ensure_one()
        debit_notes = self.smart_debit_note_ids
        action = {
            "type": "ir.actions.act_window",
            "name": "Debit Notes",
            "res_model": "account.move",
            "target": "current",
        }

        if not debit_notes:
            action.update(
                {
                    "view_mode": "tree,form",
                    "domain": [("id", "in", [])],
                }
            )
            return action

        action["domain"] = [("id", "in", debit_notes.ids)]
        if len(debit_notes) == 1:
            action.update(
                {
                    "view_mode": "form",
                    "views": [(False, "form")],
                    "res_id": debit_notes.id,
                }
            )
            return action

        action["view_mode"] = "tree,form"
        return action

    @api.depends("invoice_ids", "invoice_ids.move_type", "invoice_ids.state")
    def _compute_smart_credit_notes(self):
        for order in self:
            credit_notes = order._get_related_credit_notes()
            order.smart_credit_note_ids = credit_notes
            order.smart_credit_note_count = len(credit_notes)

    @api.depends("invoice_ids")
    def _compute_smart_debit_notes(self):
        for order in self:
            debit_notes = order._get_related_debit_notes()
            order.smart_debit_note_ids = debit_notes
            order.smart_debit_note_count = len(debit_notes)
