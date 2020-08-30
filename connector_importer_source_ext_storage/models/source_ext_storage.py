# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields


class ExtStorageSourceMixin(models.AbstractModel):
    _name = 'import.source.ext.storage.mixin'
    _description = 'External Storage import source'
    _source_type = 'ExtStorage'

    storage_backend_id = fields.Many2one(
        "storage.backend", "Storage Backend", required=True
    )
    csv_path = fields.Char(required=True, help="Relative file path in the storage backend.")


class ExtStorageCSVSource(models.Model):
    _name = "import.source.ext.storage.csv"
    _inherit = [
        "import.source.csv",
        "import.source.ext.storage.mixin"
    ]

    @property
    def _config_summary_fields(self):
        _fields = super()._config_summary_fields
        return _fields + [
            "storage_backend_id",
        ]

    def _get_csv_reader_args(self):
        reader_args = super()._get_csv_reader_args()
        if self.storage_backend_id:
            reader_args["filedata"] = self.storage_backend_id._get_bin_data(reader_args.pop("filepath"))
        return reader_args