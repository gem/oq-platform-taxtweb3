String.prototype.startswith = function(needle)
{
    return(this.indexOf(needle) == 0);
};




function taxonomy_short2full(t_short)
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


