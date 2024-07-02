#!/usr/bin/env python
from openquake.taxonomy3.taxtweb_maps import (
    mat_tech_grp, mat_tead_grp, mat_prop_grp,
    llrs_type_grp, llrs_duct_grp, occu_spec_grp,
    roof_sys_grp, floo_conn_grp)

mat_tech =\
    { 'MAT99': [],
      'C99': mat_tech_grp[1],

      'CU':  mat_tech_grp[0],

      'CR':  mat_tech_grp[1],
      'SRC': mat_tech_grp[1],

      'S':   mat_tech_grp[2],

      'ME':  mat_tech_grp[3],

      'M99': mat_tech_grp[4],
      'MUR': mat_tech_grp[4],
      'MCF': mat_tech_grp[4],
      'MR':  mat_tech_grp[4],

      'E99': mat_tech_grp[5],
      'EU':  mat_tech_grp[5],
      'ER':  mat_tech_grp[5],

      'W':   mat_tech_grp[6],

      'MATO': []
    }

mat_tead =\
    { 'MAT99': [],
      'C99':   [],
      'CU':    [],
      'CR':    [],
      'SRC':   [],
      'S':     [],
      'ME':    [],
      'M99':   [],
      'MUR':   [],
      'MCF':   [],
      'MR':    mat_tead_grp[0],
      'E99':   [],
      'EU':    [],
      'ER':    [],
      'W':     [],
      'MATO':  []
    }

mat_prop =\
    { 'MAT99': [],
      'C99':   [],

      'CU':    [],

      'CR':    [],
      'SRC':   [],

      'S':   mat_prop_grp[0],

      'ME':    [],

      'M99': mat_prop_grp[1],
      'MUR': mat_prop_grp[1],
      'MCF': mat_prop_grp[1],
      'MR':  mat_prop_grp[1],

      'E99':  [],
      'EU':   [],
      'ER':   [],

      'W':    [],

      'MATO': []
    }

llrs_type =\
    { 'MAT99':llrs_type_grp[2],
      'C99':  llrs_type_grp[2],
      'CU':   llrs_type_grp[2],
      'CR':   llrs_type_grp[2],
      'SRC':  llrs_type_grp[2],
      'S':    llrs_type_grp[2],
      'ME':   llrs_type_grp[2],

      'M99':  llrs_type_grp[1],
      'MUR':  llrs_type_grp[1],
      'MCF':  llrs_type_grp[1],
      'MR':   llrs_type_grp[1],

      'E99':  llrs_type_grp[0],
      'EU':   llrs_type_grp[0],
      'ER':   llrs_type_grp[0],

      'W':    llrs_type_grp[1],

      'MATO': llrs_type_grp[2]
    }

llrs_duct =\
    { 'L99': [],
      'LN': [],
      'LFM': llrs_duct_grp[0],
      'LFINF': llrs_duct_grp[0],
      'LFBR': llrs_duct_grp[0],
      'LPB': llrs_duct_grp[0],
      'LWAL': llrs_duct_grp[0],
      'LDUAL': llrs_duct_grp[0],
      'LFLS': llrs_duct_grp[0],
      'LFLSINF': llrs_duct_grp[0],
      'LH': llrs_duct_grp[0],
      'LO': llrs_duct_grp[0]
    }

occu_spec =\
    { 'OC99': [],
      'RES': occu_spec_grp[0],
      'COM': occu_spec_grp[1],
      'MIX': occu_spec_grp[2],
      'IND': occu_spec_grp[3],
      'AGR': occu_spec_grp[4],
      'ASS': occu_spec_grp[5],
      'GOV': occu_spec_grp[6],
      'EDU': occu_spec_grp[7],
      'OCO': []
    }


roof_sys =\
    { 'R99': [],
      'RM':  roof_sys_grp[0],
      'RE':  roof_sys_grp[1],
      'RC':  roof_sys_grp[2],
      'RME': roof_sys_grp[3],
      'RWO': roof_sys_grp[4],
      'RFA': roof_sys_grp[5],
      'RO':  []
    }

floo_conn =\
    { 'F99': [],
      'FN':  [],
      'FM':  floo_conn_grp[0],
      'FE':  floo_conn_grp[1],
      'FC':  floo_conn_grp[2],
      'FME': floo_conn_grp[3],
      'FW':  floo_conn_grp[4],
      'FO':  []
    }

if __name__ == '__main__':
    print(__name__)
