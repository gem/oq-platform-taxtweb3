String.prototype.startswith = function(needle)
{
    return(this.indexOf(needle) == 0);
};


function taxonomy_splitattr(attr)
{
    var re = new RegExp("[^" + gem_tax_subsep + "(]+(\\([^)]*\\))?", "g");
    return [...attr.matchAll(re)];
}

function taxonomy_attrname(attr)
{
    return attr.replace(/\([^\)]+\)$/, '').replace(/:.*/, '');
}

function taxonomy_attrargs(attr)
{
    return (attr.replace(/^[A-Z]+\(/, '').replace(/\)$/, '').split(','));
}

function taxonomy_short2full(t_short)
{
    var tfull = ['', '', '', '', '', '', // Structural System
                 'H99', 'Y99', 'OC99',   // Building Information
                 'BP99', 'PLF99', 'IR99', 'EW99', // Exterior Attributes
                 'RSH99+RMT99+R99+RWC99', 'F99+FWC99', 'FOS99' // Roof/Floor/Foundation
                ];
    tfull_orig = tfull.slice();

    // split the incoming taxonomy
    var t_short = t_short.replace(/\/+$/, "");
    var t_arr = t_short.split('/');
    var is_first_material = is_first_llrs = true;

    for (var i = 0 ; i < t_arr.length ; i++) {
        var t_el = t_arr[i];
        var t_subattrs = taxonomy_splitattr(t_el);

        if (t_subattrs.length == 0)
            continue;


        var t_sub_first = t_subattrs[0][0];
        var t_sub_first_name = taxonomy_attrname(t_sub_first);
        console.log('t_sub_first: ' + t_sub_first);
        console.log('t_sub_first_name: ' + t_sub_first_name);

        if (t_sub_first_name == 'DXP') {
            tfull[tid_xdir] = t_sub_first_name;
            tfull[tid_ydir] = 'DYO';
            continue;
        }
        else if (t_sub_first_name == 'DYO') {
            if (tfull[tid_xdir] != 'DXP') {
                return ({ result: null, err_s: "Found item '" + t_el + "' before its 'DXP' counterpart." });
            }
            tfull[tid_ydir] = t_sub_first_name;
            is_first_material = is_first_llrs = false;
            continue;
        }
        else if (t_sub_first_name in gem_tax['mat']) {
            if (t_sub_first_name in gem_tax['mat_grps']) {
                var grp = gem_tax['mat_grps'][t_sub_first_name];
                if (grp == 'hybrid') {
                    var args = taxonomy_attrargs(t_sub_first);
                    if (args.length == 2) {
                        for (var e = 0 ; e < args.length ; e++) {
                            var arg = args[e];
                            if (!(arg in gem_tax['mat_hyb'])) {
                                return ({ result: null, err_s: "Unknown hybrid material component '" + arg + "'" });
                            }
                        }
                    }
                    else {
                        return ({ result: null, err_s: "Insufficient number of hybrid material components (must be two)" });
                    }
                }
            }

            // FIXME: reorder components HERE with different subel in a prefixed sequence
            for (var e = 1 ; e < t_subattrs.length ; e++) {
                var t_subattr = t_subattrs[e][0];
                var t_subattr_name = taxonomy_attrname(t_subattr);

                console.log('t_subattr: ' + t_subattr);
                console.log('t_subattr_name: ' + t_subattr_name);

                if (t_sub_first_name in gem_tax['mat_grps']) {
                    // special case for HYBrid material
                    if (grp in gem_tax['mat_lone']) {
                        if (t_subattr_name in gem_tax['mat_lone'][grp]) {
                            continue;
                        }
                    }
                    if (grp in gem_tax['mat_loneone']) {
                        if (t_subattr_name in gem_tax['mat_loneone'][grp]) {
                            continue;
                        }
                    }
                    if (t_sub_first_name in gem_tax['mat_ltwo']) {
                        if (t_subattr_name in gem_tax['mat_ltwo'][t_sub_first_name]) {
                            continue;
                        }
                    }
                }
            }

            if (is_first_material) {
                tfull[tid_xmat] = t_el;
                tfull[tid_ymat] = t_el;
            }
            else {
                tfull[tid_ymat] = t_el;
            }
            continue;
        }
        else if (t_sub_first_name in gem_tax['llrs']) {
            console.log('HERE LLRS');
            if (is_first_llrs) {
                tfull[tid_xllrs] = t_el;
                tfull[tid_yllrs] = t_el;
            }
            else {
                tfull[tid_yllrs] = t_el;
            }
        }
    }
    // for (var e = 0 ; e < t_subattrs.length ; e++) {

    console.log(t_short);
    console.log(tfull.join('/'));
    return ({result: tfull.join('/'), err_s: null});
}

