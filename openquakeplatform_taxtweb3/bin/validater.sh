#!/bin/bash
# an utility script that perform a coarse conversion from javascript to python
#
# Example
#
# from:
#   function taxt_ValidateRoof()
#   {
#
#       gem$('#RoofCB4').empty();
#       if (gem$('#RoofCB3').val() == 0 || gem$('#RoofCB3').val() == 7) {
#           gem$('#RoofCB4').prop("disabled", true);
#       }
#       else if (gem$('#RoofCB3').val() == 1) {
#           var RoofCB4 = [];
#           /* RM99 */ RoofCB4.push({'_text': 'Masonry roof, unknown', 'dataGemHelp': gem_taxonomy_base +
#               'masonry-unknown--rm99' });
#           /* RM1  */ RoofCB4.push({'_text': 'Vaulted masonry roof', 'dataGemHelp': gem_taxonomy_base +
#               'vaulted-masonry--rm1' });
#           /* RM2  */ RoofCB4.push({'_text': 'Shallow-arched masonry roof', 'dataGemHelp': gem_taxonomy_base +
#               'shallow-arched-masonry--rm2' });
#           /* RM3  */ RoofCB4.push({'_text': 'Composite masonry and concrete roof system',
#               'dataGemHelp': gem_taxonomy_base + 'composite-masonry-and-concrete-roof-system--rm3' });
#           select_populate('RoofCB4', RoofCB4);
#           gem$('#RoofCB4').prop("disabled", false);
#       }
#       else if (...
#
#  to:
#       def taxt_ValidateRoof(self):
#
#           self.RoofCB4.empty()
#           if self.RoofCB3.val() == 0 or self.RoofCB3.val() == 7:
#               self.RoofCB4.disabled(True)
#
#           elif self.RoofCB3.val() == 1:
#               self.RoofCB4.items([
#                   'Masonry roof, unknown',
#                   'Vaulted masonry roof',
#                   'Shallow-arched masonry roof',
#                   'Composite masonry and concrete roof system',
#               ], val=0)
#               self.RoofCB4.disabled(False)
#
#           elif ...

set -x
echo "class placeholder(object):"
cat "$1" | \
    sed "s/^    /        /g" | \
    sed "s/function \([a-zA-Z0-9_]\+\)().*/    def \1(self):/g" | \
    sed "s/gem\$('#\([a-zA-Z0-9_]\+\)')/self.\1/g" | \
    sed "s/.*\.push({'_text': '//g;t lab;b;:lab ;s/'.*//g;s/\(.*\)/                '\1',/g" | \
    sed "s/\.prop(\"\([a-zA-Z0-9_]\+\)\", \([a-zA-Z0-9_]\+\))/.\1(\2)/g" | \
    sed "s/var \([a-zA-Z0-9_]\+\) = \[\]/self.\1.items([/g" | \
    sed "s/select_populate('\([a-zA-Z0-9_]\+\)', .*)/], val=0)/g" | \
    sed "s/\bif (\(.*\)) {/if \1:/g" | \
    sed "s/\belse if/elif/g" | \
    sed "s/\(^ *if \)(\(.*\)) *\$/\1\2:/g" | \
    #    grep -v '^{ *$'| \
    #    grep -v '^ *} *$'| \
    sed 's/\btrue\b/True/g' | \
    sed 's/\bfalse\b/False/g' | \
    sed 's/^{ *$//g' | \
    sed 's/ *} *$//g' | \
    sed 's/) {$/):/g' | \
    sed 's/else {/else:/g' | \
    sed 's/;$//g' | \
    sed 's/||/or/g' | \
    sed 's/&&/and/g' | \
    sed 's@//@#@g' | \
    cat
