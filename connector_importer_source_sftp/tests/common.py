# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os

from odoo.addons.connector_importer.tests.common import BaseTestCase


class TestSourceCSVSFTPMixin(object):
    @classmethod
    def _setup_source_records(cls):
        cls.storage_backend = cls._get_storage_backend()
        cls.source = cls._create_source()

    @classmethod
    def _get_storage_backend(cls):
        backend = cls.env.ref("storage_backend.default_storage_backend")
        backend.write(
            {
                "backend_type": "sftp",
                "sftp_login": "foo",
                "sftp_password": "pass",
                "sftp_server": os.environ.get("SFTP_HOST", "localhost"),
                "sftp_port": os.environ.get("SFTP_PORT", "2222"),
                "directory_path": "upload",
            }
        )
        return backend

    @classmethod
    def _create_source(cls):
        source = cls.env["import.source.csv.sftp"].create(
            {
                "name": "test_sftp_source",
                "csv_delimiter": ",",
                "storage_id": cls.storage_backend.id,
                "sftp_path_input": "/input",
                "sftp_path_error": "/error",
                "sftp_path_success": "/success",
            }
        )
        source._onchance_csv_file()
        return source


class BaseTestSourceCSVSFTP(BaseTestCase, TestSourceCSVSFTPMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_source_records()

    def setUp(self):
        super().setUp()
        self._setup_components()

    def _get_component_modules(self):
        return super()._get_component_modules() + ["connector_importer_source_sftp"]
