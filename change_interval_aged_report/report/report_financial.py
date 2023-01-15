# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

class ReportAccountAgedPartner(models.AbstractModel):
    _inherit = "account.aged.partner"

    def get_columns_name(self, options):
        ctx = self.env.context
        columns = super(ReportAccountAgedPartner, self).get_columns_name(options)
        if options.get('interval_custom'):
            for column in columns:
                if column.get('name') == '0 - 30':
                    column['name'] = str(options.get('interval')['1'][0]) +' - ' +str(options.get('interval')['1'][1])
                elif column.get('name') == '30 - 60':
                    column['name'] = str(options.get('interval')['2'][0]) +' - ' +str(options.get('interval')['2'][1])
                elif column.get('name') == '60 - 90':
                    column['name'] = str(options.get('interval')['3'][0]) +' - ' +str(options.get('interval')['3'][1])
                elif column.get('name') == '90 - 120':
                    column['name'] = str(options.get('interval')['4'][0]) +' - ' +str(options.get('interval')['4'][1])
        return columns


    @api.model
    def get_options(self, previous_options=None):
        res = super(ReportAccountAgedPartner, self).get_options(previous_options)
        ctx = self.env.context
        if ctx.get('interval_custom'):
            res['interval_custom'] = ctx.get('interval_custom')
            res['interval'] = ctx.get('interval')
        return res


    @api.model
    def get_lines(self, options, line_id=None):
        if not options.get('interval_custom'):
            return super(ReportAccountAgedPartner, self).get_lines(options, line_id)
        else:
            sign = -1.0 if self.env.context.get('aged_balance') else 1.0
            lines = []
            account_types = [self.env.context.get('account_type')]
            interval_custom = options['interval_custom']
            interval = options['interval']
            results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(interval_custom=interval_custom,interval=interval,include_nullified_amount=True)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)
            for values in results:
                if line_id and 'partner_%s' % (values['partner_id'],) != line_id:
                    continue
                vals = {
                    'id': 'partner_%s' % (values['partner_id'],),
                    'name': values['name'],
                    'level': 2,
                    'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                    'trust': values['trust'],
                    'unfoldable': True,
                    'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                }
                lines.append(vals)
                if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                    for line in amls[values['partner_id']]:
                        aml = line['line']
                        caret_type = 'account.move'
                        if aml.invoice_id:
                            caret_type = 'account.invoice.in' if aml.invoice_id.type in ('in_refund', 'in_invoice') else 'account.invoice.out'
                        elif aml.payment_id:
                            caret_type = 'account.payment'
                        vals = {
                            'id': aml.id,
                            'name': aml.move_id.name if aml.move_id.name else '/',
                            'caret_options': caret_type,
                            'level': 4,
                            'parent_id': 'partner_%s' % (values['partner_id'],),
                            'columns': [{'name': v} for v in [line['period'] == 6-i and self.format_value(sign * line['amount']) or '' for i in range(7)]],
                        }
                        lines.append(vals)
                    vals = {
                        'id': values['partner_id'],
                        'class': 'o_account_reports_domain_total',
                        'name': _('Total '),
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': self.format_value(sign * v)} for v in [values['direction'], values['4'], values['3'], values['2'], values['1'], values['0'], values['total']]],
                    }
                    lines.append(vals)
            if total and not line_id:
                total_line = {
                    'id': 0,
                    'name': _('Total'),
                    'class': 'total',
                    'level': 'None',
                    'columns': [{'name': self.format_value(sign * v)} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
                }
                lines.append(total_line)
            return lines



class ReportAgedPartnerBalance(models.AbstractModel):

    _inherit = 'report.account.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        ctx = self.env.context
        if not ctx.get('interval_custom'):
            return super(ReportAgedPartnerBalance, self)._get_partner_move_lines(account_type, date_from, target_move, period_length)
        else:
            # This method can receive the context key 'include_nullified_amount' {Boolean}
            # Do an invoice and a payment and unreconcile. The amount will be nullified
            # By default, the partner wouldn't appear in this report.
            # The context key allow it to appear
            periods = {}
            start = datetime.strptime(date_from, "%Y-%m-%d")
            
            name_interval_1 = str(self._context.get('interval')['1'][0]) +' - ' +str(self._context.get('interval')['1'][1])
            name_interval_2 = str(self._context.get('interval')['2'][0]) +' - ' +str(self._context.get('interval')['2'][1])
            name_interval_3 = str(self._context.get('interval')['3'][0]) +' - ' +str(self._context.get('interval')['3'][1])
            name_interval_4 = str(self._context.get('interval')['4'][0]) +' - ' +str(self._context.get('interval')['4'][1])
            name_interval_5 = ' +' +str(self._context.get('interval')['4'][1])

            stop_interval_1 = (start - relativedelta(days=self._context.get('interval')['1'][0])).strftime('%Y-%m-%d')
            start_interval_1 = (start - relativedelta(days=self._context.get('interval')['1'][1])).strftime('%Y-%m-%d')

            stop_interval_2 = (start - relativedelta(days=self._context.get('interval')['2'][0])).strftime('%Y-%m-%d')
            start_interval_2 = (start - relativedelta(days=self._context.get('interval')['2'][1])).strftime('%Y-%m-%d')

            stop_interval_3 = (start - relativedelta(days=self._context.get('interval')['3'][0])).strftime('%Y-%m-%d')
            start_interval_3 = (start - relativedelta(days=self._context.get('interval')['3'][1])).strftime('%Y-%m-%d')


            stop_interval_4 = (start - relativedelta(days=self._context.get('interval')['4'][0])).strftime('%Y-%m-%d')
            start_interval_4 = (start - relativedelta(days=self._context.get('interval')['4'][1])).strftime('%Y-%m-%d')

            stop_interval_5 = (start - relativedelta(days=self._context.get('interval')['4'][1]+1)).strftime('%Y-%m-%d')

            periods = {'4': {'name': name_interval_1, 'stop': stop_interval_1, 'start': start_interval_1}, 
                '3': {'name': name_interval_2, 'stop': stop_interval_2, 'start': start_interval_2}, 
                '2': {'name': name_interval_3, 'stop': stop_interval_3, 'start': start_interval_3}, 
                '1': {'name': name_interval_4, 'stop': stop_interval_4, 'start': start_interval_4}, 
                '0': {'name': name_interval_5, 'stop': stop_interval_5, 'start': False}}




            res = []
            total = []
            cr = self.env.cr
            company_ids = self.env.context.get('company_ids', (self.env.user.company_id.id,))
            move_state = ['draft', 'posted']
            if target_move == 'posted':
                move_state = ['posted']
            arg_list = (tuple(move_state), tuple(account_type))
            #build the reconciliation clause to see what partner needs to be printed
            reconciliation_clause = '(l.reconciled IS FALSE)'
            cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
            reconciled_after_date = []
            for row in cr.fetchall():
                reconciled_after_date += [row[0], row[1]]
            if reconciled_after_date:
                reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
                arg_list += (tuple(reconciled_after_date),)
            arg_list += (date_from, tuple(company_ids))
            query = '''
                SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
                FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
                WHERE (l.account_id = account_account.id)
                    AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND ''' + reconciliation_clause + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                ORDER BY UPPER(res_partner.name)'''
            cr.execute(query, arg_list)

            partners = cr.dictfetchall()
            # put a total of 0
            for i in range(7):
                total.append(0)

            # Build a string like (1,2,3) for easy use in SQL query
            partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
            lines = dict((partner['partner_id'] or False, []) for partner in partners)
            if not partner_ids:
                return [], [], []

            # This dictionary will store the not due amount of all partners
            undue_amounts = {}
            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND (COALESCE(l.date_maturity,l.date) > %s)\
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''
            cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in undue_amounts:
                    undue_amounts[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.amount
                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    undue_amounts[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': 6,
                    })

            # Use one query per period and store results in history (a list variable)
            # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
            history = []
            for i in range(5):
                args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
                dates_query = '(COALESCE(l.date_maturity,l.date)'

                if periods[str(i)]['start'] and periods[str(i)]['stop']:
                    dates_query += ' BETWEEN %s AND %s)'
                    args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
                elif periods[str(i)]['start']:
                    dates_query += ' >= %s)'
                    args_list += (periods[str(i)]['start'],)
                else:
                    dates_query += ' <= %s)'
                    args_list += (periods[str(i)]['stop'],)
                args_list += (date_from, tuple(company_ids))

                query = '''SELECT l.id
                        FROM account_move_line AS l, account_account, account_move am
                        WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                            AND (am.state IN %s)
                            AND (account_account.internal_type IN %s)
                            AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                            AND ''' + dates_query + '''
                        AND (l.date <= %s)
                        AND l.company_id IN %s'''
                cr.execute(query, args_list)
                partners_amount = {}
                aml_ids = cr.fetchall()
                aml_ids = aml_ids and [x[0] for x in aml_ids] or []
                for line in self.env['account.move.line'].browse(aml_ids):
                    partner_id = line.partner_id.id or False
                    if partner_id not in partners_amount:
                        partners_amount[partner_id] = 0.0
                    line_amount = line.balance
                    if line.balance == 0:
                        continue
                    for partial_line in line.matched_debit_ids:
                        if partial_line.max_date <= date_from:
                            line_amount += partial_line.amount
                    for partial_line in line.matched_credit_ids:
                        if partial_line.max_date <= date_from:
                            line_amount -= partial_line.amount

                    if not self.env.user.company_id.currency_id.is_zero(line_amount):
                        partners_amount[partner_id] += line_amount
                        lines[partner_id].append({
                            'line': line,
                            'amount': line_amount,
                            'period': i + 1,
                            })
                history.append(partners_amount)

            for partner in partners:
                if partner['partner_id'] is None:
                    partner['partner_id'] = False
                at_least_one_amount = False
                values = {}
                undue_amt = 0.0
                if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                    undue_amt = undue_amounts[partner['partner_id']]

                total[6] = total[6] + undue_amt
                values['direction'] = undue_amt
                if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True

                for i in range(5):
                    during = False
                    if partner['partner_id'] in history[i]:
                        during = [history[i][partner['partner_id']]]
                    # Adding counter
                    total[(i)] = total[(i)] + (during and during[0] or 0)
                    values[str(i)] = during and during[0] or 0.0
                    if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                        at_least_one_amount = True
                values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
                ## Add for total
                total[(i + 1)] += values['total']
                values['partner_id'] = partner['partner_id']
                if partner['partner_id']:
                    browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                    values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                    values['trust'] = browsed_partner.trust
                else:
                    values['name'] = _('Unknown Partner')
                    values['trust'] = False

                if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                    res.append(values)

            return res, total, lines
