# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
class Notascredito(models.Model):
    _inherit="account.invoice"
    
    @api.one
    def _compute_get_note(self):
        if self.type == 'out_invoice':
	    inv_obj_refund= self.env["account.invoice"].search([('type', '=', 'out_refund'), ('origin','=',self.number)])
	    if inv_obj_refund:
                for refund in inv_obj_refund:
                    if refund.state == 'open' or refund.state == 'paid':
                        self.amount_credit_note += refund.amount_total

    @api.one
    def _compute_check(self):
        if self.state == 'open' and self.type == 'out_invoice':
	    if self.residual == 0:
                query = """ UPDATE account_invoice 
					    SET state='paid'
                   			WHERE id = %s
                			"""
        	self._cr.execute(query, (self.id,))
		self.check_status= True

    @api.one
    @api.depends("residual","amount_total")
    def _amount_paid(self):
	if self.residual >= 0:	
            self.amount_paid = self.amount_total - self.residual - self.amount_credit_note	
	

    amount_credit_note = fields.Float("Credit note amount", domain=[('type','=','out_invoice')], compute='_compute_get_note')
    check_status = fields.Boolean("Invoice paid",  compute='_compute_check')
    amount_paid = fields.Float('Amount paid', help="Is residual - amount credit note",compute='_amount_paid')
	

    @api.multi
    def get_action_credit_note(self):
        view_id = self.env.ref("credit.note.credit_note_view_invoice", False)
	for inv in self:
            return {
                'name':_("Credi Note Customer"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'credit.note',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]',
        }

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line.price_subtotal',
        'move_id.line_id.account_id.type',
        'move_id.line_id.amount_residual',
        # Fixes the fact that move_id.line_id.amount_residual, being not stored and old API, doesn't trigger recomputation
        'move_id.line_id.reconcile_id',
        'move_id.line_id.amount_residual_currency',
        'move_id.line_id.currency_id',
        'move_id.line_id.reconcile_partial_id.line_partial_ids.invoice.type',
    )
    # An invoice's residual amount is the sum of its unreconciled move lines and,
    # for partially reconciled move lines, their residual amount divided by the
    # number of times this reconciliation is used in an invoice (so we split
    # the residual amount between all invoice)
    def _compute_residual(self):
        self.residual = 0.0
        # Each partial reconciliation is considered only once for each invoice it appears into,
        # and its residual amount is divided by this number of invoices
        partial_reconciliations_done = []
        for line in self.sudo().move_id.line_id:
            if line.account_id.type not in ('receivable', 'payable'):
                continue
            if line.reconcile_partial_id and line.reconcile_partial_id.id in partial_reconciliations_done:
                continue
            # Get the correct line residual amount
            if line.currency_id == self.currency_id:
                line_amount = line.amount_residual_currency if line.currency_id else line.amount_residual
            else:
                from_currency = line.company_id.currency_id.with_context(date=line.date)
                line_amount = from_currency.compute(line.amount_residual, self.currency_id)
            # For partially reconciled lines, split the residual amount
            if line.reconcile_partial_id:
                partial_reconciliation_invoices = set()
                for pline in line.reconcile_partial_id.line_partial_ids:
                    if pline.invoice and self.type == pline.invoice.type:
                        partial_reconciliation_invoices.update([pline.invoice.id])
                line_amount = self.currency_id.round(line_amount / len(partial_reconciliation_invoices))
                partial_reconciliations_done.append(line.reconcile_partial_id.id)
            self.residual += line_amount

	#Resiaul calculated for credit note
        if self.type == 'out_invoice':
            inv_obj_refund= self.env["account.invoice"].search([('type', '=', 'out_refund'), ('origin','=',self.number)])
            if inv_obj_refund:
                for refund in inv_obj_refund:
                    if refund.state == 'open' or refund.state== 'paid':
                        # Se hizo de esta forma ya que el campo residual tiene resultado cero
                        self.residual = self.residual - refund.amount_total
      
        self.residual = max(self.residual, 0.0)


