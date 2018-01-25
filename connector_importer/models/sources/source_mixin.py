# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, tools

from ..utils.import_utils import gen_chunks


class ImportSourceConsumerdMixin(models.AbstractModel):
    _name = 'import.source.consumer.mixin'
    _description = 'Import source consumer'

    source_id = fields.Integer(
        string='Source ID',
        required=False,
        ondelete='cascade',
    )
    source_model = fields.Selection(
        string='Source type',
        selection='_selection_source_ref_id',
    )
    source_ref_id = fields.Reference(
        string='Source',
        compute='_compute_source_ref_id',
        selection='_selection_source_ref_id',
        store=True,
    )
    source_config_summary = fields.Html(
        compute='_compute_source_config_summary',
        readonly=True,
    )

    @api.multi
    @api.depends('source_model', 'source_id')
    def _compute_source_ref_id(self):
        for item in self:
            if not item.source_id or not item.source_model:
                continue
            item.source_ref_id = '{0.source_model},{0.source_id}'.format(item)

    @api.model
    @tools.ormcache('self')
    def _selection_source_ref_id(self):
        domain = [('model', '=like', 'import.source.%')]
        return [(r.model, r.name)
                for r in self.env['ir.model'].search(domain)
                if not r.model.endswith('mixin')]

    @api.multi
    @api.depends('source_ref_id', )
    def _compute_source_config_summary(self):
        for item in self:
            if not item.source_ref_id:
                continue
            item.source_config_summary = item.source_ref_id.config_summary

    @api.multi
    def open_source_config(self):
        self.ensure_one()
        action = self.env[self.source_model].get_formview_action()
        action.update({
            'views': [
                (self.env[self.source_model].get_config_view_id(), 'form'),
            ],
            'res_id': self.source_id,
            'target': 'new',
        })
        return action

    def get_source(self):
        return self.source_ref_id


class ImportSource(models.AbstractModel):
    _name = 'import.source'
    _description = 'Import source'
    _source_type = 'none'
    _reporter_model = ''

    name = fields.Char(
        compute=lambda self: self._source_type,
        readony=True,
    )
    chunk_size = fields.Integer(
        required=True,
        default=500,
        string='Chunks Size'
    )
    config_summary = fields.Html(
        compute='_compute_config_summary',
        readonly=True,
    )

    _config_summary_template = 'connector_importer.source_config_summary'
    _config_summary_fields = ('chunk_size', )

    @api.depends()
    def _compute_config_summary(self):
        template = self.env.ref(self._config_summary_template)
        for item in self:
            item.config_summary = template.render(item._config_summary_data())

    def _config_summary_data(self):
        info = []
        for fname in self._config_summary_fields:
            info.append((fname, self[fname]))
        return {
            'source': self,
            'summary_fields': self._config_summary_fields,
            'fields_info': self.fields_get(self._config_summary_fields),
        }

    @api.model
    def create(self, vals):
        res = super(ImportSource, self).create(vals)
        if self.env.context.get('active_model'):
            # update reference on consumer
            self.env[self.env.context['active_model']].browse(
                self.env.context['active_id']).source_id = res.id
        return res

    @api.multi
    def get_lines(self):
        self.ensure_one()
        # retrieve lines
        lines = self._get_lines()

        # sort them
        lines_sorted = self._sort_lines(lines)

        for i, chunk in enumerate(gen_chunks(lines_sorted,
                                  chunksize=self.chunk_size)):
            # get out of chunk iterator
            yield list(chunk)

    def _get_lines(self):
        raise NotImplementedError()

    def _sort_lines(self, lines):
        return lines

    def get_config_view_id(self):
        return self.env['ir.ui.view'].search([
            ('model', '=', self._name),
            ('type', '=', 'form')], limit=1).id

    def get_reporter(self):
        return self.env.get(self._reporter_model)
