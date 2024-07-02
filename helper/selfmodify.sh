#!/bin/bash
fin=$1
fot=$2

IFS='
'
for r in $(cat $fin); do
    url=$(echo "$r" | sed 's@.*|/terms/@@g')
    echo "$url"
    new_url="$(echo "$url" | sed 's/--/-/g')"
    sed -i "s/\b${url}\b/$new_url/g" $(find openquakeplatform_taxtweb/templates/ -type f ; echo "openquakeplatform_taxtweb/static/taxtweb/js/taxtweb.js")
done
