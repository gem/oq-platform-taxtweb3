#!/bin/bash
# set -x

# this script split original javascript code and create a separate file for
# each javascript function end convert static javascript datasets (dictionaries
# and lists) to python equivalents
#
# Example:
#
# from:
#
#   var mat_tech =
#       { 'MAT99': [],
#         'C99': mat_tech_grp[1],
#
#         'CU':  mat_tech_grp[0],
#
#         'CR':  mat_tech_grp[1],
#         'SRC': mat_tech_grp[1],
#
#         'S':   mat_tech_grp[2],
#         ....
#
#   to:
#
#   #!/usr/bin/env python
#   from utils.taxtweb_maps import *
#   mat_tech = \
#       { 'MAT99': [],
#         'C99': mat_tech_grp[1],
#
#         'CU':  mat_tech_grp[0],
#
#         'CR':  mat_tech_grp[1],
#         'SRC': mat_tech_grp[1],
#
#         'S':   mat_tech_grp[2],
#         ....

vars_to_py () {
    local MAPS_FILE="$1"
    local TARGET_FILE="$2"
    local PREFIX="$3"

    rm -f ${TMPD}/tmp.$$

    (
        echo "#!/usr/bin/env python"
        echo "$PREFIX"
        cat "$MAPS_FILE" | \
            sed 's/;$//g' | \
            sed 's/^var //g' | \
            sed "s/\b\([a-z]\+\):/'\1':/g" | \
            sed 's/\(.* = *\)$/\1 \\/g'
        echo "if __name__ == '__main__':"
        echo "    print(__name__)"
    ) > ${TMPD}/tmp.$$

    IFS='
'
    for und in $(grep 'var [a-z_]\+ = \[\]' "$MAPS_FILE"); do
        und_name="$(echo "$und" | sed 's/^var //g;s/ = .*//g')"
        # echo "$und [$und_name]"
        max_id=-1
        for item in $(grep "^${und_name}\[" "$MAPS_FILE"); do
            # echo "$item"
            new_id="$(echo "$item" | sed 's/^[^\[]*\[//g;s/\].*//g')"
            # echo "$new_id"
            if [ $max_id -lt $new_id ]; then
                max_id=$new_id
            fi
        done
        max_id=$((max_id + 1))
        sed -i "s/${und_name} = \[\]/${und_name} = [0] \* $max_id/g" ${TMPD}/tmp.$$
    done

    mv ${TMPD}/tmp.$$ "$TARGET_FILE"
}


#
#  MAIN
#

TMPD=./py_tmp
rm -rf "$TMPD"
mkdir "$TMPD"

vars_to_py 'static/taxtweb/js/taxtweb_maps.js' 'utils/taxtweb_maps.py'

sed -n '/^function /b lab;p;d; : lab q' 'static/taxtweb/js/taxtweb.js' >${TMPD}/taxtweb.$$
vars_to_py ${TMPD}/taxtweb.$$ ${TMPD}/taxtweb_head.py.$$ "from utils.taxtweb_maps import *"

mkdir ${TMPD}/funcs
for func_name in $(grep '^function' 'static/taxtweb/js/taxtweb.js' | sed 's/^function //g;s/(.*//g' ); do
    echo "$func_name"
    sed -n "/^function $func_name/,/^} *$/p" 'static/taxtweb/js/taxtweb.js' > ${TMPD}/funcs/${func_name}.js
done
