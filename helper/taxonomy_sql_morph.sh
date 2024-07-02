#!/bin/bash
fin=$1
fot=$2

if [ $# -ne 2 ]; then
    exit 1
fi

IFS='
'
cp "$fot" "taxonomy_morphed.sql"
for r in $(cat $fin); do
    url=$(echo "$r" | sed 's@.*|/terms/@@g')
    echo "$url"
    new_url="$(echo "$url" | sed 's/--/-/g')"
    sed -i "s/\b${url}\b/$new_url/g" "taxonomy_morphed.sql"
done
