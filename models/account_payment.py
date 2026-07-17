from odoo import api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    smart_bill_ids = fields.Many2many(
        "account.move",
        compute="_compute_smart_bill_links",
    )
    smart_bill_count = fields.Integer(compute="_compute_smart_bill_links")

    def _get_related_bills(self):
        self.ensure_one()
        payable_lines = self.move_id.line_ids.filtered(
            lambda line: line.account_id.internal_type in ("receivable", "payable")
        )
        counterpart_lines = (
            payable_lines.mapped("matched_debit_ids.debit_move_id")
            | payable_lines.mapped("matched_credit_ids.credit_move_id")
        ).filtered(lambda line: line.move_id != self.move_id)
        return counterpart_lines.mapped("move_id").filtered(
            lambda move: move.state != "cancel"
            and move.move_type in ("in_invoice", "in_refund")
        )

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

    def action_view_smart_bills(self):
        self.ensure_one()
        return self._build_smart_action(self.smart_bill_ids, "account.move", "Bills")

    @api.depends(
        "move_id.line_ids.account_id.internal_type",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.move_type",
        "move_id.line_ids.matched_debit_ids.debit_move_id.move_id.state",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.move_type",
        "move_id.line_ids.matched_credit_ids.credit_move_id.move_id.state",
    )
    def _compute_smart_bill_links(self):
        for payment in self:
            bills = payment._get_related_bills()
            payment.smart_bill_ids = bills
            payment.smart_bill_count = len(bills)
