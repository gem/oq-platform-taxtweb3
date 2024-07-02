from .taxonomy_map import taxonomy_map


class Ret(object):
    def __init__(self, result=None, s=None):
        self.result = result
        self.s = s


def taxonomy_short2full(t_short):

    # tfull_arr, tfull_arr_orig,
    max_pos = 0
    t_parent = ""
    t_paridx = 0
    t_parnum = 0

    # console.log('T_SHORT: ' + t_short)

    tfull_arr = [
        'DX+D99', 'MAT99', 'L99', 'DY+D99', 'MAT99', 'L99', 'H99', 'Y99',
        'OC99', 'BP99', 'PLF99', 'IR99', 'EW99', 'RSH99+RMT99+R99+RWC99',
        'F99+FWC99', 'FOS99']

    tfull_arr_orig = tfull_arr[:]

    # split the incoming taxonomy
    if t_short[-1] == '/':
        t_short = t_short[0:-1]

    t_arr = t_short.split('/')
    for i in range(0, len(t_arr)):
        t_el = t_arr[i]
        # console.log('T_EL: ' + t_el)
        # revert from hided DX and DY to explicit unknown values
        if t_el == 'DX':
            t_el = 'DX+D99'
        elif t_el == 'PF':
            t_el = 'DX+PF'

        if t_el == 'DY':
            t_el = 'DY+D99'
        elif t_el == 'PO':
            t_el = 'DY+PO'

        if t_el.startswith('DX'):
            t_parent = "DX"
            t_paridx = i
            t_parnum += 1
        elif t_el.startswith('DY'):
            t_parent = "DY"
            t_paridx = i
            t_parnum += 1

        if t_el == '':
            if i <= t_paridx + 2:
                id = i - t_paridx if t_parent == "DX" else i - t_paridx + 3
                t_el = tfull_arr_orig[id]
                if max_pos < id:
                    max_pos = id
            else:
                t_el = tfull_arr_orig[max_pos]
                max_pos += 1

        # find the prefix (all what is before '+' or ':' or ',' character
        prefix = t_el.replace('+', ',').replace(':', ',').split(',')[0]
        # print "DEBUG PREFIX: %s" % prefix
        # if prefix is identified
        if prefix in taxonomy_map:
            cur_pos = taxonomy_map[prefix]
            # console.log("FOUND: " + cur_pos + " THE VAL: " + t_el)
            if cur_pos == 0:
                # manage special case for coupled DX,DY cell
                if t_el == 'DX+D99':
                    tfull_arr[0] = t_el
                    tfull_arr[3] = 'DY+D99'

                elif t_el == 'DX+PF':
                    tfull_arr[0] = t_el
                    tfull_arr[3] = 'DY+OF'

            elif cur_pos == 3:
                # manage special case for coupled DX,DY cell
                if t_el == 'DY+D99':
                    tfull_arr[0] = 'DX+D99'
                    tfull_arr[3] = t_el

                elif t_el == 'DY+OF':
                    tfull_arr[0] = 'DX+PF'
                    tfull_arr[3] = t_el

            else:
                # if no parent set (t_parnum == 0)
                # or parent set for the first time (t_parnum == 1)
                # set DirX and DirY values
                # print "  DEBUG ELSE %d" % cur_pos
                if cur_pos == 1 or cur_pos == 2:
                    if t_parent == 'DY':
                        cur_pos += 3

                    # manage special case paired direction Y cells for
                    # 'Material' or 'Lateral load-resisting system'
                    if t_parnum <= 1:
                        # console.log("T_PARNUM <= 1")
                        if t_parent == '' or t_parent == 'DX':
                            # console.log('DX parent')
                            # console.log("ASSIGN TO " + (cur_pos + 3) + " THE VAL: " + t_el)
                            tfull_arr[cur_pos+3] = t_el

                        elif t_parent == 'DY':
                            # console.log('DY parent')
                            # console.log("ASSIGN TO " + (cur_pos - 3) + " THE VAL: " + t_el)
                            tfull_arr[cur_pos-3] = t_el

                # console.log("ASSIGN TO " + cur_pos + " THE VAL: " + t_el)
                tfull_arr[cur_pos] = t_el
                cur_pos += 1

            if max_pos < cur_pos:
                max_pos = cur_pos

        else:
            return (Ret(result=None, s="Unknown item '" + t_el + "'"))

    return (Ret(result='/'.join(tfull_arr), s=None))
