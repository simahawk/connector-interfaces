# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.connector_importer.tests.common import BaseTestCase, _load_filecontent
import mock


class TestExtStorageSource(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.storage_backend = cls.env.ref("storage_backend.default_storage_backend")
        cls.source = cls._create_source()

    def _fake_data(self):
        return _load_filecontent(
            "connector_importer_source_ext_storage", "tests/fixtures/csv_source_test1.csv", mode="rb"
        )

    @classmethod
    def _create_source(cls):
        return cls.env['import.source.ext.storage.csv'].create({
            'storage_backend_id': cls.storage_backend.id,
            'csv_path': 'tests/fixtures/csv_source_test1.csv',
            'csv_delimiter': ',',
        })

    def test_source_get_lines(self):
        source = self.source
        with mock.patch.object(
            self.storage_backend.__class__, "_get_bin_data"
        ) as mocked:
            mocked.return_value = self._fake_data()
            lines = list(source._get_lines())
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0]["fullname"], "Marty McFly")
