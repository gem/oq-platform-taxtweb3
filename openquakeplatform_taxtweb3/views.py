# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from django.http import HttpResponse
from django.shortcuts import render
import json
from openquake.taxonomy.taxtweb_eng import Taxonomy
from openquake.taxonomy.taxonomy2human import full_text2human

try:
    from openquakeplatform.settings import STANDALONE
except ImportError:
    STANDALONE = False


def index(request, **kwargs):
    try:
        tab_id = int(request.GET.get("tab_id", 1))
        if tab_id < 1 or tab_id > 4:
            tab_id = 1
    except ValueError:
        tab_id = 1

    subtab_id = 1
    if tab_id == 1:
        try:
            subtab_id = int(request.GET.get("subtab_id", 1))
            if subtab_id < 1 or subtab_id > 2:
                subtab_id = 1
        except ValueError:
            subtab_id = 1

    if 'HTTP_HOST' in request.META:
        proto = (request.META['HTTP_X_FORWARDED_PROTO'].split(', ')[-1] if
                 'HTTP_X_FORWARDED_PROTO' in request.META else 'http')
        if request.META['HTTP_HOST'].startswith('taxtweb3'):
            taxt_prefix = proto + '://' + request.META['HTTP_HOST']
        else:
            taxt_prefix = (proto + '://' + request.META['HTTP_HOST']
                           + '/taxtweb3')
    else:
        taxt_prefix = "http://taxtweb3.openquake.org"

    desc = ['Structural System',
            'Building Information',
            'Exterior Attributes',
            'Roof/Floor/Foundation']
    tab_content = ""
    for i in range(0, len(desc)):
        tab_content = (tab_content +
                       '<li id="tab_id-%d" class="tab%s%s" onclick="tab_set(this);"><span>%s</span></li>' %
                       (i+1, ("_selected" if i + 1 == tab_id else ""),
                        (" tab_first" if i == 0 else ""), desc[i]))

    sub1desc = ['Direction X', 'Direction Y']
    taxonomy_base = ('https://taxonomy.openquake.org/terms/'
                     if not STANDALONE else '/taxonomy/')
    sub1help = [taxonomy_base + 'direction-x',
                taxonomy_base + 'direction-y',
                ]
    sub1tab_content = ""
    for i in range(0, len(sub1desc)):
        sub1tab_content = (sub1tab_content +
                           '<li id="sub1tab_id-%d" class="subtab%s%s" onclick="sub1tab_set(this);" data-gem-help="%s"><span>%s</span></li>' %
                           (i+1, ("_selected" if i + 1 == subtab_id else ""),
                            (" subtab_first" if i == 0 else ""),
                            sub1help[i], sub1desc[i]))

    is_popup = (False if request.GET.get("is_popup", False) == False else True)

    taxonomy = kwargs['taxonomy'] if 'taxonomy' in kwargs else ""

    return render(request, ("taxtweb3/index_popup.html" if is_popup
                            else "taxtweb3/index.html"),
                  dict(taxonomy_base=taxonomy_base,
                       taxonomy=taxonomy,
                       is_popup=is_popup,
                       tab_id=tab_id,
                       subtab_id=subtab_id,
                       tab_content=tab_content,
                       sub1tab_content=sub1tab_content,
                       taxt_prefix=taxt_prefix,
                       jquery="$",
                       ))


def checker(request, **kwargs):
    taxonomy = kwargs['taxonomy'][1:] if 'taxonomy' in kwargs else ""

    if 'HTTP_HOST' in request.META:
        proto = (request.META['HTTP_X_FORWARDED_PROTO'] if
                 'HTTP_X_FORWARDED_PROTO' in request.META else 'http')
        if request.META['HTTP_HOST'].startswith('taxtweb3'):
            taxt_prefix = proto + '://' + request.META['HTTP_HOST']
        else:
            taxt_prefix = (proto + '://' + request.META['HTTP_HOST']
                           + '/taxtweb3')
    else:
        taxt_prefix = "http://taxtweb3.openquake.org"

    is_popup = ""
    tab_id = ""
    subtab_id = ""
    tab_content = ""
    sub1tab_content = ""

    return render(request, "taxtweb3/checker.html",
                  dict(taxonomy=taxonomy,
                       is_popup=is_popup,
                       tab_id=tab_id,
                       subtab_id=subtab_id,
                       tab_content=tab_content,
                       sub1tab_content=sub1tab_content,
                       taxt_prefix=taxt_prefix,
                       jquery="sim_dollar",
                       ))


def explanation(request, **kwargs):
    taxonomy = kwargs['taxonomy'][1:] if 'taxonomy' in kwargs else ""

    t = Taxonomy('Taxonomy', True)

    if taxonomy == "":
        res = {
            'error': 2,
            'message': "Empty taxonomy."
        }
        return HttpResponse(json.dumps(res), content_type="application/json")

    full_text, full_res = t.process(taxonomy, 0)

    if full_res is None:
        err = 0
        msg = full_text2human(full_text, no_unknown=True)
    else:
        err = 1
        msg = full_res

    res = {
        'error': err,
        'message': msg
    }
    return HttpResponse(json.dumps(res), content_type="application/json")
