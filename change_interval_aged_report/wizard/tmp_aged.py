
from datetime import datetime, timedelta
from itertools import groupby
import json
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import ast




class TmpAgedReportWizard(models.TransientModel):
    _name = "tmp.aged.report.wizard"


    name = fields.Char("Name")
    interval_1_1 = fields.Integer("Interval 1-1",required=1, default="0")
    interval_1_2 = fields.Integer("Interval 1-2",required=1, default="30")
    interval_2_1 = fields.Integer("Interval 2-1",required=1, default="31")
    interval_2_2 = fields.Integer("Interval 2-2",required=1, default="60")
    interval_3_1 = fields.Integer("Interval 3-1",required=1, default="61")
    interval_3_2 = fields.Integer("Interval 3-2",required=1, default="90")
    interval_4_1 = fields.Integer("Interval 4-1",required=1, default="91")
    interval_4_2 = fields.Integer("Interval 4-2",required=1, default="120")




    def process(self):
        name = 'Aged '+self.name
        model_report = 'account.aged.'+self.name.lower()
        interval_1_1 = self.interval_1_1
        interval_1_2 = self.interval_1_2

        interval_2_1 = self.interval_2_1
        interval_2_2 = self.interval_2_2

        interval_3_1 = self.interval_3_1
        interval_3_2 = self.interval_3_2

        interval_4_1 = self.interval_4_1
        interval_4_2 = self.interval_4_2

        if interval_1_2 <= 0:
            raise ValidationError("Please input the correct interval value.\nThe interval value must be greater than 0")
        if interval_2_1 <= 0 or interval_2_2 <= 0:
            raise ValidationError("Please input the correct interval value.\nThe interval value must be greater than 0")
        if interval_3_1 <= 0 or interval_3_2 <= 0:
            raise ValidationError("Please input the correct interval value.\nThe interval value must be greater than 0")
        if interval_4_1 <= 0 or interval_4_2 <= 0:
            raise ValidationError("Please input the correct interval value.\nThe interval value must be greater than 0")

        l = [interval_1_1,interval_1_2,interval_2_1,interval_2_2,interval_3_1,interval_3_2,interval_4_1,interval_4_2]

        if not all(l[i] <= l[i+1] for i in range(len(l)-1)):
            raise ValidationError("Please input the interval value in order from smallest to largest")


        interval = {
                        1:[interval_1_1,interval_1_2],
                        2:[interval_2_1,interval_2_2],
                        3:[interval_3_1,interval_3_2],
                        4:[interval_4_1,interval_4_2],
                    }
        return {
            'name': name ,
            'type': 'ir.actions.client',
            'tag': 'account_report',
            'context':{'model': model_report,'interval':interval}
        }
