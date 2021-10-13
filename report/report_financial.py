# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain


class ReportAccountAgedPartner(models.AbstractModel):
    _inherit = "account.aged.partner"

    @api.model
    def _get_query_period_table(self, options):
        ''' Compute the periods to handle in the report.
        E.g. Suppose date = '2019-01-09', the computed periods will be:

        Name                | Start         | Stop
        --------------------------------------------
        As of 2019-01-09    | 2019-01-09    |
        1 - 30              | 2018-12-10    | 2019-01-08
        31 - 60             | 2018-11-10    | 2018-12-09
        61 - 90             | 2018-10-11    | 2018-11-09
        91 - 120            | 2018-09-11    | 2018-10-10
        Older               |               | 2018-09-10

        Then, return the values as an sql floating table to use it directly in queries.

        :return: A floating sql query representing the report's periods.
        '''
        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        date_str = options['date']['date_to']
        date = fields.Date.from_string(date_str)
        if self._context.get('interval'):
            interval_1_1 = self._context.get('interval')['1'][0]
            interval_1_2 = self._context.get('interval')['1'][1]

            interval_2_1 = self._context.get('interval')['2'][0]
            interval_2_2 = self._context.get('interval')['2'][1]

            interval_3_1 = self._context.get('interval')['3'][0]
            interval_3_2 = self._context.get('interval')['3'][1]

            interval_4_1 = self._context.get('interval')['4'][0]
            interval_4_2 = self._context.get('interval')['4'][1]

            period_values = [
                (False,                  date_str),
                (minus_days(date,  interval_1_1),    minus_days(date, interval_1_2)),
                (minus_days(date, interval_2_1),   minus_days(date, interval_2_2)),
                (minus_days(date, interval_3_1),   minus_days(date, interval_3_2)),
                (minus_days(date, interval_4_1),   minus_days(date, interval_4_2)),
                (minus_days(date, interval_4_2+1),  False),
            ]
        else:
            period_values = [
                (False,                  date_str),
                (minus_days(date, 1),    minus_days(date, 30)),
                (minus_days(date, 31),   minus_days(date, 60)),
                (minus_days(date, 61),   minus_days(date, 90)),
                (minus_days(date, 91),   minus_days(date, 120)),
                (minus_days(date, 121),  False),
            ]

        period_table = ('(VALUES %s) AS period_table(date_start, date_stop, period_index)' %
                        ','.join("(%s, %s, %s)" for i, period in enumerate(period_values)))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(period_values)
        ))
        return self.env.cr.mogrify(period_table, params).decode(self.env.cr.connection.encoding)



    def _field_column(self, field_name, sortable=False, name=None):
        """Build a column based on a field.

        The type of the field determines how it is displayed.
        The column's title is the name of the field.
        :param field_name: The name of the fields.Field to use
        :param sortable: Allow the user to sort data based on this column
        :param name: Use a specific name for display.
        """
        classes = ['text-nowrap']
        def getter(v): return v.get(field_name, '')
        if self._fields[field_name].type in ['monetary', 'float']:
            classes += ['number']
            def formatter(v): return self.format_value(v)
        elif self._fields[field_name].type in ['char']:
            classes += ['text-center']
            def formatter(v): return v
        elif self._fields[field_name].type in ['date']:
            classes += ['date']
            def formatter(v): return format_date(self.env, v)
        if self._context.get('interval'):
            if field_name == 'period1':
                name = str(self._context.get('interval')['1'][0]) + ' - ' + str(self._context.get('interval')['1'][1])
            if field_name == 'period2':
                name = str(self._context.get('interval')['2'][0]) + ' - ' + str(self._context.get('interval')['2'][1])
            if field_name == 'period3':
                name = str(self._context.get('interval')['3'][0]) + ' - ' + str(self._context.get('interval')['3'][1])
            if field_name == 'period4':
                name = str(self._context.get('interval')['4'][0]) + ' - ' + str(self._context.get('interval')['4'][1])
        return self._custom_column(name=name or self._fields[field_name].string,
                                   getter=getter,
                                   formatter=formatter,
                                   classes=classes,
                                   sortable=sortable)
