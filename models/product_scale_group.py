# -*- coding: utf-8 -*-
# Copyright (C) 2014 GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import re

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

    # Tri les articles par nom
    # Tri selon les catégories de 281 à 980
    # et aussi pour le labo (de 1 à 280)
    # Voir le tuto sur le portail
    def reorder_products_by_name(self, cr, uid, ids, context=None):
        myself = self.browse(cr, uid, ids, context=context)
        seqs = {1: 1, 2: 281, 3: 421, 4: 561, 5: 771, 6: 876}
        for group in myself:
            sp = {}
            seq_min = seqs[group.id]
            logging.info('Reorder group "%s" - Min: %s', group.name, seq_min)
            for pp in group.product_ids:
                if pp.sale_ok is True:
                    sp[pp.name] = pp
                elif pp.scale_sequence != 0:
                    sp[pp].write({'scale_sequence': 0})

            # Sort product
            for pp in sorted(sp):
                logging.info('--- %s : %s => %s', sp[pp].name, sp[pp].scale_sequence, seq_min)
                sp[pp].write({'scale_sequence': seq_min})
                seq_min += 1
                if seq_min == seqs[group.id+1]:
                    break
