#!/bin/bash

function pre_gene () {
    local fin=$1

tr -d '\n' < $fin | \
    sed 's/;/;\n/g;s@/\*@\n/\*@g' | \
    grep dataGemHelp | grep '^/\*[a-zA-Z0-9 :]\+\*/' | \
    sed 's@^/\* *\([a-zA-Z0-9:]\+\) *\*/.*gem_taxonomy_base + '"'"'@\1|@g;s/'"'"'.*//g' | \
    # remove anomalities prefixes
    sed 's/^[A-Z]\+://g' | \
    # remove "same" items
    grep -v '^same|' | \
        cat

    # missing atoms from html templates
    grep -r data-gem-help openquakeplatform_taxtweb/templates | grep -- -- | \
        sed 's/.*{{ taxonomy_base }}//g;s/".*//g' | \
        sed -n 's/.*|//g;h;s/.*--\(.*\)/\U\1/g;H;x;s/\n/|/g;s/^\([^|]\+\)|\([^|]\+\)/\2|\1/g;p'
}

function gene () {
    local fin=$1
    
    pre_gene $fin | \
        sort | uniq | sed 's@\([^|]\+\)|\([^|]\+\)@/terms/\1|/terms/\2@g' | \
        sed 's@|/terms/\([A-Z]\)@|/terms/\L\1@g'
}


#
#  MAIN
#
if [ "$1" = "--pro-sql" ]; then
    pro_sql=y
    shift
fi

fin=openquakeplatform_taxtweb/static/taxtweb/js/taxtweb.js

if [ "$pro_sql" ]; then
    gene $fin
    echo "XXX|/terms/Composite-cast-in-place-reinforced-concrete-and-masonry-floor-system--fm3"
    echo "XXX|/terms/composite-cast-in-place-reinforced-concrete-and-masonry-floor-system--fm3"
    echo "XXX|/terms/Upper-and-lower-bound-for-the-date-of-construction-or-retrofit--ybet"
    echo "XXX|/terms/upper-and-lower-bound-for-the-date-of-construction-or-retrofit--ybet"
    echo "XXX|/terms/Latest-possible-date-of-construction-or-retrofit--ypre"
    echo "XXX|/terms/latest-possible-date-of-construction-or-retrofit--ypre"
else
    gene $fin | sed -n 's/.*|//g;h;s/--/-/g;H;x;s/\n/|/g;p'
    gene $fin | sed 's/--/-/g'
    echo "/terms/Composite-cast-in-place-reinforced-concrete-and-masonry-floor-system--fm3|/terms/composite-cast-in-place-reinforced-concrete-and-masonry-floor-system-fm3"
    echo "/terms/Upper-and-lower-bound-for-the-date-of-construction-or-retrofit--ybet|/terms/upper-and-lower-bound-for-the-date-of-construction-or-retrofit-ybet"
    echo "/terms/Latest-possible-date-of-construction-or-retrofit--ypre|/terms/latest-possible-date-of-construction-or-retrofit-ypre"

    # fix double-dashed alias redirect
    echo "/terms/lime--cement-mortar--mocl|/terms/lime-cement-mortar-mocl"
    echo "/terms/change-in-vertical-structure--include-large-overhangs--chv|/terms/change-in-vertical-structure-include-large-overhangs-chv"
    echo "/terms/2-units--duplex--res2a|/terms/2-units-duplex-res2a"
    echo "/terms/metal--except-steel--me|/terms/metal-except-steel-me"
    
fi
