#!/usr/bin/env python3
import sys
from openquake.taxonomy3.taxtweb_eng import Taxonomy
from openquake.taxonomy3.taxtweb_maps import (
    material, mat_tech_grp, mat_prop_grp, mat_tead_grp,
    llrs_type_grp, llrs_duct_grp,
    h_aboveground, h_belowground, h_abovegrade, h_slope,
    date_type,
    occu_type, occu_spec_grp,
    bupo_type, plsh_type,
    stir_type, plan_irre, plan_seco, vert_irre, vert_seco,
    wall_type,

    roof_shap, roof_cove, roof_mate, roof_sys_grp, roof_conn,
    floo_syma, floo_conn_grp, floo_syty,

    foun_type
)


def smart_concat(s_out, new_out, cur_sep, next_sep):
    '''
    return s_out, next_sep
    '''

    if new_out:
        if s_out:
            s_out += cur_sep
        s_out += new_out
        next_sep = next_sep
    else:
        next_sep = cur_sep
    return (s_out, next_sep)


def dx2human(blk, no_unknown=False):
    atoms = blk.split('+')
    if len(atoms) == 2 and atoms[1] == 'PF':
        return 'X direction parallel to the street'
    elif no_unknown is False:
        return 'X direction unspecified to the street'
    else:
        return ''


def arrdicts_flatten(arrs):
    d = {}
    for arr in arrs:
        for item in arr:
            d[item["id"]] = item
    return d


def llrs2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    atoms = blk.split('+')

    llrs_types = arrdicts_flatten(llrs_type_grp)
    llrs_ducts = arrdicts_flatten(llrs_duct_grp)

    for atom in atoms:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in llrs_types:
            if blk_out:
                blk_out += '; '
            blk_out += ('Type lateral load-resisting system: ' +
                        llrs_types[atom]['desc'])
        elif atom in llrs_ducts:
            if blk_out:
                blk_out += '; '
            blk_out += 'System ductility: ' + llrs_ducts[atom]['desc']
        else:
            blk_err += ' ' + atom + ' not found'

    return (blk_out, blk_err)


def lmat2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    atoms = blk.split('+')

    mat_erials = arrdicts_flatten([material])
    mat_techs = arrdicts_flatten(mat_tech_grp)
    mat_props = arrdicts_flatten(mat_prop_grp)
    mat_teads = arrdicts_flatten(mat_tead_grp)

    for atom in atoms:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in mat_erials:
            if blk_out:
                blk_out += '; '
            blk_out += 'Material type: ' + mat_erials[atom]['desc']
        elif atom in mat_techs:
            if blk_out:
                blk_out += '; '
            blk_out += 'Material technology: ' + mat_techs[atom]['desc']
        elif atom in mat_props:
            if blk_out:
                blk_out += '; '
            blk_out += 'Material properties: ' + mat_props[atom]['desc']
        elif atom in mat_teads:
            if blk_out:
                blk_out += '; '
            blk_out += ('Material technology (additional): ' +
                      mat_teads[atom]['desc'])
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def height2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    subblks = blk.split('+')

    hei_aboveground = arrdicts_flatten([h_aboveground])
    hei_belowground = arrdicts_flatten([h_belowground])
    hei_abovegrade = arrdicts_flatten([h_abovegrade])
    hei_slope = arrdicts_flatten([h_slope])

    for subblk in subblks:
        atoms = subblk.split(':')
        atom = atoms[0]
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in hei_aboveground:
            pfx = 'Number of storeys above ground'
            desc = hei_aboveground[atom]['desc']
            sfx = ''
        elif atom in hei_belowground:
            pfx = 'Number of storeys below ground'
            desc = hei_belowground[atom]['desc']
            sfx = ''
        elif atom in hei_abovegrade:
            pfx = 'Height of ground floor level above grade'
            desc = hei_abovegrade[atom]['desc']
            sfx = ' meters'
        elif atom in hei_slope:
            pfx = 'Slope of the ground'
            desc = hei_slope[atom]['desc']
            sfx = ' degrees'
        else:
            if blk_err:
                blk_err += '; '
            blk_err += 'atom ' + atom + ' unknown'
            continue

        if blk_out:
            blk_out += '; '
        if atom in Taxonomy.ATOM_TYPE_RANGE:
            pars = atoms[1].split(',')
            blk_out += (pfx + ' - ' + desc + ': between ' +
                        pars[0] + ' and ' + pars[1] + sfx)
        elif atom in Taxonomy.ATOM_TYPE_VALUE:
            blk_out += (pfx + ' - ' + desc + ': ' +
                        atoms[1] + sfx)
        else:
            blk_out += (pfx + ' - ' + desc + sfx)

    return (blk_out, blk_err)


