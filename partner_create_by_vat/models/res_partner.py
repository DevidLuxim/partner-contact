# -*- coding: utf-8 -*-
# ©  2015 Forest and Biomass Services Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp import api, models, _
from openerp.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    from stdnum.eu.vat import check_vies
except ImportError:
    _logger.debug("Cannot import check_vies method from python stdnum.")


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _get_vies_data(self, vat):
        res = {}
        vat = vat.strip().upper()
        vat_country, vat_number = self._split_vat(vat)
        result = check_vies(vat)
        # Raise error if partner is not listed on Vies
        if result.name is None:
            raise ValidationError(_("The partner is not listed on Vies "
                                    "Webservice."))
        res['vat'] = vat
        res['vat_subjected'] = result.valid
        # Update partner name if listed on VIES
        if result.name != '---':
            res['name'] = result.name.upper()
        # Update partner address if listed on VIES
        country = self.env['res.country'].search(
            [('code', 'ilike', vat_country)])
        if country:
            res['country_id'] = country[0].id
        if result.address != '---':
            strng = \
                 result.address.replace('\n', ' ').replace('\r', '').title()
            if res['country_id'] ==110:
                strng = \
                    result.address.title()
                SubstrngEnd =strng.find('\n')
                res['street'] = strng[:SubstrngEnd]
                strng = strng[SubstrngEnd:]
                res['zip'] =strng[:6]
                strng = strng [7:]
                res['street2'] = None
                res['city'] = strng [: len(strng)-4]
            else:
                if res['country_id'] ==201 and (strng.count(',') == 0 or strng.count(',') > 2):
                    res['street'] = strng
                    res['zip'] = None
                    res['city'] = None
                    res['street2'] = None
                elif strng.count(',') == 1:
                    SubstrngEnd = strng.find(',')
                    res['street'] = strng[:SubstrngEnd]
                    strng = strng[SubstrngEnd + 2:]
                    SubstrngEnd = strng.find(' ')
                    res['street2'] = None
                    res['zip'] = strng[:SubstrngEnd]
                    res['city'] = strng[SubstrngEnd + 1:]
                elif strng.count(',') == 2:
                    SubstrngEnd = strng.find(',')
                    res['street'] = strng[:SubstrngEnd]
                    strng = strng[SubstrngEnd + 2:]
                    SubstrngEnd = strng.find(',')
                    res['street2'] = strng[:SubstrngEnd]
                    strng = strng[SubstrngEnd + 2:]
                    SubstrngEnd = strng.find(' ')
                    res['zip'] = strng[:SubstrngEnd]
                    res['city'] = strng[SubstrngEnd + 1:]
                    if res['street2'] == res['city']:
                        res['street2'] = None

                # konec unesene kode
                # Get country by country code
        return res

    @api.multi
    def vat_change(self, value):
        res = super(ResPartner, self).vat_change(value)
        # Update fields with the values available in the upper method
        # Skip required name error
        with self.env.do_in_onchange():
            if value:
                result = self._get_vies_data(value)
                res['value'].update(result)
        return res

    @api.one
    def get_vies_data_from_vat(self):
        if self.vat:
            res = self._get_vies_data(self.vat)
            self.update(res)
