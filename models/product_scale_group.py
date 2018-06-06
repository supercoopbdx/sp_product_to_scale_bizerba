# -*- coding: utf-8 -*-
# Copyright (C) 2014 GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openerp.osv import fields
from openerp.osv.orm import Model

_logger = logging.getLogger(__name__)


class product_scale_group(Model):
    _name = 'product.scale.group'

    # Compute Section
    def _compute_product_qty(
            self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for group in self.browse(cr, uid, ids, context):
            res[group.id] = len(group.product_ids)
        return res

    # Column Section
    _columns = {
        'name': fields.char(
            string='Name', required=True),
        'active': fields.boolean(
            string='Active'),
        'external_identity': fields.char(
            string='External ID', required=True),
        'company_id': fields.many2one(
            'res.company', string='Company', select=True),
        'scale_system_id': fields.many2one(
            'product.scale.system', string='Scale System', required=True),
        'product_ids': fields.one2many(
            'product.product', 'scale_group_id', 'Products'),
        'product_qty': fields.function(
            _compute_product_qty, type='integer', string='Products Quantity'),
    }

    _defaults = {
        'active': True,
        'company_id': lambda s, cr, uid, c: s.pool.get('res.company').
            _company_default_get(cr, uid, 'product.product', context=c),
    }

    def send_all_to_scale_create(self, cr, uid, ids, context=None):
        myself = self.browse(cr, uid, ids, context=context)
        for scale_group in myself:
            scale_group.product_ids.send_scale_create()

    def send_all_to_scale_write(self, cr, uid, ids, context=None):
        myself = self.browse(cr, uid, ids, context=context)
        for scale_group in myself:
            scale_group.product_ids.send_scale_write()

    # Tri les articles par nom pour la balance tactile
    # Tri selon les catégories de 281 à 980
    # et aussi pour le labo (de 1 à 280)
    # Voir le tuto sur le portail
    # TODO ne pas réattribuer si déjà dans l'ordre (génère sans arrêt le même fichier)
    def reorder_products_by_name(self, cr, uid, ids, context=None):
        myself = self.browse(cr, uid, ids, context=context)
        keys = [1, 281, 421, 561, 771, 876]
        cats = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}}
        for group in myself:
            logging.info('Reorder group "%s"', group.name)
            for pp in group.product_ids:
                if 1 <= pp.scale_sequence <= 280:
                    cats[0][pp.name] = pp
                elif 281 <= pp.scale_sequence <= 420:
                    cats[1][pp.name] = pp
                elif 421 <= pp.scale_sequence <= 560:
                    cats[2][pp.name] = pp
                elif 561 <= pp.scale_sequence <= 770:
                    cats[3][pp.name] = pp
                elif 771 <= pp.scale_sequence <= 875:
                    cats[4][pp.name] = pp
                elif 876 <= pp.scale_sequence <= 980:
                    cats[5][pp.name] = pp

            # Sort
            for i, cat in cats.items():
                logging.info('Sort cat %s', i)
                # sorted(cat.keys(), key=unicode.lower)
                for n in sorted(cat):
                    logging.info('--- %s : %s => %s', n, cat[n].scale_sequence, keys[i])
                    cat[n].write({'scale_sequence': keys[i]})
                    keys[i] += 1