def date2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    subblks = blk.split('+')

    dt_type = arrdicts_flatten([date_type])

    for subblk in subblks:
        atoms = subblk.split(':')
        atom = atoms[0]
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in dt_type:
            pfx = 'Date of construction or retrofit'
            desc = dt_type[atom]['desc']
            sfx = ''
        else:
            if blk_err:
                blk_err += '; '
            blk_err += 'atom ' + atom + ' unknown'
            continue

        if blk_out:
            blk_out += '; '
        if atom in Taxonomy.ATOM_TYPE_RANGE:
            pars = atoms[1].split(',')
            blk_out += (pfx + ' - ' + desc + ': between ' +
                        pars[0] + ' and ' + pars[1] + sfx)
        elif atom in Taxonomy.ATOM_TYPE_VALUE:
            blk_out += (pfx + ' - ' + desc + ': ' +
                        atoms[1] + sfx)
        else:
            blk_out += (pfx + ' - ' + desc + sfx)

    return (blk_out, blk_err)


def occupancy2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    atoms = blk.split('+')

    occ_types = arrdicts_flatten([occu_type])
    occ_specs = arrdicts_flatten(occu_spec_grp)

    for atom in atoms:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in occ_types:
            if blk_out:
                blk_out += '; '
            blk_out += ('Building occupancy type: ' +
                        occ_types[atom]['desc'])
        elif atom in occ_specs:
            if blk_out:
                blk_out += '; '
            blk_out += ('Details: ' +
                        occ_specs[atom]['desc'])
        else:
            blk_err += ' ' + atom + ' subblock not found'

    return (blk_out, blk_err)


def position2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""

    bupo_types = arrdicts_flatten([bupo_type])

    for atom in [blk]:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in bupo_types:
            if blk_out:
                blk_out += '; '
            blk_out += ('Building position within a block: ' +
                        bupo_types[atom]['desc'])
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def plan2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""

    plsh_types = arrdicts_flatten([plsh_type])

    for atom in [blk]:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in plsh_types:
            if blk_out:
                blk_out += '; '
            blk_out += ('Shape of the building plan: ' +
                        plsh_types[atom]['desc'])
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def irreg2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    next_sep = '; '

    plan_out = ""
    vert_out = ""

    stir_types = arrdicts_flatten([stir_type])
    plan_irres = arrdicts_flatten([plan_irre])
    plan_secos = arrdicts_flatten([plan_seco])
    vert_irres = arrdicts_flatten([vert_irre])
    vert_secos = arrdicts_flatten([vert_seco])

    atoms = blk.split('+')

    for atom in atoms:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in stir_types:
            blk_out += ('Type of irregularity: ' +
                        stir_types[atom]['desc'])
            next_sep = ' - '
        elif atom in plan_irres:
            plan_out += ('Plan structural irregularity: ' +
                         plan_irres[atom]['desc'])
        elif atom in plan_secos:
            plan_out += (' (primary), ' + plan_secos[atom]['desc'] +
                         ' (secondary)')
        elif atom in vert_irres:
            vert_out += ('Vertical structural irregularity: ' +
                         vert_irres[atom]['desc'])
        elif atom in vert_secos:
            vert_out += (' (primary), ' + vert_secos[atom]['desc'] +
                         ' (secondary)')
        else:
            blk_err += ' ' + atom + ' atom not found'

    if plan_out:
        blk_out += next_sep + plan_out
        next_sep = '; '

    if vert_out:
        blk_out += next_sep + vert_out

    return (blk_out, blk_err)


