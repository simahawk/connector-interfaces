# Copyright 2019 Camptocamp SA (<http://camptocamp.com>)
# @author: Sebastien Alix <sebastien.alix@camptocamp.com>
# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import os

from odoo import fields, models


# TODO: in the future, split this to a generic mixin not tied to CSV.
class ImportSourceCSVSFTP(models.Model):
    """Import source for CSV files on SFTP.
    """

    _name = "import.source.csv.sftp"
    _inherit = ["import.source.csv", "server.env.mixin"]
    _description = "CSV import source through SFTP"
    _source_type = "csv_sftp"

    # Overrided to get a store field for env purpose
    name = fields.Char(compute=False)
    storage_id = fields.Many2one(
        string="Storage backend",
        comodel_name="storage.backend",
        required=True,
        ondelete="restrict",
        domain=[("backend_type", "=", "sftp")],
    )
    sftp_path_input = fields.Char(
        string="SFTP Folder path - Input",
        required=True,
        default="pending",
        help=("Where to find CSV files to import. Eg: `/mnt/csv/res_partner/pending/`"),
    )
    sftp_path_error = fields.Char(
        string="SFTP Folder path - Error",
        required=True,
        default="error",
        help=(
            "Where to move CSV files if errors occurred "
            "when `Move file after import` is enabled. "
            "Eg: `/mnt/csv/res_partner/error/`"
        ),
    )
    sftp_path_success = fields.Char(
        string="SFTP Folder path - Success",
        required=True,
        default="done",
        help=(
            "Where to move CSV files if no errors occurred "
            "when `Move file after import` is enabled. "
            "Eg: `/mnt/csv/res_partner/done/`"
        ),
    )
    sftp_filename_pattern = fields.Char(
        string="SFTP Filename pattern",
        required=True,
        default=r".*\.csv$",
        help="Regex pattern to match CSV file names.",
    )
    move_file_after_import = fields.Boolean(
        help="If enabled, the file processed will be moved to success/error folders "
        "depending on the result of the import"
    )

    # FIXME: screws tests
    # @property
    # def _server_env_fields(self):
    #     return {
    #         "sftp_path_input": {},
    #         "sftp_path_error": {},
    #         "sftp_path_success": {},
    #         "sftp_filename_pattern": {},
    #         "move_file_after_import": {},
    #     }

    @property
    def _config_summary_fields(self):
        _fields = super()._config_summary_fields
        _fields.extend(
            [
                "storage_id",
                "sftp_path_input",
                "sftp_filename_pattern",
                "move_file_after_import",
            ]
        )
        if self.move_file_after_import:
            _fields.extend(["sftp_path_error", "sftp_path_success"])
        return _fields

    def _get_lines(self):
        """Get lines from file on sftp server.

        Gets file from SFTP server and passes it to csv_file field to keep
        standard csv source machinery. Overwrites it on every run, so the file
        pattern should be defined in sftp_filename_pattern field.
        """
        self.csv_filename, self.csv_file = self._sftp_get_file()
        return super()._get_lines()

    def _sftp_get_file(self):
        """Try to read the first file matching the pattern.

        Return a tuple (filename, filedata).
        """
        filepaths = self._sftp_find_files()
        filename = None
        filedata = None
        if filepaths:
            filedata = self._sftp_read_file(filepaths[0])
            filename = os.path.basename(filepaths[0])
        return filename, filedata

    def _sftp_find_files(self):
        return self.storage_id._find_files(
            self.sftp_filename_pattern, relative_path=self.sftp_path_input
        )

    def _sftp_read_file(self, filepath):
        return self.storage_id._get_b64_data(filepath)

    def _sftp_filepath(self):
        base_path = (self.sftp_path_input or "").rstrip("/ ")
        return os.path.join(base_path, self.csv_filename.strip("/ "))
