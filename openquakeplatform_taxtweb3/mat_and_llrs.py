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

taxt_mat = (
    ('MAT99', 'Unknown Material'),
    ('C99', 'Concrete, unknown reinforcement'),
    ('CU', 'Concrete, unreinforced'),
    ('CR', 'Concrete, reinforced'),
    ('SRC', 'Concrete, composite with steel section'),
    ('S', 'Steel'),
    ('ME', 'Metal (except steel)'),
    ('M99', 'Masonry, unknown reinforcement'),
    ('MUR', 'Masonry, unreinforced'),
    ('MCF', 'Masonry, confined'),
    ('MR', 'Masonry, reinforced'),
    ('E99', 'Earth, unknown reinforcement'),
    ('EU', 'Earth, unreinforced'),
    ('ER', 'Earth, reinforced'),
    ('W', 'Wood'),
    ('MATO', 'Other material')
 )

taxt_llrs = (
    ('L99', 'Unknown lateral load-resisting system'),
    ('LN', 'No lateral load-resisting system'),
    ('LFM', 'Moment frame'),
    ('LFINF', 'Infilled frame'),
    ('LFBR', 'Braced frame'),
    ('LPB', 'Post and beam'),
    ('LWAL', 'Wall'),
    ('LDUAL', 'Dual frame-wall system'),
    ('LFLS', 'Flat slab/plate or waffle slab'),
    ('LFLSINF', 'Infilled flat slab/plate or infilled waffle slab'),
    ('LH', 'Hybrid lateral load-resisting system'),
    ('LO', 'Other lateral load-resisting system')
 )