def extwall2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""

    wall_types = arrdicts_flatten([wall_type])

    for atom in [blk]:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in wall_types:
            if blk_out:
                blk_out += '; '
            blk_out += ('Material of exterior walls: ' +
                        wall_types[atom]['desc'])
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def roof2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    atoms = blk.split('+')

    roof_shaps = arrdicts_flatten([roof_shap])
    roof_coves = arrdicts_flatten([roof_cove])
    roof_mates = arrdicts_flatten([roof_mate])
    roof_syses = arrdicts_flatten(roof_sys_grp)
    roof_conns = arrdicts_flatten([roof_conn])

    for atom in atoms:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in roof_shaps:
            if blk_out:
                blk_out += '; '
            blk_out += 'Roof shape: ' + roof_shaps[atom]['desc']
        elif atom in roof_coves:
            if blk_out:
                blk_out += '; '
            blk_out += 'Roof covering: ' + roof_coves[atom]['desc']
        elif atom in roof_mates:
            if blk_out:
                blk_out += '; '
            blk_out += 'Roof system material: ' + roof_mates[atom]['desc']
        elif atom in roof_syses:
            if blk_out:
                blk_out += '; '
            blk_out += 'Roof system type: ' + roof_syses[atom]['desc']
        elif atom in roof_conns:
            if blk_out:
                blk_out += '; '
            blk_out += 'Roof connections: ' + roof_conns[atom]['desc']
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def floor2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""
    atoms = blk.split('+')

    floo_symas = arrdicts_flatten([floo_syma])
    floo_sytys = arrdicts_flatten([floo_syty])
    floo_conns = arrdicts_flatten(floo_conn_grp)

    for atom in atoms:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in floo_symas:
            if blk_out:
                blk_out += '; '
            blk_out += 'Floor system material: ' + floo_symas[atom]['desc']
        elif atom in floo_sytys:
            if blk_out:
                blk_out += '; '
            blk_out += 'Floor system type: ' + floo_sytys[atom]['desc']
        elif atom in floo_conns:
            if blk_out:
                blk_out += '; '
            blk_out += 'Floor connections: ' + floo_conns[atom]['desc']
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def foundation2human(blk, no_unknown=False):
    blk_out = ""
    blk_err = ""

    foun_types = arrdicts_flatten([foun_type])

    for atom in [blk]:
        if atom in Taxonomy.UNKNOWN_ATOMS and no_unknown:
            continue

        if atom in foun_types:
            if blk_out:
                blk_out += '; '
            blk_out += ('Foundation system: ' +
                        foun_types[atom]['desc'])
        else:
            blk_err += ' ' + atom + ' atom not found'

    return (blk_out, blk_err)


