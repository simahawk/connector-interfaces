# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api

from ..utils.import_utils import CSVReader, guess_csv_metadata


class CSVSource(models.Model):
    _name = 'import.source.csv'
    _inherit = 'import.source'
    _description = 'CSV import source'
    _source_type = 'csv'
    _reporter_model = 'reporter.csv'

    csv_file = fields.Binary('CSV file')
    # use these to load file from an FS path
    csv_filename = fields.Char('CSV filename')
    csv_filesize = fields.Char(
        string='CSV filesize',
        compute='_compute_csv_filesize',
        readonly=True,
    )
    # This is for scheduled import via FS path (FTP, sFTP, etc)
    csv_path = fields.Char('CSV path')
    csv_delimiter = fields.Char(
        string='CSV delimiter',
        default=';',
    )
    csv_quotechar = fields.Char(
        string='CSV quotechar',
        default='"',
    )

    @property
    def _config_summary_fields(self):
        _fields = super()._config_summary_fields
        return _fields + (
            'csv_filename', 'csv_filesize',
            'csv_delimiter', 'csv_quotechar',
        )

    @api.onchange('csv_file')
    def _onchance_csv_file(self):
        if self.csv_file:
            meta = guess_csv_metadata(self.csv_file.decode('base64'))
            if meta:
                self.csv_delimiter = meta['delimiter']
                self.csv_quotechar = meta['quotechar']

    def _filesize_human(self, size, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(size) < 1024.0:
                return "%3.1f%s%s" % (size, unit, suffix)
            size /= 1024.0
        return "%.1f%s%s" % (size, 'Y', suffix)

    @api.depends('csv_file')
    def _compute_csv_filesize(self):
        for item in self:
            if item.csv_file:
                item.csv_filesize = self._filesize_human(
                    len(item.csv_file.decode('base64')))

    def _get_lines(self):
        # read CSV
        reader_args = {
            'delimiter': self.csv_delimiter,
        }
        if self.csv_path:
            # TODO: join w/ filename
            reader_args['filepath'] = self.csv_path
        else:
            reader_args['filedata'] = self.csv_file

        reader = CSVReader(**reader_args)
        return reader.read_lines()

    # TODO: this stuff is now unrelated from backend version must be refactored
    # # handy fields to make the example attachment
    # # downloadable within recordset view
    # example_file_xmlid = fields.Char()
    # example_file_url = fields.Char(
    #     string='Download example file',
    #     compute='_compute_example_file_url',
    #     readonly=True,
    # )
    #
    # def _get_example_attachment(self):
    #     # You can define example file by creating attachments
    #     # with an xmlid matching the import type/key
    #     # `connector_importer.example_file_$version_key`
    #     if not self.backend_id.version or not self.import_type_id:
    #         return
    #     xmlid = self.example_file_xmlid
    #     if not xmlid:
    #         xmlid = u'connector_importer.examplefile_{}_{}'.format(
    #             self.backend_id.version.replace('.', '_'),
    #             self.import_type_id.key)
    #     return self.env.ref(xmlid, raise_if_not_found=0)
    #
    # @api.depends('backend_id.version', 'import_type_id', 'example_file_xmlid')
    # def _compute_example_file_url(self):
    #     att = self._get_example_attachment()
    #     if att:
    #         self.example_file_url = u'/web/content/{}/{}'.format(
    #             att.id, att.name)