function taxonomy_short2full_old(t_short)
{
    var max_pos = 0, tfull_arr, tfull_arr_orig, t_parent = "", t_paridx = 0, t_parnum = 0;

    // console.log('T_SHORT: ' + t_short);

    tfull_arr = ['DX+D99', 'MAT99', 'L99', 'DY+D99', 'MAT99', 'L99', 'H99', 'Y99', 'OC99', 'BP99',
                 'PLF99', 'IR99', 'EW99', 'RSH99+RMT99+R99+RWC99', 'F99+FWC99', 'FOS99'];

    tfull_arr_orig = tfull_arr.slice();

    // split the incoming taxonomy
    if (t_short.slice(-1) == '/') {
        t_short = t_short.slice(0,-1);
    }
    t_arr = t_short.split('/');
    for (var i = 0 ; i < t_arr.length ; i++) {
        t_el = t_arr[i];
        // console.log('T_EL: ' + t_el);
        // revert from hided DX and DY to explicit unknown values
        if (t_el == 'DX') {
            t_el = 'DX+D99';
        }
        else if (t_el == 'PF') {
            t_el = 'DX+PF';
        }

        if (t_el == 'DY') {
            t_el = 'DY+D99';
        }
        else if (t_el == 'PO') {
            t_el = 'DY+PO';
        }

        if (t_el.startswith('DX')) {
            t_parent = "DX";
            t_paridx = i;
            t_parnum++;
        }
        else if (t_el.startswith('DY')) {
            t_parent = "DY";
            t_paridx = i;
            t_parnum++;
        }

        if (t_el == '') {
            // console.log("T_EL EMPTY (" + i + ", " + t_paridx + ")" );
            if (i <= (t_paridx + 2)) {
                var id;

                // console.log("CHILDREN AT: " + (i - t_paridx));
                id = (t_parent == "DX" ? i - t_paridx : i - t_paridx + 3);
                t_el = tfull_arr_orig[id];
                if (max_pos < id) {
                    max_pos = id;
                }
            }
            else {
                t_el = tfull_arr_orig[max_pos];
                max_pos += 1;
            }
        }

        // find the prefix (all what is before '+' or ':' or ',' character
        prefix = t_el.replace('+', ',').replace(':', ',').split(',')[0];

        // if prefix is identified
        if (prefix in taxonomy_map) {
            cur_pos = taxonomy_map[prefix];
            // console.log("FOUND: " + cur_pos + " THE VAL: " + t_el);
            if (cur_pos == 0) {
                // manage special case for coupled DX,DY cell
                if (t_el == 'DX+D99') {
                    tfull_arr[0] = t_el;
                    tfull_arr[3] = 'DY+D99';
                }
                else if (t_el == 'DX+PF') {
                    tfull_arr[0] = t_el;
                    tfull_arr[3] = 'DY+OF';
                }
            }
            else if (cur_pos == 3) {
                // manage special case for coupled DX,DY cell
                if (t_el == 'DY+D99') {
                    tfull_arr[0] = 'DX+D99';
                    tfull_arr[3] = t_el;
                }
                else if (t_el == 'DY+OF') {
                    tfull_arr[0] = 'DX+PF';
                    tfull_arr[3] = t_el;
                }
            }
            else {
                // if no parent set (t_parnum == 0)
                // or parent set for the first time (t_parnum == 1)
                // set DirX and DirY values
                if (cur_pos == 1 || cur_pos == 2) {
                    if (t_parent == 'DY') {
                        cur_pos += 3;
                    }
                    // manage special case paired direction Y cells for
                    // 'Material' or 'Lateral load-resisting system'
                    if (t_parnum <= 1) {
                        // console.log("T_PARNUM <= 1");
                        if (t_parent == '' || t_parent == 'DX') {
                            // console.log('DX parent');
                            // console.log("ASSIGN TO " + (cur_pos + 3) + " THE VAL: " + t_el);
                            tfull_arr[cur_pos+3] = t_el;
                        }
                        else if (t_parent == 'DY') {
                            // console.log('DY parent');
                            // console.log("ASSIGN TO " + (cur_pos - 3) + " THE VAL: " + t_el);
                            tfull_arr[cur_pos-3] = t_el;
                        }
                    }
                }
                // console.log("ASSIGN TO " + cur_pos + " THE VAL: " + t_el);
                tfull_arr[cur_pos] = t_el;
            }

            if (max_pos < cur_pos) {
                max_pos = cur_pos;
            }
        }
        else {
            return ({ result: null, err_s: "Unknown item '" + t_el + "'" });
        }
    }
    return ({result: tfull_arr.join('/'), err_s: null});
}


