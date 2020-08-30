# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'External storage source for Connector Importer',
    'description': """`connector_importer` source via ExtStorage.""",
    'version': '13.0.1.0.0',
    'depends': [
        'connector_importer',
        'storage_backend',
    ],
    'author': 'Camptocamp',
    'license': 'AGPL-3',
    'category': 'Uncategorized',
    'website': 'https://github.com/OCA/connector-interfaces',
    'data': [
        'security/ir.model.access.csv',
        # 'views/source_views.xml',
    ],
}