def full_text2human(full_text, no_unknown=False):
    atoms = full_text.split('/')

    # Direction specification
    s_out = dx2human(atoms[Taxonomy.POS_DX], no_unknown=no_unknown)

    dx_lmat = atoms[Taxonomy.POS_DX_LMAT]
    dy_lmat = atoms[Taxonomy.POS_DY_LMAT]
    dx_llrs = atoms[Taxonomy.POS_DX_LLRS]
    dy_llrs = atoms[Taxonomy.POS_DY_LLRS]

    if dx_lmat == dy_lmat and dx_llrs == dy_llrs:
        # Material both
        lmat_out, lmat_err = lmat2human(dx_lmat, no_unknown=no_unknown)
        # LLRS both
        llrs_out, llrs_err = llrs2human(dx_llrs, no_unknown=no_unknown)

        if lmat_out:
            if s_out:
                s_out += '; '
            s_out += lmat_out

        if llrs_out:
            if s_out:
                s_out += '; '
            s_out += llrs_out

        next_sep = '; '

    else:
        dx_out = ''
        dy_out = ''
        # Material DX
        dx_lmat_out, dx_lmat_err = lmat2human(
            dx_lmat, no_unknown=no_unknown)
        # LLRS DX
        dx_llrs_out, dx_llrs_err = llrs2human(
            dx_llrs, no_unknown=no_unknown)

        if dx_lmat_out or dx_llrs_out:
            dx_out += 'For X direction - '

            if dx_lmat_out:
                dx_out += dx_lmat_out
                if dx_llrs_out:
                    dx_out += '; '

            if dx_llrs_out:
                dx_out += dx_llrs_out

        # Material DY
        dy_lmat_out, dy_lmat_err = lmat2human(
            dy_lmat, no_unknown=no_unknown)
        # LLRS DY
        dy_llrs_out, dy_llrs_err = llrs2human(
            dy_llrs, no_unknown=no_unknown)

        if dy_lmat_out or dy_llrs_out:
            if dx_out:
                dx_out += '. '
            dy_out += 'For Y direction - '

            if dy_lmat_out:
                dy_out += dy_lmat_out
                if dy_llrs_out:
                    dy_out += '; '

            if dy_llrs_out:
                dy_out += dy_llrs_out

        if dx_lmat_out or dx_llrs_out or dy_lmat_out or dy_llrs_out:
            if s_out:
                s_out += '. '
            s_out += dx_out + dy_out
            next_sep = '. '

    # height
    hei_out, hei_err = height2human(atoms[Taxonomy.POS_HEIGHT],
                                    no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, hei_out, next_sep, '; ')

    # date
    dt_out, dt_err = date2human(atoms[Taxonomy.POS_DATE],
                                no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, dt_out, next_sep, '; ')

    # occupancy
    occ_out, occ_err = occupancy2human(atoms[Taxonomy.POS_OCCUPANCY],
                                       no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, occ_out, next_sep, '; ')

    # building position
    pos_out, pos_err = position2human(atoms[Taxonomy.POS_POSITION],
                                      no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, pos_out, next_sep, '; ')

    # shape of building plan
    pla_out, pla_err = plan2human(atoms[Taxonomy.POS_PLAN],
                                  no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, pla_out, next_sep, '; ')

    # structural irregularity
    irr_out, irr_err = irreg2human(atoms[Taxonomy.POS_IRREG],
                                   no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, irr_out, next_sep, '; ')

    # exterior wall
    extwall_out, extwall_err = extwall2human(atoms[Taxonomy.POS_EXTWALL],
                                             no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, extwall_out, next_sep, '; ')

    # roof
    roof_out, roof_err = roof2human(atoms[Taxonomy.POS_ROOF],
                                    no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, roof_out, next_sep, '; ')

    # floor
    floor_out, floor_err = floor2human(atoms[Taxonomy.POS_FLOOR],
                                       no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, floor_out, next_sep, '; ')

    # foundation
    foun_out, foun_err = foundation2human(atoms[Taxonomy.POS_FOUNDATION],
                                          no_unknown=no_unknown)
    s_out, next_sep = smart_concat(s_out, foun_out, next_sep, '; ')

    if s_out:
        s_out += '.'

    return s_out


def taxonomy2human(s, no_unknown=True):
    t = Taxonomy('Taxonomy', True)

    full_text, full_res = t.process(s, 0)

    if full_res is None:
        s_out = full_text2human(full_text, no_unknown=no_unknown)
    else:
        s_out = "Invalid GEM Taxonomy v2.0 string: %s" % s

    return s_out


def taxonomy2human_cmd():
    print(taxonomy2human(sys.argv[1], no_unknown=True))


if __name__ == '__main__':
    taxonomy2human_cmd()
