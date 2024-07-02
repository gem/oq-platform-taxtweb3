#!/usr/bin/env python
import sys, math, re, io

from openquake.taxonomy3.taxtweb_maps import (
    material, date_type, occu_type, bupo_type, plsh_type, stir_type,
    plan_irre, plan_seco, vert_irre, vert_seco, wall_type, roof_shap,
    roof_cove, roof_mate, roof_conn, floo_syma, floo_syty, foun_type,)
from openquake.taxonomy3.taxtweb_head import (
    mat_tech, mat_tead, mat_prop, llrs_type, llrs_duct, occu_spec,
    roof_sys, floo_conn)
from openquake.taxonomy3.taxonomy import taxonomy_short2full, Ret

taxonomy = None


def is_not_negative_int(s):
    """return true if the string is convertible
    to integer and its value is not negative"""
    try:
        if int(s) < 0 or int(s) != float(s):
            return False
        else:
            return True
    except ValueError:
        return False

def is_not_negative_float(s):
    """return true if the string is convertible
    to float and its value is not negative"""
    try:
        if float(s) < 0.0:
            return False
        else:
            return True
    except ValueError:
        return False

def is_in_rect_angle_float(s):
    """return true if the string is convertible
    to float and its value is between 0.0 and 90.0"""

    if not is_not_negative_float(s):
        return False

    if float(s) > 90.0:
        return False
    return True

def is_or_are_given(n):
    return n + (" is" if n <= 1 else " are") + " given."


class TaxtSel(object):
    """this class modelize the behavior of the javascript rapresentation
of a 'select' html tag with the same methods"""
    def __init__(self, name, items=[], val=-1, disabled=False, change_cb=None):
        '''
        items => list of 1 element dicts
        val => int identifing current val item
        '''
        self._name = name
        self._items = items[:]
        if items:
            if val == -1:
                self._val = 0
            else:
                self._val = val
        else:
            self._val = val

        self._disabled = disabled
        self._first_disabled = False
        self._change_cb = change_cb

    def empty(self):
        self._items = []
        self._val = -1

    def disabled(self, disabled=None):
        if disabled is None:
            return self._disabled
        else:
            self._disabled = disabled

    def first_disabled(self, first_disabled=None):
        if first_disabled is not None:
            self._first_disabled = first_disabled

        return self._first_disabled

    def items(self, items=None, val=0):
        '''
        items => list of 1 element dicts
        val => int identifing current val item
        '''
        if items is None:
            return self._items
        else:
            self._items = items[:]

        self.val(val)

    def val(self, val=-1):
        if val != -1:
            if isinstance(val, str):
                val = self.items.index(val)

            if val < -1 or val > len(self._items):
                raise ValueError

            self._val = val
            if self._change_cb:
                self._change_cb(self)

        return self._val

    def __str__(self):
        ret = "  %s (Sel)\n" % self._name
        if self._items:
            for k, v in enumerate(self._items):
                if k == self._val:
                    ret += "    %02d) * [%s]\n" % (k, v)
        else:
            ret += "    - no elements -\n"

        return ret


class TaxtBool(object):
    def __init__(self, name, val=False, change_cb=None):
        self._name = name
        self._val = val
        self._change_cb = change_cb

    def val(self, val=None):
        if val is None:
            return self._val
        else:
            self._val = val
            if self._change_cb:
                self._change_cb(self)
            return self._val

    def checked(self, val=None):
        return self.val(val)

    def __str__(self):
        return "  %s (Bool)\n    %s\n" % (self._name, "True" if self._val else "False")


class TaxtRadioItem(object):
    def __init__(self, val=None, checked=False, radio=None, change_cb=None):
        self._val = val
        self._checked = checked
        self._change_cb = change_cb
        self._radio = radio

    def radio(self, radio=None):
        if (radio is None):
            return self._radio
        else:
            self._radio = radio

    def val(self, val=None):
        if val is not None:
            self._val = val
            if self._change_cb:
                self._change_cb(self)

        return self._val

    def checked(self, is_checked=None):
        if is_checked is not None:
            if is_checked is True:
                if self._radio is not None:
                    for item in self._radio._items:
                        item.checked(False)
            self._checked = is_checked

        return self._checked


class TaxtRadio(object):
    def __init__(self, items=[]):
        self._items = items[:]
        for item in items:
            item.radio(self)

    def item_add(self, item):
        self.items.append(item)
        item.radio(self)


class TaxtStr(object):
    def __init__(self, name, val="0", change_cb=None, disabled=None):
        self._val = val
        self._change_cb = change_cb
        self._disabled = disabled
        self._name = name

    def val(self, val=None):
        if val is None:
            return self._val
        else:
            self._val = val
            if self._change_cb:
                self._change_cb(self)
            return self._val

    def disabled(self, disabled=None):
        if disabled is None:
            return self._disabled
        else:
            self._disabled = disabled

    def __str__(self):
        return "%s" % self._val


