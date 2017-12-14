# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.addons.component.core import Component, AbstractComponent
from ..log import logger
from ..log import LOGGER_NAME


class RecordSetImporter(Component):
    """Importer for recordsets."""

    _name = 'importer.recordset'
    _inherit = 'importer.base.component'
    _usage = 'recordset.importer'
    _apply_on = 'import.recordset'

    def run(self, recordset, **kw):
        # update recordset report
        recordset.set_report({
            '_last_start': fields.Datetime.now(),
        }, reset=True)
        msg = 'START RECORDSET {0}({1})'.format(recordset.name,
                                                recordset.id)
        logger.info(msg)

        record_model = recordset.record_ids

        source = recordset.get_source()
        for chunk in source.get_lines():
            # create chuncked records and run their imports
            record = record_model.create({'recordset_id': recordset.id})
            # store data
            record.set_data(chunk)
            record.run_import()


class RecordImporter(AbstractComponent):
    """Importer for records."""

    _name = 'importer.record'
    _inherit = ['importer.base.component']
    _usage = 'record.importer'
    _apply_on = 'import.record'
    # log and report errors
    # do not make the whole import fail
    _break_on_error = False
    odoo_unique_key = ''

    def _init_importer(self, recordset):
        self.recordset = recordset
        self.record_handler = self.component_by_name(
            'importer.odoorecord.handler',
            model_name=self.model._name,
        )
        self.record_handler._init_handler(
            importer=self,
            unique_key=self.odoo_unique_key
        )
        self.tracker = self.component_by_name(
            'importer.tracking.handler',
            model_name=self.model._name,
        )
        self.tracker._init_handler(
            model_name=self.model._name,
            logger_name=LOGGER_NAME,
            log_prefix=self.recordset.import_type_id.key + ' ',
        )

    _mapper = None

    @property
    def mapper(self):
        if not self._mapper:
            self._mapper = self.component(usage='importer.mapper')
        return self._mapper

    def required_keys(self, create=False):
        """Keys that are mandatory to import a line."""
        req = self.mapper.required_keys()
        all_values = []
        for k, v in req.items():
            # make sure values are always tuples
            # as we support multiple dest keys
            if not isinstance(v, (tuple, list)):
                req[k] = (v, )
            all_values.extend(req[k])
        unique_key = self.odoo_unique_key
        if (unique_key and
                unique_key not in list(req.keys()) and
                unique_key not in all_values):
            # this one is REALLY required :)
            req[unique_key] = (unique_key, )
        return req

    # mostly for auto-documentation in UI
    def default_values(self):
        """Values that are automatically assigned."""
        return self.mapper.default_values()

    def translatable_keys(self, create=False):
        """Keys that are translatable."""
        return self.mapper.translatable_keys()

    def translatable_langs(self):
        return self.env['res.lang'].search([
            ('translatable', '=', True)]).mapped('code')

    def make_translation_key(self, key, lang):
        return '{}:{}'.format(key, lang)

    def collect_translatable(self, values, orig_values):
        """Get translations values for `mapper.translatable_keys`.

        We assume that the source contains extra columns in the form:

            `mapper_key:lang`

        whereas `mapper_key` is an odoo record field to translate
        and lang matches one of the installed languages.

        Translatable keys must be declared on the mapper
        within the attribute `translatable`.
        """
        translatable = {}
        if not self.translatable_keys():
            return translatable
        for lang in self.translatable_langs():
            for key in self.translatable_keys():
                # eg: name:fr_FR
                tkey = self.make_translation_key(key, lang)
                if tkey in orig_values and values.get(key):
                    if lang not in translatable:
                        translatable[lang] = {}
                    # we keep only translation for existing values
                    translatable[lang][key] = orig_values.get(tkey)
        return translatable

    def _check_missing(self, source_key, dest_key, values, orig_values):
        """Check for required keys missing."""
        missing = (not source_key.startswith('__') and
                   orig_values.get(source_key) is None)
        if missing:
            msg = 'MISSING REQUIRED SOURCE KEY={}'.format(source_key)
            unique_key = self.odoo_unique_key
            if unique_key and values.get(unique_key):
                msg += ': {}={}'.format(
                    unique_key, values[unique_key])
            return {
                'message': msg,
            }
        missing = (not dest_key.startswith('__') and
                   values.get(dest_key) is None)
        if missing:
            msg = 'MISSING REQUIRED DESTINATION KEY={}'.format(dest_key)
            if unique_key and values.get(unique_key):
                msg += ': {}={}'.format(
                    unique_key, values[unique_key])
            return {
                'message': msg,
            }
        return False

    def skip_it(self, values, orig_values):
        """Skip item import conditionally... if you want ;).

        You can return back `False` to not skip
        or a dictionary containing info about skip reason.
        """
        msg = ''
        required = self.required_keys()
        for source_key, dest_key in required.items():
            # we support multiple destination keys
            for _dest_key in dest_key:
                missing = self._check_missing(
                    source_key, _dest_key, values, orig_values)
                if missing:
                    return missing

        if self.record_handler.odoo_exists(values, orig_values) \
                and not self.recordset.override_existing:
            msg = 'ALREADY EXISTS'
            if self.odoo_unique_key:
                msg += ': {}={}'.format(
                    self.odoo_unique_key, values[self.odoo_unique_key])
            return {
                'message': msg,
                'odoo_record':
                    self.record_handler.odoo_find(values, orig_values).id,
            }
        return False

    def cleanup_line(self, line):
        """Apply basic cleanup on lines."""
        # we cannot alter dict keys while iterating
        res = {}
        for k, v in line.items():
            if not k.startswith('_'):
                k = self.clean_line_key(k)
            if isinstance(v, str):
                v = v.strip()
            res[k] = v
        return res

    def clean_line_key(self, key):
        """Clean record key.

        Sometimes your CSV source do not have proper keys,
        they can contain a lot of crap or they can change
        lower/uppercase from import to importer.
        You can override this method to normalize keys
        and make your import mappers work reliably.
        """
        return key.strip()

    def prepare_line(self, line):
        """Pre-manipulate a line if needed."""
        pass

    def _do_report(self):
        previous = self.recordset.get_report()
        report = self.tracker.get_report(previous)
        self.recordset.set_report({self.model._name: report})

    def _record_lines(self):
        return self.record.get_data()

    def _load_mapper_options(self):
        return {
            'override_existing': self.recordset.override_existing
        }

    def run(self, record, **kw):
        """Run the import machinery!"""

        self.record = record
        if not self.record:
            # maybe deleted???
            msg = 'NO RECORD FOUND, maybe deleted? Check your jobs!'
            logger.error(msg)
            return

        self._init_importer(self.record.recordset_id)

        mapper_options = self._load_mapper_options()

        for line in self._record_lines():
            line = self.cleanup_line(line)
            self.prepare_line(line)

            odoo_record = None

            try:
                with self.env.cr.savepoint():
                    values = self.mapper.map_record(line).values(
                        **mapper_options)
            except Exception as err:
                values = {}
                self.tracker.log_error(values, line, odoo_record, message=err)
                if self._break_on_error:
                    raise
                continue

            # handle forced skipping
            skip_info = self.skip_it(values, line)
            if skip_info:
                self.tracker.log_skipped(values, line, skip_info)
                continue

            try:
                with self.env.cr.savepoint():
                    if self.record_handler.odoo_exists(values, line):
                        odoo_record = \
                            self.record_handler.odoo_write(values, line)
                        self.tracker.log_updated(values, line, odoo_record)
                    else:
                        odoo_record = \
                            self.record_handler.odoo_create(values, line)
                        self.tracker.log_created(values, line, odoo_record)
            except Exception as err:
                self.tracker.log_error(values, line, odoo_record, message=err)
                if self._break_on_error:
                    raise
                continue

        # update report
        self._do_report()

        # log chunk finished
        msg = ' '.join([
            'CHUNK FINISHED',
            '[created: {created}]',
            '[updated: {updated}]',
            '[skipped: {skipped}]',
            '[errored: {errored}]',
        ]).format(**self.tracker.get_counters())
        self.tracker._log(msg)

        # TODO
        # chunk_finished_event.fire(
        #     self.env, self.model._name, self.record)
        return 'ok'

    # TODO
    def after_all(self, recordset):
        """Get something done after all the children jobs have completed.

        This should be triggered by `chunk_finished_event`.
        """
        # TODO: needed for logger and other stuff. Can be simplified.
        # self._init_importer(recordset)
        pass
