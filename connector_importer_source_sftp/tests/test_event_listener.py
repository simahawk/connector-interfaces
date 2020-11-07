# Copyright 2020 ACSONE SA/NV (<http://acsone.eu>)
# @author: Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import io

import mock

from odoo.tools import mute_logger

from .common import SFTPSourceSavepointComponentRegistryCase

MOD_PATH = "odoo.addons.connector_importer_source_sftp"
EVENT_LISTENER_PATH = (
    MOD_PATH + ".components.event_listeners.SFTPSourceImportRecordsetEventListener"
)
SOURCE_MODEL_PATH = MOD_PATH + ".models.source_csv_sftp.ImportSourceCSVSFTP"


class TestRecordImporterFinishedEvent(SFTPSourceSavepointComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fake_lines = cls._fake_lines(cls, 10, keys=("id", "fullname"))

    def setUp(self):
        super().setUp()
        self._setup_components()
        # Not sure why but this write gets lost if done in setUpClass :/
        # Probably depends on server env override?
        # self.source.write(
        #     {
        #         "sftp_path_input": "input",
        #         "sftp_path_error": "error",
        #         "sftp_path_success": "success",
        #     }
        # )
        self.recordset.write(
            {"source_model": "import.source.csv.sftp", "source_id": self.source.id}
        )
        self.record = self.env["import.record"].create(
            {"recordset_id": self.recordset.id}
        )

    def _get_components(self):
        from odoo.addons.connector_importer.tests.fake_components import (
            PartnerRecordImporter,
            PartnerMapper,
        )

        return [PartnerRecordImporter, PartnerMapper]

    def _test_result(self, expected_counters):
        report = self.recordset.get_report()
        for k, v in expected_counters.items():
            self.assertEqual(len(report["res.partner"][k]), v)

    def _sftp_get_file_patch(self, *args):
        filecontent = self.load_filecontent(
            "connector_importer", "tests/fixtures/csv_source_test1.csv", mode="rb"
        )
        with io.BytesIO(filecontent) as file_obj:
            return ("filename.csv", base64.b64encode(file_obj.read()))

    @mute_logger("[importer]")
    @mock.patch(EVENT_LISTENER_PATH + "._add_after_commit_hook")
    def test_importer_create_move_disabled(self, add_after_commit_hook_mocked):
        with mock.patch(
            SOURCE_MODEL_PATH + "._sftp_get_file", self._sftp_get_file_patch
        ):
            chunk = tuple(self.source._get_lines())
            self.record.set_data(chunk)
            self.record.run_import()
            self._test_result({"created": 5, "errored": 0, "updated": 0, "skipped": 0})
        # source is not configured for moving files
        self.assertFalse(self.source.move_file_after_import)
        add_after_commit_hook_mocked.assert_not_called()

    @mute_logger("[importer]")
    @mock.patch(EVENT_LISTENER_PATH + "._add_after_commit_hook")
    def test_importer_create_move_enabled_success(self, mocked_method):
        self.source.move_file_after_import = True
        with mock.patch(
            SOURCE_MODEL_PATH + "._sftp_get_file", self._sftp_get_file_patch
        ):
            chunk = tuple(self.source._get_lines())
            self.record.set_data(chunk)
            self.record.run_import()
            self._test_result({"created": 5, "errored": 0, "updated": 0, "skipped": 0})
        mocked_method.assert_called_with(
            self.source.storage_id._move_files, "input/filename.csv", "success"
        )

    @mute_logger("[importer]")
    @mock.patch(EVENT_LISTENER_PATH + "._add_after_commit_hook")
    def test_importer_create_move_enabled_fail(self, mocked_method):
        self.source.move_file_after_import = True
        with mock.patch(
            SOURCE_MODEL_PATH + "._sftp_get_file", self._sftp_get_file_patch
        ):
            chunk = tuple(self.source._get_lines())
            self.record.set_data(chunk)
            self.record.with_context(
                _test_break_import="Ops, value XYZ is not valid"
            ).run_import()
            self._test_result({"created": 0, "errored": 5, "updated": 0, "skipped": 0})
        mocked_method.assert_called_with(
            self.source.storage_id._move_files, "input/filename.csv", "error"
        )

    @mute_logger("[importer]")
    @mock.patch(EVENT_LISTENER_PATH + "._add_after_commit_hook")
    def test_importer_create_move_enabled_fail_error_report(self, mocked_method):
        self.source.move_file_after_import = True
        self.source.send_back_error_report = True
        with mock.patch(
            SOURCE_MODEL_PATH + "._sftp_get_file", self._sftp_get_file_patch
        ):
            chunk = tuple(self.source._get_lines())
            self.record.set_data(chunk)
            with mock.patch.object(type(self.source.storage_id), "add") as mocked_add:
                self.record.with_context(
                    _test_break_import="Ops, value XYZ is not valid"
                ).run_import()
            self._test_result({"created": 0, "errored": 5, "updated": 0, "skipped": 0})
        mocked_method.assert_called_with(
            self.source.storage_id._move_files, "input/filename.csv", "error"
        )
        mocked_add.assert_called_with(
            "error/filename.report.csv", self.recordset.report_file, binary=False
        )
