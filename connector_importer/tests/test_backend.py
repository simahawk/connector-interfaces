# -*- coding: utf-8 -*-
# Author: Simone Orsi
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import odoo.tests.common as common


class TestBackend(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUp()
        cls.backend_model = cls.env['import.backend']

    def test_backend_create(self):
        b1 = self.backend_model.create({
            'version': '1.0',
        })
        self.assertTrue(b1)
