# Author: Simone Orsi
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo.addons.component.core import Component
# from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import DONE


_logger = logging.getLogger(__name__)


class ImporterListener(Component):
    _name = 'record.importer.event.listener'
    _inherit = 'base.event.listener'
    _collection = 'import.backend'

    def on_record_chunk_finished(
            self, record, is_last_importer=False, options=None):
        """Event triggered on import.record chunk done.

        :param record: current import.record browse record
        :param is_last_importer: True if the importer is the last one.

        You can have different importers running for the same recordset
        (ie: you have to import partners and users w/ the same source).
        So, if the trigger of the event is the last importer in the process
        this flag is set to true.

        :param options: dictionary of options to propagate from the importer

        You can hook here if you want to do something else
        when a chunk as been processed.
        """
        pass


class ImporterListener(Component):
    _name = 'recordset.importer.event.listener'
    _inherit = 'base.event.listener'
    _collection = 'import.backend'

    def on_recordset_all_jobs_finished(self, recordset, options=None):
        """Event triggered when all jobs related to a recordset are done.

        :param recordset: current import.recordset browse record
        :param options: dictionary of options to propagate from the importer

        You can hook here if you want to do something when all the jobs
        enqueued for the given recordset are done.
        """
        _logger.info(
            'All jobs for the recordset %s have been successfully performed.',
            (recordset.name)
        )


class ImportRecordlJobEventListener(Component):
    _name = 'queue.job.listener'
    _inherit = 'base.event.listener'
    _collection = 'import.backend'
    _apply_on = ['queue.job']

    def _get_record_by_job(self, job):
        """Retrieve import record by its job."""
        return self.env['import.record'].search(
            [('job_id', '=', job.id)], limit=1)

    def on_record_write(self, job, fields=None):
        if 'state' in fields and job.state == DONE:
            self._handle_jobs_all_done(job)

    def _handle_jobs_all_done(self, job):
        """Trigger a specific event when all the jobs are done."""
        # retrieve all the jobs tied to same recordset's records
        recordset = self._get_record_by_job(job).recordset_id
        sibling_jobs_ids = recordset.mapped('record_ids.job_id').ids
        if job.id in sibling_jobs_ids:
            sibling_jobs_ids.remove(job.id)
        if sibling_jobs_ids:
            # use another transaction to make sure we read the real DB state
            with job.pool.cursor() as cr:
                jobs_yet_to_perform = job.with_env(
                    job.env(cr=cr)
                ).search_count([
                    ('id', 'in', sibling_jobs_ids), ('state', '!=', DONE)
                ])
                if not jobs_yet_to_perform:
                    recordset._event(
                        'on_recordset_all_jobs_finished'
                    ).notify(recordset)
