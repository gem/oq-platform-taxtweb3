#!/bin/bash
fin="$1"
IFS='
'
HOST="https://taxonomy.openquake.org"
for r in $(cat $fin); do
    add="$(echo "$r" | cut -d '|' -f 2)"
    url="${HOST}$add"
    rm -f _test.html
    curl -s -o _test.html "$url"
    if grep -q '<meta http-equiv="refresh"' _test.html; then
        echo "NOT FOUND $r"
    else
        echo "OK $r"
    fi
    sleep 1
done
rm -f _test.html
    
         
         
