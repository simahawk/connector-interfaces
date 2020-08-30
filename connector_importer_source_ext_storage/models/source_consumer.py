# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ConsumerMixin(models.AbstractModel):
    _inherit = 'import.source.consumer.mixin'

    @api.model
    def _selection_source_ref_id(self):
        res = super()._selection_source_ref_id()
        return res + [
            ('import.source.extstorage', 'External Storage'),
        ]
