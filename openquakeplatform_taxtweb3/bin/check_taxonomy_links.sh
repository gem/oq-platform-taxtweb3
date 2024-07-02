#!/bin/bash
ddown_items="$(grep push $(find . -name '*.js') | grep dataGemHelp | sed "s/.*gem_taxonomy_base + '//g;s/'.*//g" | sort | uniq)"

# 'direction-x', 'direction-y'
# from views.py:  sub1help = [taxonomy_base + 'direction-x', taxonomy_base + 'direction-y']

simple_items="$(grep data-gem-help openquakeplatform_taxtweb/templates/taxtweb/incl_taxtweb_content.html | sed 's/.*{{ taxonomy_base }}//g;s/".*//g' | sort | uniq)"

for item in $simple_items 'direction-x' 'direction-y' $ddown_items; do
    wget -O /dev/null -q "https://taxonomy.openquake.org/terms/$item"
    if [ $? -ne 0 ]; then
        echo "Page [https://taxonomy.openquake.org/terms/$item] NOT FOUND"
    else
        echo "Page [https://taxonomy.openquake.org/terms/$item] ok"
    fi
    sleep 1
done