class Taxonomy(object):
    POS_DX = 0
    POS_DX_LMAT = 1
    POS_DX_LLRS = 2
    POS_DY = 3
    POS_DY_LMAT = 4
    POS_DY_LLRS = 5
    POS_HEIGHT = 6
    POS_DATE = 7
    POS_OCCUPANCY = 8
    POS_POSITION = 9
    POS_PLAN = 10
    POS_IRREG = 11
    POS_EXTWALL = 12
    POS_ROOF = 13
    POS_FLOOR = 14
    POS_FOUNDATION = 15

    UNKNOWN_ATOMS = [
        'MAT99', 'CT99', 'S99', 'ME99', 'SC99', 'MUN99', 'MR99', 'MO99',
        'ET99', 'W99', 'L99', 'DU99', 'Y99', 'H99', 'HB99', 'HF99', 'HD99',
        'OC99', 'RES99', 'COM99', 'MIX99', 'IND99', 'AGR99', 'ASS99', 'GOV99',
        'EDU99', 'BP99', 'PLF99', 'IR99', 'IRPP:IRN', 'IRVP:IRN', 'IRVS:IRN',
        'EW99', 'RSH99', 'RMT99', 'R99', 'RM99', 'RE99', 'RC99', 'RME99',
        'RWO99', 'RWC99', 'F99', 'FM99', 'FE99', 'FC99', 'FME99', 'FW99',
        'FWC99', 'FOS99', 'D99']
    ATOM_TYPE_VALUE = ['HEX', 'HAPP', 'HBEX', 'HBAPP', 'HFEX', 'HFAPP', 'HD',
                       'YEX', 'YPRE', 'YAPP']
    ATOM_TYPE_RANGE = ['HBET', 'HBBET', 'HFBET', 'YBET']

    def __init__(self, name, full):
        self._name = name

        self._gem_taxonomy_regularity_postinit = -1
        self._gem_taxonomy_form = ""
        self._gem_taxonomy_form_full = ""
        self._virt_sfx = ""

        if full:
            self.OutTypeCB = TaxtSel('OutTypeCB', ['Full',
                                      'Omit Unknown',
                                      'Short'],
                                     val=2, change_cb=self.taxt_OutTypeCBSelect)

        self.DirectionCB = TaxtBool("DirectionCB", val=True, change_cb=self.taxt_SetDirection2)

        self.Direction1RB1 = TaxtRadioItem(val="false", change_cb=self.taxt_Direction1RB1Click)
        self.Direction1RB2 = TaxtRadioItem(val="true", change_cb=self.taxt_Direction1RB2Click)
        self._Direction1R = TaxtRadio(items=[self.Direction1RB1, self.Direction1RB2])
        self.Direction1RB1.checked(True)

        self.Direction2RB1 = TaxtRadioItem(val="unspec", change_cb=self.taxt_Direction2RB1Click)
        self.Direction2RB3 = TaxtRadioItem(val="spec", change_cb=self.taxt_Direction2RB3Click)
        self._Direction2R = TaxtRadio(items=[self.Direction2RB1, self.Direction2RB3])
        self.Direction2RB1.checked(True)

        self.MaterialCB11 = TaxtSel('MaterialCB11',
                                    ['Unknown Material',
                                     'Concrete, unknown reinforcement',
                                     'Concrete, unreinforced',
                                     'Concrete, reinforced',
                                     'Concrete, composite with steel section',
                                     'Steel',
                                     'Metal (except steel)',
                                     'Masonry, unknown reinforcement',
                                     'Masonry, unreinforced',
                                     'Masonry, confined',
                                     'Masonry, reinforced',
                                     'Earth, unknown reinforcement',
                                     'Earth, unreinforced',
                                     'Earth, reinforced',
                                     'Wood',
                                     'Other material'], val=0, change_cb=self.taxt_MaterialCB11Select)
        self.MaterialCB21 = TaxtSel('MaterialCB21', change_cb=self.taxt_MaterialCB21Select)
        self.MaterialCB31 = TaxtSel('MaterialCB31', change_cb=self.taxt_MaterialCB31Select)
        self.MaterialCB41 = TaxtSel('MaterialCB41', change_cb=self.taxt_MaterialCB41Select)
        self.SystemCB11 = TaxtSel('SystemCB11', change_cb=self.taxt_SystemCB11Select)
        self.SystemCB21 = TaxtSel('SystemCB21', change_cb=self.taxt_SystemCB21Select)

        self.MaterialCB12 = TaxtSel('MaterialCB12', ['Unknown Material',
                                     'Concrete, unknown reinforcement',
                                     'Concrete, unreinforced',
                                     'Concrete, reinforced',
                                     'Concrete, composite with steel section',
                                     'Steel',
                                     'Metal (except steel)',
                                     'Masonry, unknown reinforcement',
                                     'Masonry, unreinforced',
                                     'Masonry, confined',
                                     'Masonry, reinforced',
                                     'Earth, unknown reinforcement',
                                     'Earth, unreinforced',
                                     'Earth, reinforced',
                                     'Wood',
                                     'Other material'], change_cb=self.taxt_MaterialCB12Select)
        self.MaterialCB22 = TaxtSel('MaterialCB22', change_cb=self.taxt_MaterialCB22Select)
        self.MaterialCB32 = TaxtSel('MaterialCB32', change_cb=self.taxt_MaterialCB32Select)
        self.MaterialCB42 = TaxtSel('MaterialCB42', change_cb=self.taxt_MaterialCB42Select)
        self.SystemCB12 = TaxtSel('SystemCB12', change_cb=self.taxt_SystemCB12Select)
        self.SystemCB22 = TaxtSel('SystemCB22', change_cb=self.taxt_SystemCB22Select)

        self.HeightCB1 = TaxtSel('HeightCB1', ['Unknown number of storeys',
                                  'Range of the number of storeys',
                                  'Exact number of storeys',
                                  'Approximate number of storeys'],
                                 val=0, change_cb=self.taxt_HeightCB1Select)
        self.noStoreysE11 = TaxtStr('noStoreysE11', change_cb=self.taxt_HeightCB1Select)
        self.noStoreysE12 = TaxtStr('noStoreysE12', change_cb=self.taxt_HeightCB1Select)



        self.HeightCB2 = TaxtSel('HeightCB2', ['Unknown number of storeys',
                                  'Range of the number of storeys',
                                  'Exact number of storeys',
                                  'Approximate number of storeys'],
                                 val=0, change_cb=self.taxt_HeightCB2Select)
        self.noStoreysE21 = TaxtStr('noStoreysE21', change_cb=self.taxt_HeightCB2Select)
        self.noStoreysE22 = TaxtStr('noStoreysE22', change_cb=self.taxt_HeightCB2Select)

        self.HeightCB3 = TaxtSel('HeightCB3', ['Height above grade unknown',
                                  'Range of height above grade',
                                  'Exact height above grade',
                                  'Approximate height above grade'],
                                 val=0, change_cb=self.taxt_HeightCB3Select)
        self.noStoreysE31 = TaxtStr('noStoreysE31', change_cb=self.taxt_HeightCB3Select)
        self.noStoreysE32 = TaxtStr('noStoreysE32', change_cb=self.taxt_HeightCB3Select)

        self.HeightCB4 = TaxtSel('HeightCB4', ['Unknown slope',
                                  'Slope of the ground'],
                                  val=0, change_cb=self.taxt_HeightCB4Select)
        self.noStoreysE41 = TaxtStr('noStoreysE41', change_cb=self.taxt_HeightCB4Select)

        self.DateCB1 = TaxtSel('DateCB1', ['Year unknown',
                                'Exact date of construction or retrofit',
                                'Bounds for the date of construction or retrofit',
                                'Latest possible date of construction or retrofit',
                                'Approximate date of construction or retrofit'],
                               val=0, change_cb=self.taxt_DateCB1Select)
        self.DateE1 = TaxtStr('DateE1', change_cb=self.taxt_DateE1Change)
        self.DateE2 = TaxtStr('DateE2', change_cb=self.taxt_DateE2Change)

        self.OccupancyCB1 = TaxtSel('OccupancyCB1', ['Unknown occupancy type',
                                     'Residential',
                                     'Commercial and public',
                                     'Mixed use',
                                     'Industrial',
                                     'Agriculture',
                                     'Assembly',
                                     'Government',
                                     'Education',
                                     'Other occupancy type'],
                                    val=0, change_cb=self.taxt_OccupancyCB1Select)
        self.OccupancyCB2 = TaxtSel('OccupancyCB2', change_cb=self.taxt_OccupancyCB2Select)

        self.PositionCB = TaxtSel('PositionCB', ['Unknown building position',
                                   'Detached building',
                                   'Adjoining building(s) on one side',
                                   'Adjoining building(s) on two sides',
                                   'Adjoining building(s) on three sides'],
                                  val=0, change_cb=self.taxt_PositionCBSelect)

        self.PlanShapeCB = TaxtSel('PlanShapeCB', ['Unknown plan shape',
                                    'Square, solid',
                                    'Square, with an opening in plan',
                                    'Rectangular, solid',
                                    'Rectangular, with an opening in plan',
                                    'L-shape',
                                    'Curved, solid (e.g. circular, eliptical, ovoid)',
                                    'Curved, with an opening in plan',
                                    'Triangular, solid',
                                    'Triangular, with an opening in plan',
                                    'E-shape',
                                    'H-shape',
                                    'S-shape',
                                    'T-shape',
                                    'U- or C-shape',
                                    'X-shape',
                                    'Y-shape',
                                    'Polygonal, solid',
                                    'Polygonal, with an opening in plan',
                                    'Irregular plan shape'],
                                   val=0, change_cb=self.taxt_PlanShapeCBSelect)

        self.RegularityCB1 = TaxtSel('RegularityCB1', ['Unknown structural irregularity',
                                      'Regular structure',
                                      'Irregular structure'],
                                     val=0, change_cb=self.taxt_RegularityCB1Select)
        self.RegularityCB2 = TaxtSel('RegularityCB2', change_cb=self.taxt_RegularityCB2Select)
        self.RegularityCB3 = TaxtSel('RegularityCB3', change_cb=self.taxt_RegularityCB3Select)
        self.RegularityCB4 = TaxtSel('RegularityCB4', change_cb=self.taxt_RegularityCB4Select)
        self.RegularityCB5 = TaxtSel('RegularityCB5', change_cb=self.taxt_RegularityCB5Select)

        self.WallsCB = TaxtSel('WallsCB', ['Unknown material of exterior walls',
                                'Concrete exterior walls',
                                'Glass exterior walls',
                                'Earthen exterior walls',
                                'Masonry exterior walls',
                                'Metal exterior walls',
                                'Vegetative exterior walls',
                                'Wooden exterior walls',
                                'Stucco finish on light framing for exterior walls',
                                'Plastic/vinyl exterior walls, various',
                                'Cement-based boards for exterior walls',
                                'Material of exterior walls, other'],
                               val=0, change_cb=self.taxt_WallsCBSelect)

        self.RoofCB1 = TaxtSel('RoofCB1', ['Unknown roof shape',
                                'Flat',
                                'Pitched with gable ends',
                                'Pitched and hipped',
                                'Pitched with dormers',
                                'Monopitch',
                                'Sawtooth',
                                'Curved',
                                'Complex regular',
                                'Complex irregular',
                                'Roof shape, other'],
                               val=0, change_cb=self.taxt_RoofCB1Select)
        self.RoofCB2 = TaxtSel('RoofCB2', ['Unknown roof covering',
                                'Concrete roof, no covering',
                                'Clay or concrete tile roof covering',
                                'Fibre cement or metal tile covering',
                                'Membrane roof covering',
                                'Slate roof covering',
                                'Stone slab roof covering',
                                'Metal or asbestos sheet covering',
                                'Wooden or asphalt shingle covering',
                                'Vegetative roof covering',
                                'Earthen roof covering',
                                'Solar panelled roofs',
                                'Tensile membrane or fabric roof',
                                'Roof covering, other'],
                               val=0, change_cb=self.taxt_RoofCB2Select)

        self.RoofCB3 = TaxtSel('RoofCB3', ['Roof material, unknown',
                                'Masonry roof',
                                'Earthen roof',
                                'Concrete roof',
                                'Metal roof',
                                'Wooden roof',
                                'Fabric roof',
                                'Roof material,other'],
                               val=0, change_cb=self.taxt_RoofCB3Select)

        self.RoofCB4 = TaxtSel('RoofCB4', change_cb=self.taxt_RoofCB4Select)
        self.RoofCB5 = TaxtSel('RoofCB5', ['Roof-wall diaphragm connection unknown',
                                'Roof-wall diaphragm connection not provided',
                                'Roof-wall diaphragm connection present',
                                'Roof tie-down unknown',
                                'Roof tie-down not provided',
                                'Roof tie-down present'],
                               val=0, change_cb=self.taxt_RoofCB5Select)

        self.FoundationsCB = TaxtSel('FoundationsCB', ['Unknown foundation system',
                                      'Shallow foundation, with lateral capacity',
                                      'Shallow foundation, with no lateral capacity',
                                      'Deep foundation, with lateral capacity',
                                      'Deep foundation, with no lateral capacity',
                                      'Foundation, other'],
                                     val=0, change_cb=self.taxt_FoundationsCBSelect)

        self.FloorCB1 = TaxtSel('FloorCB1', ['Floor material, unknown',
                                 'No elevated or suspended floor material (single-storey)',
                                 'Masonry floor',
                                 'Earthen floor',
                                 'Concrete floor',
                                 'Metal floor',
                                 'Wooden floor',
                                 'Floor material, other'],
                                val=0, change_cb=self.taxt_FloorCB1Select)
        self.FloorCB2 = TaxtSel('FloorCB2', change_cb=self.taxt_FloorCB2Select)
        self.FloorCB3 = TaxtSel('FloorCB3', ['Floor-wall diaphragm connection, unknown',
                                 'Floor-wall diaphragm connection not provided',
                                 'Floor-wall diaphragm connection present'],
                                val=0, change_cb=self.taxt_FloorCB3Select)

        self.resultE = TaxtStr('resultE')
        self.resultE_virt = TaxtStr('resultE_virt')

        self.taxt_ValidateMaterial1()
        self.taxt_ValidateMaterial2()
        self.taxt_ValidateRoof()
        self.taxt_ValidateFloor()
        self.taxt_ValidateHeight()
        self.taxt_ValidateDate()
        self.taxt_ValidateRegularity()
        self.taxt_ValidateOccupancy()
        self.taxt_BuildTaxonomy()

    def taxt_Initiate(self, full):
        if full:
            self.OutTypeCB.items(['Full',
                                  'Omit Unknown',
                                  'Short'], val=2)

        self.DirectionCB.checked(True)

        self.MaterialCB11.items(['Unknown Material',
                                 'Concrete, unknown reinforcement',
                                 'Concrete, unreinforced',
                                 'Concrete, reinforced',
                                 'Concrete, composite with steel section',
                                 'Steel',
                                 'Metal (except steel)',
                                 'Masonry, unknown reinforcement',
                                 'Masonry, unreinforced',
                                 'Masonry, confined',
                                 'Masonry, reinforced',
                                 'Earth, unknown reinforcement',
                                 'Earth, unreinforced',
                                 'Earth, reinforced',
                                 'Wood',
                                 'Other material'])

        self.MaterialCB12.items(['Unknown Material',
                                 'Concrete, unknown reinforcement',
                                 'Concrete, unreinforced',
                                 'Concrete, reinforced',
                                 'Concrete, composite with steel section',
                                 'Steel',
                                 'Metal (except steel)',
                                 'Masonry, unknown reinforcement',
                                 'Masonry, unreinforced',
                                 'Masonry, confined',
                                 'Masonry, reinforced',
                                 'Earth, unknown reinforcement',
                                 'Earth, unreinforced',
                                 'Earth, reinforced',
                                 'Wood',
                                 'Other material'])

        self.HeightCB1.items(['Unknown number of storeys',
                              'Range of the number of storeys',
                              'Exact number of storeys',
                              'Approximate number of storeys'])



        self.HeightCB2.items(['Unknown number of storeys',
                              'Range of the number of storeys',
                              'Exact number of storeys',
                              'Approximate number of storeys'])

        self.HeightCB3.items(['Height above grade unknown',
                              'Range of height above grade',
                              'Exact height above grade',
                              'Approximate height above grade'])

        self.HeightCB4.items(['Unknown slope',
                              'Slope of the ground'])

        self.DateCB1.items(['Year unknown',
                            'Exact date of construction or retrofit',
                            'Bounds for the date of construction or retrofit',
                            'Latest possible date of construction or retrofit',
                            'Approximate date of construction or retrofit'])

        self.OccupancyCB1.items(['Unknown occupancy type',
                                 'Residential',
                                 'Commercial and public',
                                 'Mixed use',
                                 'Industrial',
                                 'Agriculture',
                                 'Assembly',
                                 'Government',
                                 'Education',
                                 'Other occupancy type'])

        self.PositionCB.items(['Unknown building position',
                               'Detached building',
                               'Adjoining building(s) on one side',
                               'Adjoining building(s) on two sides',
                               'Adjoining building(s) on three sides'])

        self.PlanShapeCB.items(['Unknown plan shape',
                                'Square, solid',
                                'Square, with an opening in plan',
                                'Rectangular, solid',
                                'Rectangular, with an opening in plan',
                                'L-shape',
                                'Curved, solid (e.g. circular, eliptical, ovoid)',
                                'Curved, with an opening in plan',
                                'Triangular, solid',
                                'Triangular, with an opening in plan',
                                'E-shape',
                                'H-shape',
                                'S-shape',
                                'T-shape',
                                'U- or C-shape',
                                'X-shape',
                                'Y-shape',
                                'Polygonal, solid',
                                'Polygonal, with an opening in plan',
                                'Irregular plan shape'])

        self.RegularityCB1.items(['Unknown structural irregularity',
                                  'Regular structure',
                                  'Irregular structure'])

        self.WallsCB.items(['Unknown material of exterior walls',
                            'Concrete exterior walls',
                            'Glass exterior walls',
                            'Earthen exterior walls',
                            'Masonry exterior walls',
                            'Metal exterior walls',
                            'Vegetative exterior walls',
                            'Wooden exterior walls',
                            'Stucco finish on light framing for exterior walls',
                            'Plastic/vinyl exterior walls, various',
                            'Cement-based boards for exterior walls',
                            'Material of exterior walls, other'])

        self.RoofCB1.items(['Unknown roof shape',
                            'Flat',
                            'Pitched with gable ends',
                            'Pitched and hipped',
                            'Pitched with dormers',
                            'Monopitch',
                            'Sawtooth',
                            'Curved',
                            'Complex regular',
                            'Complex irregular',
                            'Roof shape, other'])
        self.RoofCB2.items(['Unknown roof covering',
                            'Concrete roof, no covering',
                            'Clay or concrete tile roof covering',
                            'Fibre cement or metal tile covering',
                            'Membrane roof covering',
                            'Slate roof covering',
                            'Stone slab roof covering',
                            'Metal or asbestos sheet covering',
                            'Wooden or asphalt shingle covering',
                            'Vegetative roof covering',
                            'Earthen roof covering',
                            'Solar panelled roofs',
                            'Tensile membrane or fabric roof',
                            'Roof covering, other'])

        self.RoofCB3.items(['Roof material, unknown',
                            'Masonry roof',
                            'Earthen roof',
                            'Concrete roof',
                            'Metal roof',
                            'Wooden roof',
                            'Fabric roof',
                            'Roof material,other'])

        self.RoofCB5.items(['Roof-wall diaphragm connection unknown',
                            'Roof-wall diaphragm connection not provided',
                            'Roof-wall diaphragm connection present',
                            'Roof tie-down unknown',
                            'Roof tie-down not provided',
                            'Roof tie-down present'])

        self.FoundationsCB.items(['Unknown foundation system',
                                  'Shallow foundation, with lateral capacity',
                                  'Shallow foundation, with no lateral capacity',
                                  'Deep foundation, with lateral capacity',
                                  'Deep foundation, with no lateral capacity',
                                  'Foundation, other'])

        self.FloorCB1.items(['Floor material, unknown',
                             'No elevated or suspended floor material (single-storey)',
                             'Masonry floor',
                             'Earthen floor',
                             'Concrete floor',
                             'Metal floor',
                             'Wooden floor',
                             'Floor material, other'])
        self.FloorCB3.items(['Floor-wall diaphragm connection, unknown',
                            'Floor-wall diaphragm connection not provided',
                             'Floor-wall diaphragm connection present'])

        self.taxt_ValidateMaterial1()
        self.taxt_ValidateMaterial2()
        self.taxt_ValidateRoof()
        self.taxt_ValidateFloor()
        self.taxt_ValidateHeight()
        self.taxt_ValidateDate()
        self.taxt_ValidateRegularity()
        self.taxt_ValidateOccupancy()
        self.taxt_BuildTaxonomy()


    def __str__(self):
        ret = "%s (Taxonomy)\n" % self._name
        ret += self.OutTypeCB.__str__()
        ret += self.DirectionCB.__str__()
        ret += self.MaterialCB11.__str__()
        ret += self.MaterialCB21.__str__()
        ret += self.MaterialCB31.__str__()
        ret += self.MaterialCB41.__str__()
        ret += self.SystemCB11.__str__()
        ret += self.SystemCB21.__str__()
        ret += self.MaterialCB12.__str__()
        ret += self.MaterialCB22.__str__()
        ret += self.MaterialCB32.__str__()
        ret += self.MaterialCB42.__str__()
        ret += self.SystemCB12.__str__()
        ret += self.SystemCB22.__str__()
        ret += self.HeightCB1.__str__()
        ret += self.HeightCB2.__str__()
        ret += self.HeightCB3.__str__()
        ret += self.HeightCB4.__str__()
        ret += self.DateCB1.__str__()
        ret += self.OccupancyCB1.__str__()
        ret += self.OccupancyCB2.__str__()
        ret += self.PositionCB.__str__()
        ret += self.PlanShapeCB.__str__()
        ret += self.RegularityCB1.__str__()
        ret += self.RegularityCB2.__str__()
        ret += self.RegularityCB4.__str__()
        ret += self.RegularityCB3.__str__()
        ret += self.RegularityCB5.__str__()
        ret += self.WallsCB.__str__()
        ret += self.RoofCB1.__str__()
        ret += self.RoofCB2.__str__()
        ret += self.RoofCB3.__str__()
        ret += self.RoofCB4.__str__()
        ret += self.RoofCB5.__str__()
        ret += self.FoundationsCB.__str__()
        ret += self.FloorCB1.__str__()
        ret += self.FloorCB2.__str__()
        ret += self.FloorCB3.__str__()

        return ret

    def taxt_Direction1RB1Click(self, taxt_radioitem=None):
        self.Direction2RB1.checked(True)
        self.taxt_BuildTaxonomy()

    def taxt_Direction1RB2Click(self, taxt_radioitem=None):
        self.Direction2RB3.checked(True)
        self.taxt_BuildTaxonomy()

    def taxt_Direction2RB1Click(self, taxt_radioitem=None):
        self.Direction1RB1.checked(True)
        self.taxt_BuildTaxonomy()

    def taxt_Direction2RB3Click(self, taxt_radioitem=None):
        self.Direction1RB2.checked(True)
        self.taxt_BuildTaxonomy()

    def taxt_OutTypeCBSelect(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_SetDirection2(self, obj=None):
        if self.DirectionCB.checked():
            self.MaterialCB12.val(self.MaterialCB11.val())
            self.taxt_MaterialCB12Select()
            self.MaterialCB22.val(self.MaterialCB21.val())
            self.taxt_MaterialCB22Select()
            self.MaterialCB32.val(self.MaterialCB31.val())
            self.taxt_MaterialCB32Select()
            self.MaterialCB42.val(self.MaterialCB41.val())
            self.taxt_MaterialCB42Select()
            self.SystemCB12.val(self.SystemCB11.val())
            self.taxt_SystemCB12Select()
            self.SystemCB22.val(self.SystemCB21.val())
            self.taxt_SystemCB22Select()

    def taxt_MaterialCB11Select(self, obj=None):
        self.taxt_ValidateMaterial1()
        self.taxt_SetDirection2()
        if self.DirectionCB.checked():
            self.taxt_ValidateMaterial2()

        self.taxt_BuildTaxonomy()

    def taxt_MaterialCB21Select(self, obj=None):
        self.taxt_SetDirection2()
        self.taxt_BuildTaxonomy()

    def taxt_MaterialCB31Select(self, obj=None):
        self.taxt_SetDirection2()
        self.taxt_BuildTaxonomy()

    def taxt_MaterialCB41Select(self, obj=None):
        self.taxt_SetDirection2()
        self.taxt_BuildTaxonomy()

    def taxt_SystemCB11Select(self, obj=None):
        self.taxt_SetDirection2()
        self.taxt_ValidateSystem1()
        if self.DirectionCB.checked():
            self.taxt_ValidateSystem2()
        self.taxt_BuildTaxonomy()

    def taxt_SystemCB21Select(self, obj=None):
        self.taxt_SetDirection2()
        self.taxt_BuildTaxonomy()

    def taxt_BreakDirection2(self, obj=None):
        # the check is performed just when called with parameter (triggered indirectly)
        # from an event or if forced by another function
        if obj is None:
            return

        if self.DirectionCB.checked():
            if (self.MaterialCB12.val() != self.MaterialCB11.val() or
                self.MaterialCB22.val() != self.MaterialCB21.val() or
                self.MaterialCB32.val() != self.MaterialCB31.val() or
                self.MaterialCB42.val() != self.MaterialCB41.val() or
                self.SystemCB12.val() != self.SystemCB11.val() or
                self.SystemCB22.val() != self.SystemCB21.val()):
                self.DirectionCB.checked(False)


    def taxt_MaterialCB12Select(self, obj=None):
        self.taxt_ValidateMaterial2()
        self.taxt_BreakDirection2(obj)
        self.taxt_ValidateSystem2()
        self.taxt_BuildTaxonomy()

    def taxt_MaterialCB22Select(self, obj=None):
        self.taxt_BreakDirection2(obj)
        self.taxt_BuildTaxonomy()

    def taxt_MaterialCB32Select(self, obj=None):
        self.taxt_BreakDirection2(obj)
        self.taxt_BuildTaxonomy()

    def taxt_MaterialCB42Select(self, obj=None):
        self.taxt_BreakDirection2(obj)
        self.taxt_BuildTaxonomy()

    def taxt_SystemCB12Select(self, obj=None):
        self.taxt_ValidateSystem2()
        self.taxt_BreakDirection2(obj)
        self.taxt_BuildTaxonomy()

    def taxt_SystemCB22Select(self, obj=None):
        self.taxt_BreakDirection2(obj)
        self.taxt_BuildTaxonomy()

    def taxt_HeightCB1Select(self, obj=None):
        self.taxt_ValidateHeight()
        self.taxt_BuildTaxonomy()

    def taxt_HeightCB2Select(self, obj=None):
        self.taxt_ValidateHeight()
        self.taxt_BuildTaxonomy()

    def taxt_HeightCB3Select(self, obj=None):
        self.taxt_ValidateHeight()
        self.taxt_BuildTaxonomy()

    def taxt_HeightCB4Select(self, obj=None):
        self.taxt_ValidateHeight()
        self.taxt_BuildTaxonomy()

    def taxt_DateCB1Select(self, obj=None):
        self.taxt_ValidateDate()
        self.taxt_BuildTaxonomy()

    def taxt_DateE1Change(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_DateE2Change(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_OccupancyCB1Select(self, obj=None):
        self.taxt_ValidateOccupancy()
        self.taxt_BuildTaxonomy()

    def taxt_OccupancyCB2Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_PositionCBSelect(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_PlanShapeCBSelect(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_RegularityCB1Select(self, obj=None):
        self.taxt_ValidateRegularity()
        self.taxt_BuildTaxonomy()

    def taxt_RegularityCB2Select(self, obj=None):
        self.taxt_ValidateRegularity2()
        if self._gem_taxonomy_regularity_postinit == 3:
            self.RegularityCB3.val(0)
            self.taxt_ValidateRegularity3()

        self._gem_taxonomy_regularity_postinit = -1
        self.taxt_BuildTaxonomy()

    def taxt_RegularityCB3Select(self, obj=None):
        self.taxt_ValidateRegularity3()
        if self._gem_taxonomy_regularity_postinit == 2:
            self.RegularityCB2.val(0)
            self.taxt_ValidateRegularity2()

        self._gem_taxonomy_regularity_postinit = -1
        self.taxt_BuildTaxonomy()

    def taxt_RegularityCB4Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_RegularityCB5Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_WallsCBSelect(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_RoofCB1Select(self, obj=None):
        self.taxt_ValidateRoof()
        self.taxt_BuildTaxonomy()

    def taxt_RoofCB2Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_RoofCB3Select(self, obj=None):
        self.taxt_ValidateRoof()
        self.taxt_BuildTaxonomy()

    def taxt_RoofCB4Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_RoofCB5Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_FoundationsCBSelect(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_FloorCB1Select(self, obj=None):
        self.taxt_ValidateFloor()
        self.taxt_BuildTaxonomy()

    def taxt_FloorCB2Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_FloorCB3Select(self, obj=None):
        self.taxt_BuildTaxonomy()

    def taxt_ValidateSystem1(self):

        self.SystemCB21.empty()

        if self.SystemCB11.val() == 0 or self.SystemCB11.val() == 1:
            self.SystemCB21.disabled(True)

        else:
            self.SystemCB21.items([
                'Ductility unknown',
                'Ductile',
                'Non-ductile',
                'Base isolation and/or energy dissipation devices',
            ], val=0)
            self.SystemCB21.disabled(False)


    def taxt_ValidateSystem2(self):

        self.SystemCB22.empty()

        if self.SystemCB12.val() == 0 or self.SystemCB12.val() == 1:
            self.SystemCB22.disabled(True)

        else:
            self.SystemCB22.items([
                'Ductility unknown',
                'Ductile',
                'Non-ductile',
                'Base isolation and/or energy dissipation devices',
            ], val=0)
            self.SystemCB22.disabled(False)


    def taxt_ValidateMaterial1(self):
        self.MaterialCB21.empty()
        self.MaterialCB31.empty()
        self.MaterialCB41.empty()
        self.SystemCB11.empty()

        if self.MaterialCB11.val() == 0:
            self.MaterialCB21.disabled(True)
            self.MaterialCB31.disabled(True)
            self.MaterialCB41.disabled(True)

        elif self.MaterialCB11.val() == 2:
            self.MaterialCB21.items([
                'Unknown concrete technology',
                'Cast-in-place concrete',
                'Precast concrete',
            ], val=0)
            self.MaterialCB21.disabled(False)

        elif self.MaterialCB11.val() == 1 or  self.MaterialCB11.val() == 3 or self.MaterialCB11.val() == 4:
            self.MaterialCB21.items([
                'Unknown concrete technology',
                'Cast-in-place concrete',
                'Precast concrete',
                'Cast-in-place prestressed concrete',
                'Precast prestressed concrete',
            ], val=0)
            self.MaterialCB21.disabled(False)

        elif self.MaterialCB11.val() == 5:
            self.MaterialCB21.items([
                'Steel, unknown ',
                'Cold-formed steel members',
                'Hot-rolled steel members',
                'Steel, other ',
            ], val=0)
            self.MaterialCB21.disabled(False)

        elif self.MaterialCB11.val() == 6:
            self.MaterialCB21.items([
                'Metal, unknown ',
                'Iron',
                'Metal, other ',
            ], val=0)
            self.MaterialCB21.disabled(False)

        elif (self.MaterialCB11.val() > 6 and
                 self.MaterialCB11.val() < 11):
            self.MaterialCB21.items([
                'Masonry unit, unknown',
                'Adobe blocks',
                'Stone, unknown technology',
                'Rubble (field stone) or semi-dressed stone',
                'Dressed stone',
                'Fired clay unit, unknown type',
                'Fired clay solid bricks',
                'Fired clay hollow bricks',
                'Fired clay hollow blocks or tiles',
                'Concrete blocks, unknown type',
                'Concrete blocks, solid',
                'Concrete blocks, hollow',
                'Masonry unit, other',
            ], val=0)
            self.MaterialCB21.disabled(False)

            if self.MaterialCB11.val() == 10:
                self.MaterialCB41.items([
                'Unknown reinforcement',
                'Steel-reinforced',
                'Wood-reinforced',
                'Bamboo-, cane- or rope-reinforced',
                'Fibre reinforcing mesh',
                'Reinforced concrete bands',
                ], val=0)
                self.MaterialCB41.disabled(False)


        elif self.MaterialCB11.val() > 10 and self.MaterialCB11.val() < 14:
            self.MaterialCB21.items([
                'Unknown earth technology',
                'Rammed earth',
                'Cob or wet construction',
                'Earth technology, other',
            ], val=0)
            self.MaterialCB21.disabled(False)

        elif self.MaterialCB11.val() == 14:
            self.MaterialCB21.items([
                'Wood, unknown',
                'Heavy wood',
                'Light wood members',
                'Solid wood',
                'Wattle and daub',
                'Bamboo',
                'Wood, other',
            ], val=0)
            self.MaterialCB21.disabled(False)

        else:
            self.MaterialCB21.disabled(True)
            self.MaterialCB31.disabled(True)
            self.MaterialCB41.disabled(True)


        if self.MaterialCB11.val() == 5:
            self.MaterialCB31.items([
                'Unknown connection',
                'Welded connections',
                'Riveted connections',
                'Bolted connections',
            ], val=0)
            self.MaterialCB31.disabled(False)

        elif (self.MaterialCB11.val() > 6 and
                 self.MaterialCB11.val() < 11):
            self.MaterialCB31.items([
                'Mortar type, unknown',
                'No mortar',
                'Mud mortar',
                'Lime mortar',
                'Cement mortar',
                'Cement:lime mortar',
                'Stone, unknown type',
                'Limestone',
                'Sandstone',
                'Tuff',
                'Slate',
                'Granite',
                'Basalt',
                'Stone, other type',
            ], val=0)
            self.MaterialCB31.disabled(False)

        else:
            self.MaterialCB31.disabled(True)


        if self.MaterialCB11.val() > 10 and self.MaterialCB11.val() < 14:
            self.SystemCB11.items([
                'Unknown lateral load-resisting system',
                'No lateral load-resisting system',
                'Wall',
                'Hybrid lateral load-resisting system',
                'Other lateral load-resisting system',
            ], val=0)

        elif ((self.MaterialCB11.val() > 6 and self.MaterialCB11.val() < 11) or
                 self.MaterialCB11.val() == 14):
            self.SystemCB11.items([
                'Unknown lateral load-resisting system',
                'No lateral load-resisting system',
                'Moment frame',
                'Post and beam',
                'Wall',
                'Hybrid lateral load-resisting system',
                'Other lateral load-resisting system',
            ], val=0)

        else:
            self.SystemCB11.items([
                'Unknown lateral load-resisting system',
                'No lateral load-resisting system',
                'Moment frame',
                'Infilled frame',
                'Braced frame',
                'Post and beam',
                'Wall',
                'Dual frame-wall system',
                'Flat slab/plate or waffle slab',
                'Infilled flat slab/plate or infilled waffle slab',
                'Hybrid lateral load-resisting system',
                'Other lateral load-resisting system',
            ], val=0)


        self.SystemCB11.val(0)
        self.taxt_ValidateSystem1()


    def taxt_ValidateMaterial2(self):
        self.MaterialCB22.empty()
        self.MaterialCB32.empty()
        self.MaterialCB42.empty()
        self.SystemCB12.empty()

        if self.MaterialCB12.val() == 0:
            self.MaterialCB22.disabled(True)
            self.MaterialCB32.disabled(True)
            self.MaterialCB42.disabled(True)

        elif self.MaterialCB12.val() == 2:
            self.MaterialCB22.items([
                'Unknown concrete technology',
                'Cast-in-place concrete',
                'Precast concrete',
            ], val=0)
            self.MaterialCB22.disabled(False)

        elif self.MaterialCB12.val() == 1 or  self.MaterialCB12.val() == 3 or self.MaterialCB12.val() == 4:
            self.MaterialCB22.items([
                'Unknown concrete technology',
                'Cast-in-place concrete',
                'Precast concrete',
                'Cast-in-place prestressed concrete',
                'Precast prestressed concrete',
            ], val=0)
            self.MaterialCB22.disabled(False)

        elif self.MaterialCB12.val() == 5:
            self.MaterialCB22.items([
                'Steel, unknown ',
                'Cold-formed steel members',
                'Hot-rolled steel members',
                'Steel, other ',
            ], val=0)
            self.MaterialCB22.disabled(False)

        elif self.MaterialCB12.val() == 6:
            self.MaterialCB22.items([
                'Metal, unknown ',
                'Iron',
                'Metal, other ',
            ], val=0)
            self.MaterialCB22.disabled(False)

        elif (self.MaterialCB12.val() > 6 and
                 self.MaterialCB12.val() < 11):
            self.MaterialCB22.items([
                'Masonry unit, unknown',
                'Adobe blocks',
                'Stone, unknown technology',
                'Rubble (field stone) or semi-dressed stone',
                'Dressed stone',
                'Fired clay unit, unknown type',
                'Fired clay solid bricks',
                'Fired clay hollow bricks',
                'Fired clay hollow blocks or tiles',
                'Concrete blocks, unknown type',
                'Concrete blocks, solid',
                'Concrete blocks, hollow',
                'Masonry unit, other',
            ], val=0)
            self.MaterialCB22.disabled(False)

            if self.MaterialCB12.val() == 10:
                self.MaterialCB42.items([
                'Unknown reinforcement',
                'Steel-reinforced',
                'Wood-reinforced',
                'Bamboo-, cane- or rope-reinforced',
                'Fibre reinforcing mesh',
                'Reinforced concrete bands',
                ], val=0)
                self.MaterialCB42.disabled(False)


        elif self.MaterialCB12.val() > 10 and self.MaterialCB12.val() < 14:
            self.MaterialCB22.items([
                'Unknown earth technology',
                'Rammed earth',
                'Cob or wet construction',
                'Earth technology, other',
            ], val=0)
            self.MaterialCB22.disabled(False)

        elif self.MaterialCB12.val() == 14:
            self.MaterialCB22.items([
                'Wood, unknown',
                'Heavy wood',
                'Light wood members',
                'Solid wood',
                'Wattle and daub',
                'Bamboo',
                'Wood, other',
            ], val=0)
            self.MaterialCB22.disabled(False)

        else:
            self.MaterialCB22.disabled(True)
            self.MaterialCB32.disabled(True)
            self.MaterialCB42.disabled(True)


        if self.MaterialCB12.val() == 5:
            self.MaterialCB32.items([
                'Unknown connection',
                'Welded connections',
                'Riveted connections',
                'Bolted connections',
            ], val=0)
            self.MaterialCB32.disabled(False)

        elif (self.MaterialCB12.val() > 6 and
                 self.MaterialCB12.val() < 11):
            self.MaterialCB32.items([
                'Mortar type, unknown',
                'No mortar',
                'Mud mortar',
                'Lime mortar',
                'Cement mortar',
                'Cement:lime mortar',
                'Stone, unknown type',
                'Limestone',
                'Sandstone',
                'Tuff',
                'Slate',
                'Granite',
                'Basalt',
                'Stone, other type',
            ], val=0)
            self.MaterialCB32.disabled(False)

        else:
            self.MaterialCB32.disabled(True)


        if self.MaterialCB12.val() > 10 and self.MaterialCB12.val() < 14:
            self.SystemCB12.items([
                'Unknown lateral load-resisting system',
                'No lateral load-resisting system',
                'Wall',
                'Hybrid lateral load-resisting system',
                'Other lateral load-resisting system',
            ], val=0)

        elif ((self.MaterialCB12.val() > 6 and self.MaterialCB12.val() < 11) or
                 self.MaterialCB12.val() == 14):
            self.SystemCB12.items([
                'Unknown lateral load-resisting system',
                'No lateral load-resisting system',
                'Moment frame',
                'Post and beam',
                'Wall',
                'Hybrid lateral load-resisting system',
                'Other lateral load-resisting system',
            ], val=0)

        else:
            self.SystemCB12.items([
                'Unknown lateral load-resisting system',
                'No lateral load-resisting system',
                'Moment frame',
                'Infilled frame',
                'Braced frame',
                'Post and beam',
                'Wall',
                'Dual frame-wall system',
                'Flat slab/plate or waffle slab',
                'Infilled flat slab/plate or infilled waffle slab',
                'Hybrid lateral load-resisting system',
                'Other lateral load-resisting system',
            ], val=0)


        self.SystemCB12.val(0)
        self.taxt_ValidateSystem2()


    def taxt_ValidateRoof(self):
        self.RoofCB4.empty()
        if self.RoofCB3.val() == 0 or self.RoofCB3.val() == 7:
            self.RoofCB4.disabled(True)

        elif self.RoofCB3.val() == 1:
            self.RoofCB4.items([
                'Masonry roof, unknown',
                'Vaulted masonry roof',
                'Shallow-arched masonry roof',
                'Composite masonry and concrete roof system',
            ], val=0)
            self.RoofCB4.disabled(False)

        elif self.RoofCB3.val() == 2:
            self.RoofCB4.items([
                'Earthen roof, unknown',
                'Vaulted earthen roofs',
            ], val=0)
            self.RoofCB4.disabled(False)

        elif self.RoofCB3.val() == 3:
            self.RoofCB4.items([
                'Concrete roof, unknown',
                'Cast-in-place beamless RC roof',
                'Cast-in-place beam-supported RC roof',
                'Precast concrete roof with RC topping',
                'Precast concrete roof without RC topping',
            ], val=0)
            self.RoofCB4.disabled(False)

        elif self.RoofCB3.val() == 4:
            self.RoofCB4.items([
                'Metal roof, unknown',
                'Metal beams or trusses supporting light roofing',
                'Metal roof beams supporting precast concrete slabs',
                'Composite steel roof deck and concrete slab',
            ], val=0)
            self.RoofCB4.disabled(False)

        elif self.RoofCB3.val() == 5:
            self.RoofCB4.items([
                'Wooden roof, unknown',
                'Wooden structure with light roof covering',
                'Wooden beams or trusses with heavy roof covering',
                'Wood-based sheets on rafters or purlins',
                'Plywood panels or other light-weigth panels for roof',
                'Bamboo, straw or thatch roof',
            ], val=0)
            self.RoofCB4.disabled(False)

        elif self.RoofCB3.val() == 6:
            self.RoofCB4.items([
                'Inflatable or tensile membrane roof',
                'Fabric roof, other',
            ], val=0)
            self.RoofCB4.disabled(False)


    def taxt_ValidateFloor(self):
        self.FloorCB2.empty()

        if (self.FloorCB1.val() == 0 or self.FloorCB1.val() == 1 or self.FloorCB1.val() == 7):
            self.FloorCB2.disabled(True)
        elif self.FloorCB1.val() == 2:
            self.FloorCB2.items([
                'Masonry floor, unknown',
                'Vaulted masonry floor',
                'Shallow-arched masonry floor',
                'Composite cast-in place RC and masonry floor',
            ], val=0)
            self.FloorCB2.disabled(False)

        elif self.FloorCB1.val() == 3:
            self.FloorCB2.items([
                'Earthen floor, unknown',
            ], val=0)
            self.FloorCB2.disabled(False)

        elif self.FloorCB1.val() == 4:
            self.FloorCB2.items([
                'Concrete floor, unknown',
                'Cast-in-place beamless RC floor',
                'Cast-in-place beam-supported RC floor',
                'Precast concrete floor with RC topping',
                'Precast concrete floor without RC topping',
            ], val=0)
            self.FloorCB2.disabled(False)

        elif self.FloorCB1.val() == 5:
            self.FloorCB2.items([
                'Metal floor, unknown',
                'Metal beams, trusses or joists supporting light flooring',
                'Metal floor beams supporting precast concrete slabs',
                'Composite steel deck and concrete slab',
            ], val=0)
            self.FloorCB2.disabled(False)

        elif self.FloorCB1.val() == 6:
            self.FloorCB2.items([
                'Wooden floor, unknown',
                'Wood beams/trusses & joists supporting light flooring',
                'Wood beams/trusses & joists supporting heavy flooring',
                'Wood-based sheets on joists or beams',
                'Plywood panels or other light-weigth panels for floor',
            ], val=0)
            self.FloorCB2.disabled(False)


    def taxt_ValidateHeight(self):
        self.HeightCB2.disabled(True)
        self.HeightCB3.disabled(True)
        self.HeightCB4.disabled(True)
        self.noStoreysE11.disabled(True)
        # self.noStoreysE11.removeClass('gem_field_alert')
        self.noStoreysE12.disabled(True)
        # self.noStoreysE12.removeClass('gem_field_alert')

        self.noStoreysE21.disabled(True)
        # self.noStoreysE21.removeClass('gem_field_alert')
        self.noStoreysE22.disabled(True)
        # self.noStoreysE22.removeClass('gem_field_alert')

        self.noStoreysE31.disabled(True)
        # self.noStoreysE31.removeClass('gem_field_alert')
        self.noStoreysE32.disabled(True)
        # self.noStoreysE32.removeClass('gem_field_alert')
        self.noStoreysE41.disabled(True)
        # self.noStoreysE41.removeClass('gem_field_alert')

        if self.HeightCB1.val() > 0:
            self.HeightCB2.disabled(False)
            self.HeightCB3.disabled(False)
            self.HeightCB4.disabled(False)
            self.noStoreysE11.disabled(False)
            self.noStoreysE12.disabled(False)

            if self.HeightCB1.val() == 1:
                self.noStoreysE11.disabled(False)
                self.noStoreysE12.disabled(False)

            else:
                self.noStoreysE11.disabled(False)
                self.noStoreysE12.disabled(True)


            if self.HeightCB2.val() == 0:
                self.noStoreysE21.disabled(True)
                self.noStoreysE22.disabled(True)

            elif self.HeightCB2.val() == 1:
                self.noStoreysE21.disabled(False)
                self.noStoreysE22.disabled(False)

            else:
                self.noStoreysE21.disabled(False)
                self.noStoreysE22.disabled(True)


            if self.HeightCB3.val() == 0:
                self.noStoreysE31.disabled(True)
                self.noStoreysE32.disabled(True)

            elif self.HeightCB3.val() == 1:
                self.noStoreysE31.disabled(False)
                self.noStoreysE32.disabled(False)

            else:
                self.noStoreysE31.disabled(False)
                self.noStoreysE32.disabled(True)


            if self.HeightCB4.val() == 0:
                self.noStoreysE41.disabled(True)

            else:
                self.noStoreysE41.disabled(False)


        else:
            self.noStoreysE11.disabled(True)
            self.noStoreysE12.disabled(True)


    def taxt_ValidateDate(self):
        if self.DateCB1.val() == 0:
            self.DateE1.disabled(True)
            self.DateE2.disabled(True)

        elif self.DateCB1.val() == 2:
            self.DateE1.disabled(False)
            self.DateE2.disabled(False)

        else:
            self.DateE1.disabled(False)
            self.DateE2.disabled(True)


    def taxt_ValidateRegularity(self):
        self.RegularityCB2.empty()
        self.RegularityCB3.empty()
        self.RegularityCB4.empty()
        self.RegularityCB5.empty()

        default_cb2 = 0
        default_cb3 = 0

        if (self.RegularityCB1.val() == 0 or
            self.RegularityCB1.val() == 1):
            self.RegularityCB2.disabled(True)
            self.RegularityCB3.disabled(True)
            self.RegularityCB4.disabled(True)
            self.RegularityCB5.disabled(True)
            self._gem_taxonomy_regularity_postinit = -1

        elif self.RegularityCB1.val() == 2: # /* irregular case */
            # /* RegularityCB2 related part */
            reg_cb2_items = []
            if self.RegularityCB3.val() == 0 or self.RegularityCB3.val() == -1:
                reg_cb2_items.append('No irregularity')
                self.RegularityCB2.first_disabled(True)
                default_cb2 = 1
            else:
                reg_cb2_items.append('No irregularity')

            reg_cb2_items.append('Torsion eccentricity')
            reg_cb2_items.append('Re-entrant corner')
            reg_cb2_items.append('Other plan irregularity')

            self.RegularityCB2.disabled(False)
            self.RegularityCB2.items(reg_cb2_items)
            self.RegularityCB2.val(default_cb2)

            # /* RegularityCB3 related part */
            reg_cb3_items = []
            if self.RegularityCB2.val() == 0 or self.RegularityCB2.val() == -1:
                reg_cb3_items.append('No irregularity')
                self.RegularityCB3.first_disabled(True)
                default_cb3 = 1
                self._gem_taxonomy_regularity_postinit = 2
            else:
                reg_cb3_items.append('No irregularity')

            reg_cb3_items.append('Soft storey')
            reg_cb3_items.append('Cripple wall')
            reg_cb3_items.append('Short column')
            reg_cb3_items.append('Pounding potential')
            reg_cb3_items.append('Setback')
            reg_cb3_items.append('Change in vertical structure')
            reg_cb3_items.append('Other vertical irregularity')
            self.RegularityCB3.disabled(False)
            self.RegularityCB3.items(reg_cb3_items)
            self.RegularityCB3.val(default_cb3)

        self.taxt_RegularityCB2Select(-1)
        self.taxt_RegularityCB3Select(-1)
        if default_cb2 == 1:
            self._gem_taxonomy_regularity_postinit = 2
        elif default_cb3 == 1:
            self._gem_taxonomy_regularity_postinit = 3


    def taxt_ValidateRegularity2(self):

        self.RegularityCB4.empty()

        if self.RegularityCB1.val() < 2 or self.RegularityCB2.val() == 0 or self.RegularityCB2.val() == -1:
            self.RegularityCB4.disabled(True)
        else:
            self.RegularityCB4.items([
                'No irregularity',
                'Torsion eccentricity',
                'Re-entrant corner',
                'Other plan irregularity',
            ], val=0)
            self.RegularityCB4.disabled(False)

        self.taxt_ValidateRegularityCross23("2")


    def taxt_ValidateRegularity3(self):

        self.RegularityCB5.empty()

        if (self.RegularityCB1.val() < 2 or self.RegularityCB3.val() == 0
            or self.RegularityCB3.val() is None):
            self.RegularityCB5.disabled(True)

        else:
            self.RegularityCB5.items([
                'No irregularity',
                'Soft storey',
                'Cripple wall',
                'Short column',
                'Pounding potential',
                'Setback',
                'Change in vertical structure',
                'Other vertical irregularity',
            ], val=0)
            self.RegularityCB5.disabled(False)

        self.taxt_ValidateRegularityCross23("3")


    def taxt_ValidateRegularityCross23(self, who):
        if who == "2":
            if self.RegularityCB2.val() != 0:
                self.RegularityCB3.first_disabled(False)
            else:
                self.RegularityCB3.first_disabled(True)

        if who == "3":
            if self.RegularityCB3.val() != 0:
                self.RegularityCB2.first_disabled(False)
            else:
                self.RegularityCB2.first_disabled(True)

    def taxt_ValidateOccupancy(self):

        self.OccupancyCB2.empty()

        if self.OccupancyCB1.val() == 0:
            self.OccupancyCB2.disabled(True)

        elif self.OccupancyCB1.val() == 1:
            self.OccupancyCB2.items([
                'Residential, unknown type',
                'Single dwelling',
                'Multi-unit, unknown type',
                '2 Units (Duplex)',
                '3-4 Units',
                '5-9 Units',
                '10-19 Units',
                '20-49 Units',
                '50+ Units',
                'Temporary lodging',
                'Institutional housing',
                'Mobile home',
                'Informal housing',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 2:
            self.OccupancyCB2.items([
                'Commercial and public, unknown type',
                'Retail trade',
                'Wholesale trade and storage (warehouse)',
                'Offices, professional/technical services',
                'Hospital/medical clinic',
                'Entertainment',
                'Public building',
                'Covered parking garage',
                'Bus station',
                'Railway station',
                'Airport',
                'Recreation and leisure',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 3:
            self.OccupancyCB2.items([
                'Mixed, unknown type',
                'Mostly residential and commercial',
                'Mostly commercial and residential',
                'Mostly commercial and industrial',
                'Mostly residential and industrial',
                'Mostly industrial and commercial',
                'Mostly industrial and residential',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 4:
            self.OccupancyCB2.items([
                'Industrial, unknown type',
                'Heavy industrial',
                'Light industrial',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 5:
            self.OccupancyCB2.items([
                'Agriculture, unknown type',
                'Produce storage',
                'Animal shelter',
                'Agricultural processing',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 6:
            self.OccupancyCB2.items([
                'Assembly, unknown type',
                'Religious gathering',
                'Arena',
                'Cinema or concert hall',
                'Other gatherings',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 7:
            self.OccupancyCB2.items([
                'Government, unknown type',
                'Government, general services',
                'Government, emergency response',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        elif self.OccupancyCB1.val() == 8:
            self.OccupancyCB2.items([
                'Education, unknown type',
                'Pre-school facility',
                'School',
                'College/university, offices and/or classrooms',
                'College/university, research facilities and/or labs',
            ], val=0)
            self.OccupancyCB2.disabled(False)

        else:
            self.OccupancyCB2.disabled(True)


    def taxt_BuildTaxonomy(self):

        ResTax = None
        ResTaxFull = self.BuildTaxonomyString(0)
        out_type = self.OutTypeCB.val()

        height1 = self.HeightCB1.val()
        height2 = self.HeightCB2.val()
        height3 = self.HeightCB3.val()
        height4 = self.HeightCB4.val()
        date1 = self.DateCB1.val()
        validated = False
        validate_msg = ""
        h11 = True
        h12 = True
        h21 = True
        h22 = True
        h31 = True
        h32 = True
        d1 = True
        d2 = True

        if height1 > 0:
            if not is_not_negative_int(self.noStoreysE11.val()):
                if height1 == 1:
                    validate_msg += "Number of storey above ground: lower limit not positive integer. "

                else:
                    validate_msg += "Number of storey above ground: not positive integer. "

                # self.noStoreysE11.addClass('gem_field_alert')
                h11 = False

            else:
                # self.noStoreysE11.removeClass('gem_field_alert')
                pass


        if height1 == 1:
            if not is_not_negative_int(self.noStoreysE12.val()):
                validate_msg += "Number of storey above ground: upper limit not positive integer. "
                # self.noStoreysE12.addClass('gem_field_alert')
                h12 = False

            elif h11 is True and int(self.noStoreysE11.val()) == int(self.noStoreysE12.val()):
                validate_msg += "Number of storey above ground: invalid range."
                # self.noStoreysE12.addClass('gem_field_alert')
                h12 = False

            else:
                # self.noStoreysE12.removeClass('gem_field_alert')
                pass


            #  swap items if wrong order
            if h11 and h12:
                if int(self.noStoreysE11.val()) > int(self.noStoreysE12.val()):
                    swap = self.noStoreysE11.val()
                    self.noStoreysE11.val(self.noStoreysE12.val())
                    self.noStoreysE12.val(swap)

        if height2 > 0:
            if not is_not_negative_int(self.noStoreysE21.val()):
                if height2 == 1:
                    validate_msg += "Number of storey above ground: lower limit not positive integer. "
                else:
                    validate_msg += "Number of storey above ground: not positive integer. "

                # self.noStoreysE21.addClass('gem_field_alert')
                h21 = False

            else:
                # self.noStoreysE21.removeClass('gem_field_alert')
                pass



        if height2 == 1:
            if not is_not_negative_int(self.noStoreysE22.val()):
                validate_msg += "Number of storey above ground: upper limit not positive integer. "
                # self.noStoreysE22.addClass('gem_field_alert')
                h22 = False

            elif h21 is True and int(self.noStoreysE21.val()) == int(self.noStoreysE22.val()):
                validate_msg += "Number of storey above ground: invalid range."
                # self.noStoreysE22.addClass('gem_field_alert')
                h22 = False

            else:
                # self.noStoreysE22.removeClass('gem_field_alert')
                pass


            #  swap items if wrong order
            if h21 and h22:
                if int(self.noStoreysE21.val()) > int(self.noStoreysE22.val()):
                    swap = self.noStoreysE21.val()
                    self.noStoreysE21.val(self.noStoreysE22.val())
                    self.noStoreysE22.val(swap)

        if height3 > 0:
            if not is_not_negative_float(self.noStoreysE31.val()):
                if height3 == 1:
                    validate_msg += "Height of ground floor level: lower limit not positive real"
                else:
                    validate_msg += "Height of ground floor level: not positive real. "
                # self.noStoreysE31.addClass('gem_field_alert')
                h31 = False

            else:
                # self.noStoreysE31.removeClass('gem_field_alert')
                pass

        if height3 == 1:
            if not is_not_negative_float(self.noStoreysE32.val()):
                validate_msg += "Height of ground floor level: upper limit not positive real. "
                # self.noStoreysE32.addClass('gem_field_alert')
                h32 = False

            elif h31 is True and int(self.noStoreysE31.val()) == int(self.noStoreysE32.val()):
                validate_msg += "Height of ground floor level: invalid range."
                # self.noStoreysE32.addClass('gem_field_alert')
                h32 = False

            else:
                self.noStoreysE32.removeClass('gem_field_alert')


            # swap items if wrong order
            if h31 and h32:
                if float(self.noStoreysE31.val()) > float(self.noStoreysE32.val()):
                    swap = self.noStoreysE31.val()
                    self.noStoreysE31.val(self.noStoreysE32.val())
                    self.noStoreysE32.val(swap)

        if height4 > 0:
            if not is_in_rect_angle_float(self.noStoreysE41.val()):
                validate_msg += "Slope of the ground: it is not positive real between 0 and 90. "
                # self.noStoreysE41.addClass('gem_field_alert')
            else:
                # self.noStoreysE41.removeClass('gem_field_alert')
                pass



        if date1 > 0:
            if not is_not_negative_int(self.DateE1.val()) or len(self.DateE1.val()) > 4:
                if date1 == 2:
                    validate_msg += "Date of construction or retrofit: lower limit is not a valid date. "
                else:
                    validate_msg += "Date of construction or retrofit: it is not a valid date. "

                # self.DateE1.addClass('gem_field_alert')
                d1 = False

            else:
                # self.DateE1.removeClass('gem_field_alert')
                pass


        if date1 == 2:
            if not is_not_negative_int(self.DateE2.val()) or len(self.DateE2.val()) > 4:
                validate_msg += "Date of construction or retrofit: upper limit is not a valid date. "
                # self.DateE2.addClass('gem_field_alert')
                d2 = False

            elif d1 is True and int(self.DateE1.val()) == int(self.DateE2.val()):
                validate_msg += "Date of construction or retrofit: invalid range."
                d2 = False

            else:
                # self.DateE2.removeClass('gem_field_alert')
                pass

            # swap items if wrong order
            if d1 and d2:
                if int(self.DateE1.val()) > int(self.DateE2.val()):
                    swap = self.DateE1.val()
                    self.DateE1.val(self.DateE2.val())
                    self.DateE2.val(swap)

        if validate_msg == "":
            validated = True

        if validated:
            if out_type != 0:
                ResTax = self.BuildTaxonomyString(out_type)
            else:
                ResTax = ResTaxFull

            self._gem_taxonomy_form = ResTax
            self._gem_taxonomy_form_full = ResTaxFull

            getattr(self, "resultE" + self._virt_sfx).val(ResTax)
            # self.permalink.attr("href", taxt_prefix + "/" +  ResTaxFull)

        else:
            self._gem_taxonomy_form = ""
            self._gem_taxonomy_form_full = ""
            getattr(self, "resultE" + self._virt_sfx).val(validate_msg)
            # self.permalink.attr("href", taxt_prefix)


    def BuildTaxonomyString(self, out_type):
        taxonomy = [""] * 50

        ResTax = None
        direction1 = None
        direction2 = None

        # /* Structural System: Direction X */

        if self.MaterialCB11.val() == 0 and (out_type == 0):
            taxonomy[0] = 'MAT99'
        if self.MaterialCB11.val() == 1:
            taxonomy[0] = 'C99'
        if self.MaterialCB11.val() == 2:
            taxonomy[0] = 'CU'
        if self.MaterialCB11.val() == 3:
            taxonomy[0] = 'CR'
        if self.MaterialCB11.val() == 4:
            taxonomy[0] = 'SRC'

        if (self.MaterialCB11.val() > 0) and (self.MaterialCB11.val() < 5):
            if (self.MaterialCB21.val() == 0) and (out_type == 0):
                taxonomy[1] = '+CT99'
            if self.MaterialCB21.val() == 1:
                taxonomy[1] = '+CIP'
            if self.MaterialCB21.val() == 2:
                taxonomy[1] = '+PC'
            if self.MaterialCB21.val() == 3:
                taxonomy[1] = '+CIPPS'
            if self.MaterialCB21.val() == 4:
                taxonomy[1] = '+PCPS'

        if self.MaterialCB11.val() == 5:
            taxonomy[0] = 'S'
            if self.MaterialCB21.val() == 0 and (out_type == 0):
                taxonomy[1] = '+S99'
            if self.MaterialCB21.val() == 1:
                taxonomy[1] = '+SL'
            if self.MaterialCB21.val() == 2:
                taxonomy[1] = '+SR'
            if self.MaterialCB21.val() == 3:
                taxonomy[1] = '+SO'


        if self.MaterialCB11.val() == 6:
            taxonomy[0] = 'ME'
            if self.MaterialCB21.val() == 0 and (out_type == 0):
                taxonomy[1] = '+ME99'
            if self.MaterialCB21.val() == 1:
                taxonomy[1] = '+MEIR'
            if self.MaterialCB21.val() == 2:
                taxonomy[1] = '+MEO'


        if self.MaterialCB11.val() == 5:
            if self.MaterialCB31.val() == 0 and (out_type == 0):
                taxonomy[2] = '+SC99'
            if self.MaterialCB31.val() == 1:
                taxonomy[2] = '+WEL'
            if self.MaterialCB31.val() == 2:
                taxonomy[2] = '+RIV'
            if self.MaterialCB31.val() == 3:
                taxonomy[2] = '+BOL'


        if self.MaterialCB11.val() > 6 and self.MaterialCB11.val() < 11:
            if self.MaterialCB11.val() == 7:
                taxonomy[0] = 'M99'
            if self.MaterialCB11.val() == 8:
                taxonomy[0] = 'MUR'
            if self.MaterialCB11.val() == 9:
                taxonomy[0] = 'MCF'

            if self.MaterialCB21.val() == 0 and (out_type == 0):
                taxonomy[1] = '+MUN99'
            if self.MaterialCB21.val() == 1:
                taxonomy[1] = '+ADO'
            if self.MaterialCB21.val() == 2:
                taxonomy[1] = '+ST99'
            if self.MaterialCB21.val() == 3:
                taxonomy[1] = '+STRUB'
            if self.MaterialCB21.val() == 4:
                taxonomy[1] = '+STDRE'
            if self.MaterialCB21.val() == 5:
                taxonomy[1] = '+CL99'
            if self.MaterialCB21.val() == 6:
                taxonomy[1] = '+CLBRS'
            if self.MaterialCB21.val() == 7:
                taxonomy[1] = '+CLBRH'
            if self.MaterialCB21.val() == 8:
                taxonomy[1] = '+CLBLH'
            if self.MaterialCB21.val() == 9:
                taxonomy[1] = '+CB99'
            if self.MaterialCB21.val() == 10:
                taxonomy[1] = '+CBS'
            if self.MaterialCB21.val() == 11:
                taxonomy[1] = '+CBH'
            if self.MaterialCB21.val() == 12:
                taxonomy[1] = '+MO'

            if self.MaterialCB11.val() == 10:
                taxonomy[0] = 'MR'
                if (self.MaterialCB41.val() == 0) and (out_type == 0):
                    taxonomy[34] = '+MR99'
                if self.MaterialCB41.val() == 1:
                    taxonomy[34] = '+RS'
                if self.MaterialCB41.val() == 2:
                    taxonomy[34] = '+RW'
                if self.MaterialCB41.val() == 3:
                    taxonomy[34] = '+RB'
                if self.MaterialCB41.val() == 4:
                    taxonomy[34] = '+RCM'
                if self.MaterialCB41.val() == 5:
                    taxonomy[34] = '+RCB'


            if (self.MaterialCB31.val() == 0) and (out_type == 0):
                taxonomy[2] = '+MO99'
            if self.MaterialCB31.val() == 1:
                taxonomy[2] = '+MON'
            if self.MaterialCB31.val() == 2:
                taxonomy[2] = '+MOM'
            if self.MaterialCB31.val() == 3:
                taxonomy[2] = '+MOL'
            if self.MaterialCB31.val() == 4:
                taxonomy[2] = '+MOC'
            if self.MaterialCB31.val() == 5:
                taxonomy[2] = '+MOCL'
            if self.MaterialCB31.val() == 6:
                taxonomy[2] = '+SP99'
            if self.MaterialCB31.val() == 7:
                taxonomy[2] = '+SPLI'
            if self.MaterialCB31.val() == 8:
                taxonomy[2] = '+SPSA'
            if self.MaterialCB31.val() == 9:
                taxonomy[2] = '+SPTU'
            if self.MaterialCB31.val() == 10:
                taxonomy[2] = '+SPSL'
            if self.MaterialCB31.val() == 11:
                taxonomy[2] = '+SPGR'
            if self.MaterialCB31.val() == 12:
                taxonomy[2] = '+SPBA'
            if self.MaterialCB31.val() == 13:
                taxonomy[2] = '+SPO'


        if (self.MaterialCB11.val()>10) and (self.MaterialCB11.val()<14):
            if self.MaterialCB11.val() == 11:
                taxonomy[0] = 'E99'
            if self.MaterialCB11.val() == 12:
                taxonomy[0] = 'EU'
            if self.MaterialCB11.val() == 13:
                taxonomy[0] = 'ER'

            if (self.MaterialCB21.val() == 0) and (out_type == 0):
                taxonomy[1] = '+ET99'
            if self.MaterialCB21.val() == 1:
                taxonomy[1] = '+ETR'
            if self.MaterialCB21.val() == 2:
                taxonomy[1] = '+ETC'
            if self.MaterialCB21.val() == 3:
                taxonomy[1] = '+ETO'


        if self.MaterialCB11.val() == 14:
            taxonomy[0] = 'W'
            if (self.MaterialCB21.val() == 0) and (out_type == 0):
                taxonomy[1] = '+W99'
            if self.MaterialCB21.val() == 1:
                taxonomy[1] = '+WHE'
            if self.MaterialCB21.val() == 2:
                taxonomy[1] = '+WLI'
            if self.MaterialCB21.val() == 3:
                taxonomy[1] = '+WS'
            if self.MaterialCB21.val() == 4:
                taxonomy[1] = '+WWD'
            if self.MaterialCB21.val() == 5:
                taxonomy[1] = '+WBB'
            if self.MaterialCB21.val() == 6:
                taxonomy[1] = '+WO'


        if self.MaterialCB11.val() == 15:
            taxonomy[0] = 'MATO'

        if (self.SystemCB11.val() == 0) and (out_type == 0):
            taxonomy[3] = 'L99'

        if (self.MaterialCB11.val() > 10) and (self.MaterialCB11.val() < 14):
            if self.SystemCB11.val() == 1:
                taxonomy[3] = 'LN'
            if self.SystemCB11.val() == 2:
                taxonomy[3] = 'LWAL'
            if self.SystemCB11.val() == 3:
                taxonomy[3] = 'LH'
            if self.SystemCB11.val() == 4:
                taxonomy[3] = 'LO'

        elif ((self.MaterialCB11.val()>6) and (self.MaterialCB11.val()<11)) or (self.MaterialCB11.val() == 14):
            if self.SystemCB11.val() == 1:
                taxonomy[3] = 'LN'
            if self.SystemCB11.val() == 2:
                taxonomy[3] = 'LFM'
            if self.SystemCB11.val() == 3:
                taxonomy[3] = 'LPB'
            if self.SystemCB11.val() == 4:
                taxonomy[3] = 'LWAL'
            if self.SystemCB11.val() == 5:
                taxonomy[3] = 'LH'
            if self.SystemCB11.val() == 6:
                taxonomy[3] = 'LO'

        else:
            if self.SystemCB11.val() == 1:
                taxonomy[3] = 'LN'
            if self.SystemCB11.val() == 2:
                taxonomy[3] = 'LFM'
            if self.SystemCB11.val() == 3:
                taxonomy[3] = 'LFINF'
            if self.SystemCB11.val() == 4:
                taxonomy[3] = 'LFBR'
            if self.SystemCB11.val() == 5:
                taxonomy[3] = 'LPB'
            if self.SystemCB11.val() == 6:
                taxonomy[3] = 'LWAL'
            if self.SystemCB11.val() == 7:
                taxonomy[3] = 'LDUAL'
            if self.SystemCB11.val() == 8:
                taxonomy[3] = 'LFLS'
            if self.SystemCB11.val() == 9:
                taxonomy[3] = 'LFLSINF'
            if self.SystemCB11.val() == 10:
                taxonomy[3] = 'LH'
            if self.SystemCB11.val() == 11:
                taxonomy[3] = 'LO'


        if self.SystemCB11.val() > 0:
            if (self.SystemCB21.val() == 0) and (out_type == 0):
                taxonomy[4] = '+DU99'
            if self.SystemCB21.val() == 1:
                taxonomy[4] = '+DUC'
            if self.SystemCB21.val() == 2:
                taxonomy[4] = '+DNO'
            if self.SystemCB21.val() == 3:
                taxonomy[4] = '+DBD'


        # /* Structural System: Direction Y */

        if self.MaterialCB12.val() == 0 and (out_type == 0):
            taxonomy[5] = 'MAT99'
        if self.MaterialCB12.val() == 1:
            taxonomy[5] = 'C99'
        if self.MaterialCB12.val() == 2:
            taxonomy[5] = 'CU'
        if self.MaterialCB12.val() == 3:
            taxonomy[5] = 'CR'
        if self.MaterialCB12.val() == 4:
            taxonomy[5] = 'SRC'

        if (self.MaterialCB12.val() > 0) and (self.MaterialCB12.val() < 5):
            if (self.MaterialCB22.val() == 0) and (out_type == 0):
                taxonomy[6] = '+CT99'
            if self.MaterialCB22.val() == 1:
                taxonomy[6] = '+CIP'
            if self.MaterialCB22.val() == 2:
                taxonomy[6] = '+PC'
            if self.MaterialCB22.val() == 3:
                taxonomy[6] = '+CIPPS'
            if self.MaterialCB22.val() == 4:
                taxonomy[6] = '+PCPS'

        if self.MaterialCB12.val() == 5:
            taxonomy[5] = 'S'
            if self.MaterialCB22.val() == 0 and (out_type == 0):
                taxonomy[6] = '+S99'
            if self.MaterialCB22.val() == 1:
                taxonomy[6] = '+SL'
            if self.MaterialCB22.val() == 2:
                taxonomy[6] = '+SR'
            if self.MaterialCB22.val() == 3:
                taxonomy[6] = '+SO'


        if self.MaterialCB12.val() == 6:
            taxonomy[5] = 'ME'
            if self.MaterialCB22.val() == 0 and (out_type == 0):
                taxonomy[6] = '+ME99'
            if self.MaterialCB22.val() == 1:
                taxonomy[6] = '+MEIR'
            if self.MaterialCB22.val() == 2:
                taxonomy[6] = '+MEO'


        if self.MaterialCB12.val() == 5:
            if self.MaterialCB32.val() == 0 and (out_type == 0):
                taxonomy[7] = '+SC99'
            if self.MaterialCB32.val() == 1:
                taxonomy[7] = '+WEL'
            if self.MaterialCB32.val() == 2:
                taxonomy[7] = '+RIV'
            if self.MaterialCB32.val() == 3:
                taxonomy[7] = '+BOL'


        if self.MaterialCB12.val() > 6 and self.MaterialCB12.val() < 11:
            if self.MaterialCB12.val() == 7:
                taxonomy[5] = 'M99'
            if self.MaterialCB12.val() == 8:
                taxonomy[5] = 'MUR'
            if self.MaterialCB12.val() == 9:
                taxonomy[5] = 'MCF'

            if self.MaterialCB22.val() == 0 and (out_type == 0):
                taxonomy[6] = '+MUN99'
            if self.MaterialCB22.val() == 1:
                taxonomy[6] = '+ADO'
            if self.MaterialCB22.val() == 2:
                taxonomy[6] = '+ST99'
            if self.MaterialCB22.val() == 3:
                taxonomy[6] = '+STRUB'
            if self.MaterialCB22.val() == 4:
                taxonomy[6] = '+STDRE'
            if self.MaterialCB22.val() == 5:
                taxonomy[6] = '+CL99'
            if self.MaterialCB22.val() == 6:
                taxonomy[6] = '+CLBRS'
            if self.MaterialCB22.val() == 7:
                taxonomy[6] = '+CLBRH'
            if self.MaterialCB22.val() == 8:
                taxonomy[6] = '+CLBLH'
            if self.MaterialCB22.val() == 9:
                taxonomy[6] = '+CB99'
            if self.MaterialCB22.val() == 10:
                taxonomy[6] = '+CBS'
            if self.MaterialCB22.val() == 11:
                taxonomy[6] = '+CBH'
            if self.MaterialCB22.val() == 12:
                taxonomy[6] = '+MO'

            if self.MaterialCB12.val() == 10:
                taxonomy[5] = 'MR'
                if (self.MaterialCB42.val() == 0) and (out_type == 0):
                    taxonomy[35] = '+MR99'
                if self.MaterialCB42.val() == 1:
                    taxonomy[35] = '+RS'
                if self.MaterialCB42.val() == 2:
                    taxonomy[35] = '+RW'
                if self.MaterialCB42.val() == 3:
                    taxonomy[35] = '+RB'
                if self.MaterialCB42.val() == 4:
                    taxonomy[35] = '+RCM'
                if self.MaterialCB42.val() == 5:
                    taxonomy[35] = '+RCB'


            if (self.MaterialCB32.val() == 0) and (out_type == 0):
                taxonomy[7] = '+MO99'
            if self.MaterialCB32.val() == 1:
                taxonomy[7] = '+MON'
            if self.MaterialCB32.val() == 2:
                taxonomy[7] = '+MOM'
            if self.MaterialCB32.val() == 3:
                taxonomy[7] = '+MOL'
            if self.MaterialCB32.val() == 4:
                taxonomy[7] = '+MOC'
            if self.MaterialCB32.val() == 5:
                taxonomy[7] = '+MOCL'
            if self.MaterialCB32.val() == 6:
                taxonomy[7] = '+SP99'
            if self.MaterialCB32.val() == 7:
                taxonomy[7] = '+SPLI'
            if self.MaterialCB32.val() == 8:
                taxonomy[7] = '+SPSA'
            if self.MaterialCB32.val() == 9:
                taxonomy[7] = '+SPTU'
            if self.MaterialCB32.val() == 10:
                taxonomy[7] = '+SPSL'
            if self.MaterialCB32.val() == 11:
                taxonomy[7] = '+SPGR'
            if self.MaterialCB32.val() == 12:
                taxonomy[7] = '+SPBA'
            if self.MaterialCB32.val() == 13:
                taxonomy[7] = '+SPO'


        if (self.MaterialCB12.val() > 10) and (self.MaterialCB12.val() < 14):
            if self.MaterialCB12.val() == 11:
                taxonomy[5] = 'E99'
            if self.MaterialCB12.val() == 12:
                taxonomy[5] = 'EU'
            if self.MaterialCB12.val() == 13:
                taxonomy[5] = 'ER'

            if (self.MaterialCB22.val() == 0) and (out_type == 0):
                taxonomy[6] = '+ET99'
            if self.MaterialCB22.val() == 1:
                taxonomy[6] = '+ETR'
            if self.MaterialCB22.val() == 2:
                taxonomy[6] = '+ETC'
            if self.MaterialCB22.val() == 3:
                taxonomy[6] = '+ETO'


        if self.MaterialCB12.val() == 14:
            taxonomy[5] = 'W'
            if (self.MaterialCB22.val() == 0) and (out_type == 0):
                taxonomy[6] = '+W99'
            if self.MaterialCB22.val() == 1:
                taxonomy[6] = '+WHE'
            if self.MaterialCB22.val() == 2:
                taxonomy[6] = '+WLI'
            if self.MaterialCB22.val() == 3:
                taxonomy[6] = '+WS'
            if self.MaterialCB22.val() == 4:
                taxonomy[6] = '+WWD'
            if self.MaterialCB22.val() == 5:
                taxonomy[6] = '+WBB'
            if self.MaterialCB22.val() == 6:
                taxonomy[6] = '+WO'


        if self.MaterialCB12.val() == 15:
            taxonomy[5] = 'MATO'

        if (self.SystemCB12.val() == 0) and (out_type == 0):
            taxonomy[8] = 'L99'

        if (self.MaterialCB12.val() > 10) and (self.MaterialCB12.val() < 14):
            if self.SystemCB12.val() == 1:
                taxonomy[8] = 'LN'
            if self.SystemCB12.val() == 2:
                taxonomy[8] = 'LWAL'
            if self.SystemCB12.val() == 3:
                taxonomy[8] = 'LH'
            if self.SystemCB12.val() == 4:
                taxonomy[8] = 'LO'

        elif ((self.MaterialCB12.val() > 6) and (self.MaterialCB12.val() < 11)) or (self.MaterialCB12.val() == 14):
            if self.SystemCB12.val() == 1:
                taxonomy[8] = 'LN'
            if self.SystemCB12.val() == 2:
                taxonomy[8] = 'LFM'
            if self.SystemCB12.val() == 3:
                taxonomy[8] = 'LPB'
            if self.SystemCB12.val() == 4:
                taxonomy[8] = 'LWAL'
            if self.SystemCB12.val() == 5:
                taxonomy[8] = 'LH'
            if self.SystemCB12.val() == 6:
                taxonomy[8] = 'LO'

        else:
            if self.SystemCB12.val() == 1:
                taxonomy[8] = 'LN'
            if self.SystemCB12.val() == 2:
                taxonomy[8] = 'LFM'
            if self.SystemCB12.val() == 3:
                taxonomy[8] = 'LFINF'
            if self.SystemCB12.val() == 4:
                taxonomy[8] = 'LFBR'
            if self.SystemCB12.val() == 5:
                taxonomy[8] = 'LPB'
            if self.SystemCB12.val() == 6:
                taxonomy[8] = 'LWAL'
            if self.SystemCB12.val() == 7:
                taxonomy[8] = 'LDUAL'
            if self.SystemCB12.val() == 8:
                taxonomy[8] = 'LFLS'
            if self.SystemCB12.val() == 9:
                taxonomy[8] = 'LFLSINF'
            if self.SystemCB12.val() == 10:
                taxonomy[8] = 'LH'
            if self.SystemCB12.val() == 11:
                taxonomy[8] = 'LO'


        if self.SystemCB12.val() > 0:
            if (self.SystemCB22.val() == 0) and (out_type == 0):
                taxonomy[9] = '+DU99'
            if self.SystemCB22.val() == 1:
                taxonomy[9] = '+DUC'
            if self.SystemCB22.val() == 2:
                taxonomy[9] = '+DNO'
            if self.SystemCB22.val() == 3:
                taxonomy[9] = '+DBD'


        if self.DateCB1.val() == 0  and (out_type == 0):
            taxonomy[10] = 'Y99'
        if self.DateCB1.val() == 1:
            taxonomy[10] = 'YEX:' + self.DateE1.val()
        elif self.DateCB1.val() == 2:
            taxonomy[10] = 'YBET:' + self.DateE1.val() + "," + self.DateE2.val()
        elif self.DateCB1.val() == 3:
            taxonomy[10] = 'YPRE:' + self.DateE1.val()
        elif self.DateCB1.val() == 4:
            taxonomy[10] = 'YAPP:' + self.DateE1.val()

        if self.HeightCB1.val() == 0:
            if (out_type == 0):
                taxonomy[11] ='H99'

        else:
            if self.HeightCB1.val() == 1:
                taxonomy[11] = 'HBET:' + self.noStoreysE11.val() + ',' + self.noStoreysE12.val()
            if self.HeightCB1.val() == 2:
                taxonomy[11] = 'HEX:' + self.noStoreysE11.val()
            if self.HeightCB1.val() == 3:
                taxonomy[11] = 'HAPP:' + self.noStoreysE11.val()

            if self.HeightCB2.val() == 0 and (out_type == 0):
                taxonomy[12] = '+HB99'
            if self.HeightCB2.val() == 1:
                taxonomy[12] = '+HBBET:' + self.noStoreysE21.val() + ',' + self.noStoreysE22.val()
            if self.HeightCB2.val() == 2:
                taxonomy[12] = '+HBEX:' + self.noStoreysE21.val()
            if self.HeightCB2.val() == 3:
                taxonomy[12] = '+HBAPP:' + self.noStoreysE21.val()

            if self.HeightCB3.val() == 0 and (out_type == 0):
                taxonomy[13] = '+HF99'
            if self.HeightCB3.val() == 1:
                taxonomy[13] = '+HFBET:' + self.noStoreysE31.val() + ',' + self.noStoreysE32.val()
            if self.HeightCB3.val() == 2:
                taxonomy[13] = '+HFEX:' + self.noStoreysE31.val()
            if self.HeightCB3.val() == 3:
                taxonomy[13] = '+HFAPP:' + self.noStoreysE31.val()

            if self.HeightCB4.val() == 0 and (out_type == 0):
                taxonomy[14] = '+HD99'
            if self.HeightCB4.val() == 1:
                taxonomy[14] = '+HD:' + self.noStoreysE41.val()


        if self.OccupancyCB1.val() == 0:
            if (out_type == 0):
                taxonomy[15] = 'OC99'

        elif self.OccupancyCB1.val() == 1:
            taxonomy[15] = 'RES'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+RES99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+RES1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+RES2'
            if self.OccupancyCB2.val() == 3:
                taxonomy[16] = '+RES2A'
            if self.OccupancyCB2.val() == 4:
                taxonomy[16] = '+RES2B'
            if self.OccupancyCB2.val() == 5:
                taxonomy[16] = '+RES2C'
            if self.OccupancyCB2.val() == 6:
                taxonomy[16] = '+RES2D'
            if self.OccupancyCB2.val() == 7:
                taxonomy[16] = '+RES2E'
            if self.OccupancyCB2.val() == 8:
                taxonomy[16] = '+RES2F'
            if self.OccupancyCB2.val() == 9:
                taxonomy[16] = '+RES3'
            if self.OccupancyCB2.val() == 10:
                taxonomy[16] = '+RES4'
            if self.OccupancyCB2.val() == 11:
                taxonomy[16] = '+RES5'
            if self.OccupancyCB2.val() == 12:
                taxonomy[16] = '+RES6'

        elif self.OccupancyCB1.val() == 2:
            taxonomy[15] = 'COM'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+COM99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+COM1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+COM2'
            if self.OccupancyCB2.val() == 3:
                taxonomy[16] = '+COM3'
            if self.OccupancyCB2.val() == 4:
                taxonomy[16] = '+COM4'
            if self.OccupancyCB2.val() == 5:
                taxonomy[16] = '+COM5'
            if self.OccupancyCB2.val() == 6:
                taxonomy[16] = '+COM6'
            if self.OccupancyCB2.val() == 7:
                taxonomy[16] = '+COM7'
            if self.OccupancyCB2.val() == 8:
                taxonomy[16] = '+COM8'
            if self.OccupancyCB2.val() == 9:
                taxonomy[16] = '+COM9'
            if self.OccupancyCB2.val() == 10:
                taxonomy[16] = '+COM10'
            if self.OccupancyCB2.val() == 11:
                taxonomy[16] = '+COM11'

        elif self.OccupancyCB1.val() == 3:
            taxonomy[15] = 'MIX'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+MIX99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+MIX1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+MIX2'
            if self.OccupancyCB2.val() == 3:
                taxonomy[16] = '+MIX3'
            if self.OccupancyCB2.val() == 4:
                taxonomy[16] = '+MIX4'
            if self.OccupancyCB2.val() == 5:
                taxonomy[16] = '+MIX5'
            if self.OccupancyCB2.val() == 6:
                taxonomy[16] = '+MIX6'

        elif self.OccupancyCB1.val() == 4:
            taxonomy[15] = 'IND'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+IND99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+IND1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+IND2'

        elif self.OccupancyCB1.val() == 5:
            taxonomy[15] = 'AGR'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+AGR99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+AGR1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+AGR2'
            if self.OccupancyCB2.val() == 3:
                taxonomy[16] = '+AGR3'

        elif self.OccupancyCB1.val() == 6:
            taxonomy[15] = 'ASS'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+ASS99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+ASS1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+ASS2'
            if self.OccupancyCB2.val() == 3:
                taxonomy[16] = '+ASS3'
            if self.OccupancyCB2.val() == 4:
                taxonomy[16] = '+ASS4'

        elif self.OccupancyCB1.val() == 7:
            taxonomy[15] = 'GOV'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+GOV99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+GOV1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+GOV2'

        elif self.OccupancyCB1.val() == 8:
            taxonomy[15] = 'EDU'
            if self.OccupancyCB2.val() == 0 and (out_type == 0):
                taxonomy[16] = '+EDU99'
            if self.OccupancyCB2.val() == 1:
                taxonomy[16] = '+EDU1'
            if self.OccupancyCB2.val() == 2:
                taxonomy[16] = '+EDU2'
            if self.OccupancyCB2.val() == 3:
                taxonomy[16] = '+EDU3'
            if self.OccupancyCB2.val() == 4:
                taxonomy[16] = '+EDU4'

        elif self.OccupancyCB1.val() == 9:
            taxonomy[15] = 'OCO'


        if self.PositionCB.val() == 0 and (out_type == 0):
            taxonomy[17] = 'BP99'
        elif self.PositionCB.val() == 1:
            taxonomy[17] = 'BPD'
        elif self.PositionCB.val() == 2:
            taxonomy[17] = 'BP1'
        elif self.PositionCB.val() == 3:
            taxonomy[17] = 'BP2'
        elif self.PositionCB.val() == 4:
            taxonomy[17] = 'BP3'
        elif self.PositionCB.val() == 5:
            taxonomy[17] = 'BPI'

        if self.PlanShapeCB.val() == 0 and (out_type == 0):
            taxonomy[18] = 'PLF99'
        elif self.PlanShapeCB.val() == 1:
            taxonomy[18] = 'PLFSQ'
        elif self.PlanShapeCB.val() == 2:
            taxonomy[18] = 'PLFSQO'
        elif self.PlanShapeCB.val() == 3:
            taxonomy[18] = 'PLFR'
        elif self.PlanShapeCB.val() == 4:
            taxonomy[18] = 'PLFRO'
        elif self.PlanShapeCB.val() == 5:
            taxonomy[18] = 'PLFL'
        elif self.PlanShapeCB.val() == 6:
            taxonomy[18] = 'PLFC'
        elif self.PlanShapeCB.val() == 7:
            taxonomy[18] = 'PLFCO'
        elif self.PlanShapeCB.val() == 8:
            taxonomy[18] = 'PLFD'
        elif self.PlanShapeCB.val() == 9:
            taxonomy[18] = 'PLFDO'
        elif self.PlanShapeCB.val() == 10:
            taxonomy[18] = 'PLFE'
        elif self.PlanShapeCB.val() == 11:
            taxonomy[18] = 'PLFH'
        elif self.PlanShapeCB.val() == 12:
            taxonomy[18] = 'PLFS'
        elif self.PlanShapeCB.val() == 13:
            taxonomy[18] = 'PLFT'
        elif self.PlanShapeCB.val() == 14:
            taxonomy[18] = 'PLFU'
        elif self.PlanShapeCB.val() == 15:
            taxonomy[18] = 'PLFX'
        elif self.PlanShapeCB.val() == 16:
            taxonomy[18] = 'PLFY'
        elif self.PlanShapeCB.val() == 17:
            taxonomy[18] = 'PLFP'
        elif self.PlanShapeCB.val() == 18:
            taxonomy[18] = 'PLFPO'
        elif self.PlanShapeCB.val() == 19:
            taxonomy[18] = 'PLFI'

        if self.RegularityCB1.val() == 0:
            if (out_type == 0):
                taxonomy[19] = 'IR99'

        else:
            if self.RegularityCB1.val() == 1:
                taxonomy[19] = 'IRRE'
            if self.RegularityCB1.val() == 2:
                taxonomy[19] = 'IRIR'
                if self.RegularityCB2.val() == 0 and (out_type == 0):
                    taxonomy[20] = '+IRPP:IRN'
                if self.RegularityCB2.val() == 1:
                    taxonomy[20] = '+IRPP:TOR'
                if self.RegularityCB2.val() == 2:
                    taxonomy[20] = '+IRPP:REC'
                if self.RegularityCB2.val() == 3:
                    taxonomy[20] = '+IRPP:IRHO'

                if self.RegularityCB3.val() == 0 and (out_type == 0):
                    taxonomy[21] = '+IRVP:IRN'
                if self.RegularityCB3.val() == 1:
                    taxonomy[21] = '+IRVP:SOS'
                if self.RegularityCB3.val() == 2:
                    taxonomy[21] = '+IRVP:CRW'
                if self.RegularityCB3.val() == 3:
                    taxonomy[21] = '+IRVP:SHC'
                if self.RegularityCB3.val() == 4:
                    taxonomy[21] = '+IRVP:POP'
                if self.RegularityCB3.val() == 5:
                    taxonomy[21] = '+IRVP:SET'
                if self.RegularityCB3.val() == 6:
                    taxonomy[21] = '+IRVP:CHV'
                if self.RegularityCB3.val() == 7:
                    taxonomy[21] = '+IRVP:IRVO'

                if self.RegularityCB2.val() > 0:
                    if self.RegularityCB4.val() == 0:
                        taxonomy[22] = '+IRPS:IRN'
                    if self.RegularityCB4.val() == 1:
                        taxonomy[22] = '+IRPS:TOR'
                    if self.RegularityCB4.val() == 2:
                        taxonomy[22] = '+IRPS:REC'
                    if self.RegularityCB4.val() == 3:
                        taxonomy[22] = '+IRPS:IRHO'

                if self.RegularityCB3.val() > 0:
                    if self.RegularityCB5.val() == 0:
                        taxonomy[23] = '+IRVS:IRN'
                    if self.RegularityCB5.val() == 1:
                        taxonomy[23] = '+IRVS:SOS'
                    if self.RegularityCB5.val() == 2:
                        taxonomy[23] = '+IRVS:CRW'
                    if self.RegularityCB5.val() == 3:
                        taxonomy[23] = '+IRVS:SHC'
                    if self.RegularityCB5.val() == 4:
                        taxonomy[23] = '+IRVS:POP'
                    if self.RegularityCB5.val() == 5:
                        taxonomy[23] = '+IRVS:SET'
                    if self.RegularityCB5.val() == 6:
                        taxonomy[23] = '+IRVS:CHV'
                    if self.RegularityCB5.val() == 7:
                        taxonomy[23] = '+IRVS:IRVO'




        if self.WallsCB.val() == 0 and (out_type == 0):
            taxonomy[24] = 'EW99'
        if self.WallsCB.val() == 1:
            taxonomy[24] = 'EWC'
        if self.WallsCB.val() == 2:
            taxonomy[24] = 'EWG'
        if self.WallsCB.val() == 3:
            taxonomy[24] = 'EWE'
        if self.WallsCB.val() == 4:
            taxonomy[24] = 'EWMA'
        if self.WallsCB.val() == 5:
            taxonomy[24] = 'EWME'
        if self.WallsCB.val() == 6:
            taxonomy[24] = 'EWV'
        if self.WallsCB.val() == 7:
            taxonomy[24] = 'EWW'
        if self.WallsCB.val() == 8:
            taxonomy[24] = 'EWSL'
        if self.WallsCB.val() == 9:
            taxonomy[24] = 'EWPL'
        if self.WallsCB.val() == 10:
            taxonomy[24] = 'EWCB'
        if self.WallsCB.val() == 11:
            taxonomy[24] = 'EWO'

        if self.RoofCB1.val() == 0 and (out_type == 0):
            taxonomy[25] = 'RSH99'
        if self.RoofCB1.val() == 1:
            taxonomy[25] = 'RSH1'
        if self.RoofCB1.val() == 2:
            taxonomy[25] = 'RSH2'
        if self.RoofCB1.val() == 3:
            taxonomy[25] = 'RSH3'
        if self.RoofCB1.val() == 4:
            taxonomy[25] = 'RSH4'
        if self.RoofCB1.val() == 5:
            taxonomy[25] = 'RSH5'
        if self.RoofCB1.val() == 6:
            taxonomy[25] = 'RSH6'
        if self.RoofCB1.val() == 7:
            taxonomy[25] = 'RSH7'
        if self.RoofCB1.val() == 8:
            taxonomy[25] = 'RSH8'
        if self.RoofCB1.val() == 9:
            taxonomy[25] = 'RSH9'
        if self.RoofCB1.val() == 10:
            taxonomy[25] = 'RSHO'

        if self.RoofCB2.val() == 0 and (out_type == 0):
            taxonomy[26] = 'RMT99'
        if self.RoofCB2.val() == 1:
            taxonomy[26] = 'RMN'
        if self.RoofCB2.val() == 2:
            taxonomy[26] = 'RMT1'
        if self.RoofCB2.val() == 3:
            taxonomy[26] = 'RMT2'
        if self.RoofCB2.val() == 4:
            taxonomy[26] = 'RMT3'
        if self.RoofCB2.val() == 5:
            taxonomy[26] = 'RMT4'
        if self.RoofCB2.val() == 6:
            taxonomy[26] = 'RMT5'
        if self.RoofCB2.val() == 7:
            taxonomy[26] = 'RMT6'
        if self.RoofCB2.val() == 8:
            taxonomy[26] = 'RMT7'
        if self.RoofCB2.val() == 9:
            taxonomy[26] = 'RMT8'
        if self.RoofCB2.val() == 10:
            taxonomy[26] = 'RMT9'
        if self.RoofCB2.val() == 11:
            taxonomy[26] = 'RMT10'
        if self.RoofCB2.val() == 12:
            taxonomy[26] = 'RMT11'
        if self.RoofCB2.val() == 13:
            taxonomy[26] = 'RMTO'

        if self.RoofCB3.val() == 0:
            if (out_type == 0):
                taxonomy[27] = 'R99'

        else:
            if self.RoofCB3.val() == 1:
                taxonomy[27] = 'RM'
                if self.RoofCB4.val() == 0 and (out_type == 0):
                    taxonomy[28] = 'RM99'
                if self.RoofCB4.val() == 1:
                    taxonomy[28] = 'RM1'
                if self.RoofCB4.val() == 2:
                    taxonomy[28] = 'RM2'
                if self.RoofCB4.val() == 3:
                    taxonomy[28] = 'RM3'

            elif self.RoofCB3.val() == 2:
                taxonomy[27] = 'RE'
                if self.RoofCB4.val() == 0 and (out_type == 0):
                    taxonomy[28] = 'RE99'
                if self.RoofCB4.val() == 1:
                    taxonomy[28] = 'RE1'

            elif self.RoofCB3.val() == 3:
                taxonomy[27] = 'RC'
                if self.RoofCB4.val() == 0 and (out_type == 0):
                    taxonomy[28] = 'RC99'
                if self.RoofCB4.val() == 1:
                    taxonomy[28] = 'RC1'
                if self.RoofCB4.val() == 2:
                    taxonomy[28] = 'RC2'
                if self.RoofCB4.val() == 3:
                    taxonomy[28] = 'RC3'
                if self.RoofCB4.val() == 4:
                    taxonomy[28] = 'RC4'

            elif self.RoofCB3.val() == 4:
                taxonomy[27] = 'RME'
                if self.RoofCB4.val() == 0 and (out_type == 0):
                    taxonomy[28] = 'RME99'
                if self.RoofCB4.val() == 1:
                    taxonomy[28] = 'RME1'
                if self.RoofCB4.val() == 2:
                    taxonomy[28] = 'RME2'
                if self.RoofCB4.val() == 3:
                    taxonomy[28] = 'RME3'

            elif self.RoofCB3.val() == 5:
                taxonomy[27] = 'RWO'
                if self.RoofCB4.val() == 0 and (out_type == 0):
                    taxonomy[28] = 'RWO99'
                if self.RoofCB4.val() == 1:
                    taxonomy[28] = 'RWO1'
                if self.RoofCB4.val() == 2:
                    taxonomy[28] = 'RWO2'
                if self.RoofCB4.val() == 3:
                    taxonomy[28] = 'RWO3'
                if self.RoofCB4.val() == 4:
                    taxonomy[28] = 'RWO4'
                if self.RoofCB4.val() == 5:
                    taxonomy[28] = 'RWO5'

            elif self.RoofCB3.val() == 6:
                taxonomy[27] = 'RFA'
                if self.RoofCB4.val() == 0:
                    taxonomy[28] = 'RFA1'
                if self.RoofCB4.val() == 1:
                    taxonomy[28] = 'RFAO'

            elif self.RoofCB3.val() == 7:
                taxonomy[27] = 'RO'



        if self.RoofCB5.val() == 0 and (out_type == 0):
            taxonomy[29] = 'RWC99'
        if self.RoofCB5.val() == 1:
            taxonomy[29] = 'RWCN'
        if self.RoofCB5.val() == 2:
            taxonomy[29] = 'RWCP'
        if self.RoofCB5.val() == 3:
            taxonomy[29] = 'RTD99'
        if self.RoofCB5.val() == 4:
            taxonomy[29] = 'RTDN'
        if self.RoofCB5.val() == 5:
            taxonomy[29] = 'RTDP'

        if self.FloorCB1.val() == 0:
            if (out_type == 0):
                taxonomy[30] = 'F99'

        elif self.FloorCB1.val() == 1:
            taxonomy[30] = 'FN'

        else:
            if self.FloorCB1.val() == 2:
                taxonomy[30] = 'FM'
                if self.FloorCB2.val() == 0 and (out_type == 0):
                    taxonomy[31] = '+FM99'
                if self.FloorCB2.val() == 1:
                    taxonomy[31] = '+FM1'
                if self.FloorCB2.val() == 2:
                    taxonomy[31] = '+FM2'
                if self.FloorCB2.val() == 3:
                    taxonomy[31] = '+FM3'

            elif self.FloorCB1.val() == 3:
                taxonomy[30] = 'FE'
                if self.FloorCB2.val() == 0 and (out_type == 0):
                    taxonomy[31] = '+FE99'

            elif self.FloorCB1.val() == 4:
                taxonomy[30] = 'FC'
                if self.FloorCB2.val() == 0 and (out_type == 0):
                    taxonomy[31] = '+FC99'
                if self.FloorCB2.val() == 1:
                    taxonomy[31] = '+FC1'
                if self.FloorCB2.val() == 2:
                    taxonomy[31] = '+FC2'
                if self.FloorCB2.val() == 3:
                    taxonomy[31] = '+FC3'
                if self.FloorCB2.val() == 4:
                    taxonomy[31] = '+FC4'

            elif self.FloorCB1.val() == 5:
                taxonomy[30] = 'FME'
                if self.FloorCB2.val() == 0 and (out_type == 0):
                    taxonomy[31] = '+FME99'
                if self.FloorCB2.val() == 1:
                    taxonomy[31] = '+FME1'
                if self.FloorCB2.val() == 2:
                    taxonomy[31] = '+FME2'
                if self.FloorCB2.val() == 3:
                    taxonomy[31] = '+FME3'

            elif self.FloorCB1.val() == 6:
                taxonomy[30] = 'FW'
                if self.FloorCB2.val() == 0 and (out_type == 0):
                    taxonomy[31] = '+FW99'
                if self.FloorCB2.val() == 1:
                    taxonomy[31] = '+FW1'
                if self.FloorCB2.val() == 2:
                    taxonomy[31] = '+FW2'
                if self.FloorCB2.val() == 3:
                    taxonomy[31] = '+FW3'
                if self.FloorCB2.val() == 4:
                    taxonomy[31] = '+FW4'

            elif self.FloorCB1.val() == 7:
                taxonomy[30] = 'FO'


        if self.FloorCB3.val() == 0 and (out_type == 0):
            taxonomy[32] = 'FWC99'
        if self.FloorCB3.val() == 1:
            taxonomy[32] = 'FWCN'
        if self.FloorCB3.val() == 2:
            taxonomy[32] = 'FWCP'

        if self.FoundationsCB.val() == 0 and (out_type == 0):
            taxonomy[33] = 'FOS99'
        if self.FoundationsCB.val() == 1:
            taxonomy[33] = 'FOSSL'
        if self.FoundationsCB.val() == 2:
            taxonomy[33] = 'FOSN'
        if self.FoundationsCB.val() == 3:
            taxonomy[33] = 'FOSDL'
        if self.FoundationsCB.val() == 4:
            taxonomy[33] = 'FOSDN'
        if self.FoundationsCB.val() == 5:
            taxonomy[33] = 'FOSO'


        # // TAIL
        direction1 = 'DX'
        direction2 = 'DY'

        if self.Direction1RB1.checked()  and (out_type == 0):
            direction1 = direction1 + '+D99'
            direction2 = direction2 + '+D99'

        elif self.Direction1RB2.checked():
            direction1 = direction1 + '+PF'
            direction2 = direction2 + '+OF'


        # /*
        #    0) direction X

        #       0 - Material type
        #       1 - Material technology
        #       34- Material tech adds
        #       2 - Material properties

        #       3 - Type of lateral system
        #       4 - System ductility

        #       direction Y

        #       5 - Material type
        #       6 - Material technology
        #       35- Material tech adds
        #       7 - Material properties

        #    5) 8 - Type of lateral system
        #       9 - System ductility

        #       11 - Height above the ground
        #       12 - Height below the ground
        #       13 - Height of grade
        #       14 - Slope of the ground

        #       10 - Date of construction

        #       15 - Occupancy type
        #       16 - Occupancy description

        #       17 - Position

        #   10) 18 - Plan

        #       19 - Type of irregularity
        #       20 - Plan irregularity(primary)
        #       22 - Vertical irregularity(primary)
        #       21 - Plan irregularity(secondary)
        #       23 - Vertical irregularity(secondary)

        #       24- Material of exterior walls

        #       25 - Roof shape
        #       26 - Roof covering
        #       27 - Roof system material
        #       28 - Roof system type
        #       29 - Roof connections

        #       30 - Floor system material
        #       31 - Floor system type
        #       32 - Floor connections

        #   15) 33 - Foundation
        #       */

        # /* roof special case */
        roof_atom_empty = True
        for i in range(25, 30):
            if taxonomy[i] != '':
                if roof_atom_empty:
                    roof_atom_empty = False
                else:
                    taxonomy[i] = "+" + str(taxonomy[i])


        # /* floor special case */
        floor_atom_empty = True
        floor_atom_primaries = [30, 32]
        for i in floor_atom_primaries:
            if taxonomy[i] != '':
                if floor_atom_empty:
                    floor_atom_empty = False
                else:
                    taxonomy[i] = "+" + str(taxonomy[i])


        ResTax = (str(direction1) + '/' + str(taxonomy[0]) + str(taxonomy[1]) + str(taxonomy[34]) + str(taxonomy[2]) +
                  '/' + str(taxonomy[3]) + str(taxonomy[4]) +
                  '/' + direction2 + '/' + str(taxonomy[5]) + str(taxonomy[6]) + str(taxonomy[35]) + str(taxonomy[7]) +
                  '/' + str(taxonomy[8]) + str(taxonomy[9]) +
                  '/' + str(taxonomy[11]) + str(taxonomy[12]) + str(taxonomy[13]) + str(taxonomy[14]) + '/' + str(taxonomy[10]) +
                  '/' + str(taxonomy[15]) + str(taxonomy[16]) + '/' + str(taxonomy[17]) + '/' + str(taxonomy[18]) +
                  '/' + str(taxonomy[19]) + str(taxonomy[20]) + str(taxonomy[22]) + str(taxonomy[21]) + str(taxonomy[23]) +
                  '/' + str(taxonomy[24]) + '/' + str(taxonomy[25]) + str(taxonomy[26]) + str(taxonomy[27]) + str(taxonomy[28]) + str(taxonomy[29]) +
                  '/' + str(taxonomy[30]) + str(taxonomy[31]) + str(taxonomy[32]) + '/' + str(taxonomy[33]))

        if out_type == 2:
            is_first = True
            ResAtoms = ResTax.split('/')
            if ResAtoms[1] == ResAtoms[4] and ResAtoms[2] == ResAtoms[5]:
                # // same params case
                ResAtoms[3] = ResAtoms[4] = ResAtoms[5] = ""
                if self.Direction1RB1.checked():
                    ResAtoms[0] = ""

                else:
                    ResAtoms[0] = "PF"


            else:
                if self.Direction1RB1.checked():
                    ResAtoms[0] = "DX"
                    ResAtoms[3] = "DY"

                else:
                    ResAtoms[0] = "DX+PF"
                    ResAtoms[3] = "DY+PO"


            ResTax = ""
            for id, v in enumerate(ResAtoms):
                if ResAtoms[id] == "":
                    continue

                if not is_first:
                    ResTax += "/"
                else:
                    is_first = False
                ResTax += ResAtoms[id]


        return (ResTax)



    def populate(self, s, ret_s):
        # var i
        # var sar, subar, el

        self.noStoreysE11.val('')
        self.noStoreysE12.val('')
        self.noStoreysE21.val('')
        self.noStoreysE22.val('')
        self.noStoreysE31.val('')
        self.noStoreysE32.val('')
        self.noStoreysE41.val('')
        self.DateE1.val('')
        self.DateE2.val('')
        self.resultE.val('')
        self.resultE_virt.val('')

        sar = s.split('/')
        self.DirectionCB.checked(False)

        #
        #  Direction
        #
        dirx = sar[0]
        diry = sar[3]
        if dirx == "DX+D99" and diry == "DY+D99":
            self.Direction1RB1.checked(True)
            self.taxt_Direction1RB1Click(None)

        elif dirx == "DX+PF" and diry == "DY+OF":
            self.Direction1RB2.checked(True)
            self.taxt_Direction1RB2Click(None)

        else:
            ret_s.s = "Not valid 'Direction specifications' found."
            return False


        #
        #  Material
        #
        mat_ddown = ['MaterialCB11', 'MaterialCB12']
        mat_selec = ['taxt_MaterialCB11Select', 'taxt_MaterialCB12Select']
        mat_tecn_ddown = ['MaterialCB21', 'MaterialCB22']
        mat_tecn_selec = ['taxt_MaterialCB21Select', 'taxt_MaterialCB22Select']
        mat_tead_ddown = ['MaterialCB41', 'MaterialCB42']
        mat_tead_selec = ['taxt_MaterialCB41Select', 'taxt_MaterialCB42Select']
        mat_prop_ddown = ['MaterialCB31', 'MaterialCB32']
        mat_prop_selec = ['taxt_MaterialCB31Select', 'taxt_MaterialCB32Select']
        llrs_ddown = ['SystemCB11', 'SystemCB12']
        llrs_selec = ['taxt_SystemCB11Select', 'taxt_SystemCB12Select']
        llrs_duct_ddown = ['SystemCB21', 'SystemCB22']
        llrs_duct_selec = ['taxt_SystemCB21Select', 'taxt_SystemCB22Select']

        # var llrs_atom

        for direct in range(0, 2):
            mat = sar[1+(direct * 3)].split('+')
            llrs = sar[2+(direct * 3)].split('+')

            if len(mat) < 1:
                ret_s.s = "Not defined material for 'Direction " + ("X" if direct == 0 else "Y") + "'"
                return (False)

            if len(llrs) < 1:
                ret_s.s = "Not defined LLRS for 'Direction " + ("X" if direct == 0 else "Y") + "'"
                return (False)


            for i in range(0, len(material)):
                if mat[0] == material[i]['id']:
                    mat_id = mat[0]
                    getattr(self, mat_ddown[direct]).val(i)
                    getattr(self, mat_selec[direct])()
                    break
            else:
                ret_s.s = "Not identified '" + mat[0] + "' material for 'Direction " + ("X" if direct == 0 else "Y") + "'"
                return (False)

            for sub_i in range(1 , len(mat)):
                mat_atom = mat[sub_i]

                # Material technology
                completed = False
                for i in range( 0, len(mat_tech[mat_id])):
                    if mat_atom == mat_tech[mat_id][i]['id']:
                        getattr(self, mat_tecn_ddown[direct]).val(i)
                        getattr(self, mat_tecn_selec[direct])()
                        break
                else:
                    completed = True

                if not completed:
                    continue

                # Material technology added
                completed = False
                for i in range(0, len(mat_tead[mat_id])):
                    if mat_atom == mat_tead[mat_id][i]['id']:
                        getattr(self, mat_tead_ddown[direct]).val(i)
                        getattr(self, mat_tead_selec[direct])()
                        break
                else:
                    completed = True

                if not completed:
                    continue

                # Material properties
                completed = False
                for i in range(0, len(mat_prop[mat_id])):
                    if mat_atom == mat_prop[mat_id][i]['id']:
                        getattr(self, mat_prop_ddown[direct]).val(i)
                        getattr(self, mat_prop_selec[direct])()
                        break
                else:
                    completed = True

                if not completed:
                    continue

                ret_s.s = "Not identified '" + mat_atom + "' as specification of '" + mat_id + "' material for 'Direction " + ("X" if direct == 0 else "Y") + "'."
                return (False)


            #
            #  Lateral load resisting system: type
            #
            for i in range(0, len(llrs_type[mat_id])):
                llrs_id = llrs_type[mat_id][i]['id']

                if llrs[0] == llrs_id:
                    getattr(self, llrs_ddown[direct]).val(i)
                    getattr(self, llrs_selec[direct])()
                    break
            else:
                ret_s.s = "Not identified '" + llrs[0] + "' as LLRS of '" + mat_id + "' material for 'Direction " + ("X" if direct == 0 else "Y") + "'."
                return (False)

            for sub_i in range(1, len(llrs)):
                llrs_atom = llrs[sub_i]

                # Ductility
                completed = False
                for i in range(0, len(llrs_duct[llrs_id])):
                    if llrs_atom == llrs_duct[llrs_id][i]['id']:
                        getattr(self, llrs_duct_ddown[direct]).val(i)
                        getattr(self, llrs_duct_selec[direct])()
                        break
                else:
                    completed = True

                if not completed:
                    continue

                ret_s.s = "Not identified '" + llrs_atom + "' as specification of '" + llrs[0] + "' LLRS of '" + mat_id + "' material for 'Direction " + ("X" if direct == 0 else"Y") + "'."
                return (False)


        dir_items = [ 'MaterialCB1', 'MaterialCB2', 'MaterialCB3', 'MaterialCB4',
                      'SystemCB1', 'SystemCB2' ]

        for i in range(0, len(dir_items)):
            if getattr(self, dir_items[i]+'1').val() != getattr(self, dir_items[i]+'2').val():
                break
        else:
            self.DirectionCB.checked(True)

        #
        #  Height
        #
        # var h, h_items, h_label, h_id, h_vals, h_grp
        h_map = [ 'H99' , 'HBET' , 'HEX' , 'HAPP' ,
                  'HB99', 'HBBET', 'HBEX', 'HBAPP',
                  'HF99', 'HFBET', 'HFEX', 'HFAPP',
                  'HD99',  None  , 'HD' ]

        # assigned but never used
        # h_pref = ['H', 'HB', 'HF', 'HD']
        h_cbid =   ['1',  '2',  '3',  '4']
        h_title = [ 'Number of storey above ground',
                    'Number of storey below ground',
                    'Height of ground floor level above grade',
                    'Slope of the ground' ]

        hsfx_99 = 0; hsfx_bet = 1
        # assigned but never used
        # ; hsfx_ex = 2; hsfx_app = 3

        h_cbfun = [self.taxt_HeightCB1Select, self.taxt_HeightCB2Select, self.taxt_HeightCB3Select, self.taxt_HeightCB4Select]
        h_typck = [is_not_negative_int, is_not_negative_int, is_not_negative_float, is_in_rect_angle_float]
        h_typck_s = ["positive integer", "positive integer", "positive real", "positive real between 0 and 90"]
        h_convf = [int, int, float, int]
        h = sar[6].split('+')

        for sub_i in range(0, len(h)):
            h_items = h[sub_i].split(':')
            h_label = h_items[0]

            try:
                h_id = h_map.index(h_label)
            except ValueError:
                h_id = -1

            if h_id == -1:
                ret_s.s = "Height not defined properly."
                return (False)

            h_grp = int(math.floor(h_id / 4))
            h_type = h_id % 4

            if h_type == hsfx_99:
                if len(h_items) != 1:
                    ret_s.s = "Height: '" + h_label + "' type requires no values, " + is_or_are_given(len(h_items))
                    return (False)


            elif h_type == hsfx_bet:
                if len(h_items) < 2:
                    ret_s.s = "Height: '" + h_label + "' type requires exactly 2 values, no one is given."
                    return (False)

                else:
                    h_vals = h_items[1].split(',')

                    if len(h_vals) != 2:
                        ret_s.s = "Height: '" + h_label + "' type requires exactly 2 values, " + is_or_are_given(len(h_vals))
                        return (False)
            else:
                if len(h_items) < 2:
                    ret_s.s = "Height: '" + h_label + "' type requires exactly 1 value, no one is given."
                    return (False)

                h_vals = h_items[1].split(',')
                if len(h_vals) != 1:
                    ret_s.s = "Height: '" + h_label + "' type requires exactly 1 value, " + is_or_are_given(len(h_vals))
                    return (False)

            if h_type != hsfx_99:
                # is_not_negative_int or is_not_negative_float
                if not h_typck[h_grp](h_vals[0]):
                    if h_type == hsfx_bet:
                        ret_s.s = h_title[h_grp] + ": lower limit not " + h_typck_s[h_grp] + ". "
                    else:
                        ret_s.s = h_title[h_grp] + ": not " + h_typck_s[h_grp] + ". "

                    return (False)

                if h_type == hsfx_bet:
                    if not h_typck[h_grp](h_vals[1]):
                        ret_s.s = h_title[h_grp] + ": higher limit not " + h_typck_s[h_grp] + ". "
                        return (False)

                    elif h_convf[h_grp](h_vals[0]) == h_convf[h_grp](h_vals[1]):
                        ret_s.s = h_title[h_grp] + ": invalid range. "
                        return (False)


                    # swap items if wrong order
                    if int(h_vals[0]) > int(h_vals[1]):
                        swap = h_vals[1]
                        h_vals[1] = h_vals[0]
                        h_vals[0] = swap
                    getattr(self, 'noStoreysE' + h_cbid[h_grp] + '2').val(h_vals[1])


                # set value (in the case of 'HD' the real index must be (h_type - 1))
                getattr(self, 'HeightCB' + h_cbid[h_grp]).val(h_type - 1 if h_map[h_id] == 'HD' else h_type)
                getattr(self, 'noStoreysE' + h_cbid[h_grp] + '1').val(h_vals[0])

                h_cbfun[h_grp](None)

            else:
                # missing case for H99 case
                the_value = h_type - 1 if h_map[h_id] == 'HD' else h_type
                getattr(self, 'HeightCB' + h_cbid[h_grp]).val(the_value)
                h_cbfun[h_grp](None)



        #
        #  Date
        #
        # var date, date_index = -1, date_items, date_label, date_id, date_vals

        date = sar[7].split('+')
        date_items = date[0].split(':')
        date_label = date_items[0]

        if len(date) != 1:
            ret_s.s = "Date not defined properly."
            return (False)


        for i in range(0, len(date_type)):
            if date_label == date_type[i]['id']:
                date_index = i
                date_id = date_label
                break
        else:
            ret_s.s = "Not identified '" + date_label + "' as specification of date."
            return (False)

        if date_id != "Y99":
            if len(date_items) < 2:
                ret_s.s = "Date: no values defined."
                return (False)


            date_vals = date_items[1].split(',')
            if date_id == 'YBET':
                if len(date_vals) != 2:
                    ret_s.s = "Date: '" + date_id + "' type requires exactly 2 values, " + is_or_are_given(len(date_vals))
                    return (False)


            elif date_id == 'YEX' or date_id == 'YPRE' or date_id == 'YAPP':
                if len(date_vals) != 1:
                    ret_s.s = "Date: '" + date_id + "' type requires exactly 1 value, " + is_or_are_given(len(date_vals))
                    return (False)



            if not is_not_negative_int(date_vals[0]) or len(date_vals[0]) > 4:
                if date_id == 'YBET':
                    ret_s.s = "Date of construction or retrofit: lower limit is not a valid date."

                else:
                    ret_s.s = "Date of construction or retrofit: it is not a valid date."

                return (False)


            if date_id == 'YBET':
                if not is_not_negative_int(date_vals[1]) or len(date_vals[1]) > 4:
                    ret_s.s = "Date of construction or retrofit: higher limit is not a valid date."
                    return (False)


                if int(date_vals[0]) == int(date_vals[1]):
                    ret_s.s = "Date of construction or retrofit: invalid range."
                    return (False)


                # swap items if wrong order
                if int(date_vals[0]) > int(date_vals[1]):
                    swap = date_vals[1]
                    date_vals[1] = date_vals[0]
                    date_vals[0] = swap

                self.DateE2.val(date_vals[1])

            self.DateCB1.val(date_index)
            self.taxt_DateCB1Select(None)
            self.DateE1.val(date_vals[0])

            self.taxt_ValidateDate()

        else:
            self.DateCB1.val(0)
            self.taxt_DateCB1Select(None)


        #
        #  Occupancy
        #
        # var occu, occu_items, occu_label, occu_id, occu_vals, occu_atom
        occu = sar[8].split('+')
        occu_label = occu[0]

        if occu_label == 'OC99':
            if len(occu) != 1:
                ret_s.s = "Occupancy not defined properly (" + occu_label + ")."
                return (False)



        for i in range(0, len(occu_type)):
            if occu_label == occu_type[i]['id']:
                occu_id = occu_label
                self.OccupancyCB1.val(i)
                self.taxt_OccupancyCB1Select(None)
                break
        else:
            ret_s.s = "Not identified '" + occu_label + "' as specification of occupancy."
            return (False)

        if occu_label != 'OC99':
            if len(occu) > 1:
                # Occupancy specification
                occu_atom = occu[1]
            elif len(occu_spec[occu_id]) > 0:
                occu_atom = occu_spec[occu_id][0]['id']
            else:
                occu_atom = 'is_disabled'

            if occu_atom == 'is_disabled':
                self.OccupancyCB2.disabled(True)
            else:
                self.OccupancyCB2.disabled(False)
                for i in range(0, len(occu_spec[occu_id])):
                    if occu_atom == occu_spec[occu_id][i]['id']:
                        self.OccupancyCB2.val(i)
                        self.taxt_OccupancyCB2Select(None)
                        break
                else:
                    ret_s.s = ("Not identified '" + occu_atom +
                               "' as specification of '" + occu_id +
                               "' occupancy.")
                    return (False)

        #
        #  Build position
        #
        # var bupo, bupo_items, bupo_label, bupo_id, bupo_vals, bupo_atom
        bupo = sar[9].split('+')
        bupo_label = bupo[0]

        if len(bupo) != 1:
            ret_s.s = "Building position within a block not defined properly."
            return (False)


        for i in range(0, len(bupo_type)):
            if bupo_label == bupo_type[i]['id']:
                # 'bupo_id' assigned but never used
                # bupo_id = bupo_label
                self.PositionCB.val(i)
                self.taxt_PositionCBSelect(None)
                break
        else:
            ret_s.s = "Not identified '" + bupo_label + "' as specification of building position within a block."
            return (False)


        #
        #  Plan shape
        #
        # var plsh, plsh_items, plsh_label, plsh_id, plsh_vals, plsh_atom
        plsh = sar[10].split('+')
        plsh_label = plsh[0]

        if len(plsh) != 1:
            ret_s.s = "Shape of the building plan not defined properly."
            return (False)


        for i in range(0, len(plsh_type)):
            if plsh_label == plsh_type[i]['id']:
                # assigned but never used
                # plsh_id = plsh_label
                self.PlanShapeCB.val(i)
                self.taxt_PlanShapeCBSelect(None)
                break
        else:
            ret_s.s = "Not identified '" + plsh_label + "' as specification of shape of the building plan."
            return (False)


        #
        # Structural irregularity
        #
        # var stir, stir_items, stir_label, stir_id, stir_vals, stir_atom
        plir_id = ""; plse_id = ""; veir_id = ""; vese_id = ""
        ir_values = [ -1, -1, -1, -1, -1 ]

        stir = sar[11].split('+')
        stir_label = stir[0]

        for i in range(0, len(stir_type)):
            if stir_label == stir_type[i]['id']:
                stir_id = stir_label
                ir_values[0] = i
                break
        else:
            ret_s.s = "Not identified '" + stir_label + "' as specification of shape of the building plan."
            return (False)

        if (stir_id != "IRIR" and
            len(stir) > 1):
            ret_s.s = "Structural irregularity not defined properly."
            return (False)


        for sub_i in range(1, len(stir)):
            stir_atom = stir[sub_i]
            s_items = stir_atom.split(':')
            if len(s_items) != 2:
                ret_s.s = "'" + stir[sub_i] + "' not define properly as specification of '" + stir_id + "' type of irregularity."
                return (False)

            s_label = s_items[0]

            # Plan structural irregularity - primary
            if s_label == "IRPP":
                completed = False
                for i in range(0, len(plan_irre)):
                    if stir_atom == plan_irre[i]['id']:
                        plir_id = stir_atom
                        ir_values[1] = i
                        break
                else:
                    completed = True

                if not completed:
                    continue


            elif s_label == "IRPS":
                completed = False
                for i in range(0, len(plan_seco)):
                    if stir_atom == plan_seco[i]['id']:
                        plse_id = stir_atom
                        ir_values[3] = i
                        break
                else:
                    completed = True

                if not completed:
                    continue

            elif s_label == "IRVP":
                completed = False
                for i in range(0, len(vert_irre)):
                    if stir_atom == vert_irre[i]['id']:
                        veir_id = stir_atom
                        ir_values[2] = i
                        break
                else:
                    completed = True

                if not completed:
                    continue


            elif s_label == "IRVS":
                completed = False
                for i in range(0, len(vert_seco)):
                    if stir_atom == vert_seco[i]['id']:
                        vese_id = stir_atom
                        ir_values[4] = i
                        break
                else:
                    completed = True

                if not completed:
                    continue

            ret_s.s = "Not identified '" + stir_atom + "' as specification of structural irregularity."
            return (False)

        if plir_id == "IRPP:IRN" and plse_id != "":
            ret_s.s = "'" + plir_id + "' and '" + plse_id + "' are not a valid specification of structural irregularity."
            return (False)

        if veir_id == "IRVP:IRN" and vese_id != "":
            ret_s.s = "'" + veir_id + "' and '" + vese_id + "' are not a valid specification of structural irregularity."
            return (False)


        # all data are retrieved before the population phase to avoid unrequired reset of values permformed
        # by hierarchical ancestors
        if ir_values[0] > -1:
            self.RegularityCB1.val(ir_values[0])
            self.taxt_RegularityCB1Select(None)

        if ir_values[1] > -1:
            self.RegularityCB2.val(ir_values[1])
            self.taxt_RegularityCB2Select(None)

        if ir_values[2] > -1:
            self.RegularityCB3.val(ir_values[2])
            self.taxt_RegularityCB3Select(None)

        if ir_values[3] > -1:
            self.RegularityCB4.val(ir_values[3])
            self.taxt_RegularityCB4Select(None)

        if ir_values[4] > -1:
            self.RegularityCB5.val(ir_values[4])
            self.taxt_RegularityCB5Select(None)


        #
        #  Exterior wall
        #
        # var wall, wall_items, wall_label, wall_id, wall_vals, wall_atom
        wall = sar[12].split('+')
        wall_label = wall[0]
        if len(wall) != 1:
            ret_s.s = "Exterior walls not defined properly."
            return (False)


        for i in range(0, len(wall_type)):
            if wall_label == wall_type[i]['id']:
                # 'wall_id' assigned but not used
                # wall_id = wall_label
                self.WallsCB.val(i)
                self.taxt_WallsCBSelect(None)
                break
        else:
            ret_s.s = "Not identified '" + wall_label + "' as specification of exterior walls."
            return (False)


        #
        #  Roof
        #
        # roof shape
        # var rosh, rosh_items, rosh_label, rosh_id, rosh_vals, rosh_atom
        roof_system_set = False
        # var roof_system_val

        rosh = sar[13].split('+')
        # rosh_label assigned but never used
        # rosh_label = rosh[0]

        for sub_i in range(0, len(rosh)):
            rosh_atom = rosh[sub_i]

            # roof shape
            completed = False
            for i in range(0, len(roof_shap)):
                if rosh_atom == roof_shap[i]['id']:
                    self.RoofCB1.val(i)
                    self.taxt_RoofCB1Select(None)
                    break
            else:
                completed = True

            if not completed:
                continue

            # roof covering
            completed = False
            for i in range(0, len(roof_cove)):
                if rosh_atom == roof_cove[i]['id']:
                    self.RoofCB2.val(i)
                    self.taxt_RoofCB2Select(None)
                    break
            else:
                completed = True

            if not completed:
                continue

            # roof system material
            completed = False
            for i in range(0, len(roof_mate)):
                if rosh_atom == roof_mate[i]['id']:
                    roof_system_set = True
                    roof_system_val = rosh_atom

                    self.RoofCB3.val(i)
                    self.taxt_RoofCB3Select(None)
                    break
            else:
                completed = True

            if not completed:
                continue

            # roof connections
            completed = False
            for i in range(0, len(roof_conn)):
                if rosh_atom == roof_conn[i]['id']:
                    self.RoofCB5.val(i)
                    self.taxt_RoofCB5Select(None)
                    break
            else:
                completed = True

            if not completed:
                continue

            if roof_system_set:
                # roof connections
                completed = False
                for i in range(0, len(roof_sys[roof_system_val])):
                    if rosh_atom == roof_sys[roof_system_val][i]['id']:
                        self.RoofCB4.val(i)
                        self.taxt_RoofCB4Select(None)
                        break
                else:
                    completed = True

                if not completed:
                    continue

            ret_s.s = "Not identified '" + rosh_atom + "' as specification of roof."
            return (False)


        #
        #  Floor
        #
        # var flma, flma_items, flma_label, flma_vals, flma_atom
        flma_id = -1

        flma = sar[14].split('+')
        # 'flma_label' assigned but never used
        # flma_label = flma[0]

        for sub_i in range(0, len(flma)):
            flma_atom = flma[sub_i]

            # floor system material
            completed = False
            for i in range(0, len(floo_syma)):

                if flma_atom == floo_syma[i]['id']:
                    flma_id = floo_syma[i]['id']
                    self.FloorCB1.val(i)
                    self.taxt_FloorCB1Select(None)
                    break
            else:
                completed = True

            if not completed:
                continue

            # floor system type
            completed = False
            for i in range(0, len(floo_syty)):
                if flma_atom == floo_syty[i]['id']:
                    self.FloorCB3.val(i)
                    self.taxt_FloorCB3Select(None)
                    break
            else:
                completed = True

            if not completed:
                continue

            if flma_id != -1:
                # floor connections
                completed = False
                for i in range(0, len(floo_conn[flma_id])):
                    if flma_atom == floo_conn[flma_id][i]['id']:
                        self.FloorCB2.val(i)
                        self.taxt_FloorCB2Select(None)
                        break

                else:
                    completed = True

                if not completed:
                    continue


            ret_s.s = "Not identified '" + flma_atom + "' as specification of floor."
            return (False)


        #
        #  Foundation
        #
        # var foun, foun_items, foun_label, foun_id, foun_vals, foun_atom
        foun = sar[15].split('+')
        foun_label = foun[0]

        if len(foun) != 1:
            ret_s.s = "Foundations not defined properly."
            return (False)

        for i in range(0, len(foun_type)):
            if foun_label == foun_type[i]['id']:
                # 'foun_id' assigned but never used
                # foun_id = foun_label
                self.FoundationsCB.val(i)
                self.taxt_FoundationsCBSelect(None)
                break
        else:
            ret_s.s = "Not identified '" + foun_label + "' as specification of foundation."
            return (False)

        return (True)

    def resultE_mgmt(self, taxonomy):

        # color = None
        # col_orange = '#ffdfbf'
        # col_red = '#ffbfbf'
        # col_green = '#bfffbf'
        # col_transparent = ''
        error = ""
        # $(item).css('background-color', col_orange)

        #if event.type == 'input':
        #    $(item).off('keyup', resultE_mgmt)

        # ev_type = (event.type == 'blur' ? "OUT" : "IN")

        #if ev_type == 'IN' and virt_sfx == '':
        self._virt_sfx = '_virt'

        try:
            for i in range(0, 1):
                ret = taxonomy_short2full(taxonomy)

                if ret:
                    if ret.s:
                        error = ret.s
                        taxonomy = ''
                        break

                    else:
                        taxonomy = ret.result

                else:
                    taxonomy = ''
                    break


                ret_s = Ret(s="")
                # NOTE: all console.log calls will be removed
                # after a short quarantine period
                # console.log("PRE POP: " + taxonomy)
                self.taxt_Initiate(False)

                if self.populate(taxonomy, ret_s) is False:
                    error = ret_s.s
                    break

                # color = col_green

            self._virt_sfx = ''
            if error != "":
                return (None, error)
            else:
                self.resultE = self.resultE_virt
                return (str(self.resultE), None)
        except Exception as ex:
            self._virt_sfx = ''
            return (None, "EXCEPTION: " + str(ex))

    def process(self, taxt_in, type_out):
        """
convert an input taxonomy to a normalized form if correct else an error is returned.
    taxt_in:   taxonomy input string
    type_out:  type of taxonomy output
               0, "full", 1: "without unknown", 2: "short"
RETURN:
(taxonomy_out, error_str)
    taxonomy_out: a taxonomy if success else None
    error_str: None if success else a string with the error description
"""
        self.OutTypeCB.val(type_out)
        return self.resultE_mgmt(taxt_in)


def taxonomy_process(taxt_in, type_out):
    """
convert an input taxonomy to a normalized form if correct else an error is returned.
    taxt_in:   taxonomy input string
    type_out:  type of taxonomy output
               0, "full", 1: "without unknown", 2: "short"
RETURN:
(taxonomy_out, error_str)
    taxonomy_out: a taxonomy if success else None
    error_str: None if success else a string with the error description
"""
    taxonomy = Taxonomy('taxonomy', True)
    return taxonomy.process(taxt_in, type_out)


if __name__ == '__main__':
    taxonomy = Taxonomy('taxonomy', True)
    if len(sys.argv) > 2:
        if sys.argv[1] == '-f' or sys.argv[1] == '--file':
            f = open(sys.argv[2])
        else:
            sys.exit(1)
    elif len(sys.argv) > 1:
        f = io.StringIO((sys.argv[1] + '\n').decode(encoding='UTF-8'))
    else:
        f = open('test/data/distinct-gem-taxonomy_mod.csv')

    for line in f:
        line = line[0:-1]
        # all this normalization stuff is to try to find a simple modified version of GED4GEM original taxonomies
        # that fit with a modified version of "hidden unknown" taxonomy output
        line_norm = line[:]
        for d in ['MAT99', 'CT99', 'S99', 'ME99', 'SC99', 'MUN99', 'MR99', 'MO99', 'ET99', 'W99', 'L99', 'DU99',
                  'MAT99', 'CT99', 'S99', 'ME99', 'SC99', 'MUN99', 'MR99', 'MO99', 'ET99', 'W99', 'L99', 'DU99',
                  'Y99', 'H99', 'HB99', 'HF99', 'HD99', 'OC99', 'RES99', 'COM99', 'MIX99', 'IND99', 'AGR99',
                  'ASS99', 'GOV99', 'EDU99', 'BP99', 'PLF99', 'IR99', 'IRPP:IRN', 'IRVP:IRN', 'EW99', 'RSH99',
                  'RMT99', 'R99', 'RM99', 'RE99', 'RC99', 'RME99', 'RWO99', 'RWC99', 'F99', 'FM99', 'FE99',
                  'FC99', 'FME99', 'FW99', 'FWC99', 'FOS99', 'D99']:
            line_norm = re.sub('\\b%s\\b' % d, '', line_norm)
        line_norm = re.sub('\+*/\+*', '/', line_norm)
        line_norm = re.sub('[/\+]+$', '', line_norm)
        line_norm = re.sub('/+', '/', line_norm)
        print( "==== %s ==== (%s) =========" % (line, line_norm))

        for i in range(0, 10):
            if line[-1] == '/':
                line = line[0:-1]
            else:
                break

        ret1 = taxonomy.process(line, 0)
        if ret1[1]:
            print("ERROR1: [%s] [%s]\n" % (line, ret1[1]))
            continue
        ret2 = taxonomy.process(ret1[0], 1)
        if ret2[1]:
            print("ERROR2: [%s] [%s]\n" % (line, ret2[1]))
            continue
        ret2_norm = re.sub('/+', '/', ret2[0])
        ret2_norm = re.sub('/+$', '', ret2_norm)

        ret3 = taxonomy.process(ret2[0], 2)
        if ret3[1]:
            print("ERROR3: [%s] [%s]\n" % (line, ret3[1]))
            continue

        if line == ret1[0] or line == ret2[0] or line == ret3[0]:
            print("SUCCESS:\n ->[%s]\n   [%s]\n   [%s]\n <-[%s]\n" % (line, ret1[0], ret2[0], ret3[0]))
        elif line_norm == ret1[0] or line_norm == ret2[0] or line_norm == ret2_norm or line_norm == ret3[0]:
            print("RENORM: \n ->[%s]\n   [%s]\n   [%s]\n n>[%s]\n n<[%s]\n <-[%s]\n" % (line_norm, ret1[0], ret2[0], line_norm, ret2_norm, ret3[0]))
        else:
            a = line_norm[:]
            b = ret2_norm[:]

            if len(a) > len(b):
                b += " " * (len(a) - len(b))
            else:
                a += " " * (len(b) - len(a))
            r = ""
            for c,_ in enumerate(a):
                if a[c] == b[c]:
                    r += " "
                else:
                    r += a[c] if a[c] != " " else b[c]
            print("DIFFER: \n ->[%s]\n   [%s]\n   [%s]\n <-[%s]\n n>[%s]\n n<[%s]\n n![%s]\n" % (line, ret1[0], ret2[0], ret3[0], line_norm, ret2_norm, r))
