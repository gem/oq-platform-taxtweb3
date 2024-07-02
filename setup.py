# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2019 GEM Foundation
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

import os
import re
import sys
from setuptools import setup
from setuptools.command import egg_info

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

pybuild_name = os.environ.get('PYBUILD_NAME', 'oq-platform-taxtweb3')

if pybuild_name == 'oq-platform-taxtweb3':
    def get_version():
        version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
        version = None

        package_init = 'openquakeplatform_taxtweb3/__init__.py'
        for line in open(package_init, 'r'):
            version_match = re.search(version_re, line, re.M)
            if version_match:
                version = version_match.group(1)
                break
        else:
            sys.exit('__version__ variable not found in %s' % package_init)

        return version

    version = get_version()

    setup(
        name='oq-platform-taxtweb3',
        version=version,
        packages=["openquakeplatform_taxtweb3"],
        include_package_data=True,
        license="AGPL3",
        description='Taxtweb - GEM building taxonomy editor',
        long_description=README,
        url='http://github.com/gem/oq-platform-taxtweb3',
        author='GEM Foundation',
        author_email='devops@openquake.org',
        install_requires=[
            'django >=4.2, <5',
        ],
        classifiers=[
            'Environment :: Web Environment',
            'Framework :: Django',
            'Intended Audience :: Scientists',
            'License :: OSI Approved :: AGPL3',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Topic :: Internet :: WWW/HTTP',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        ],
    )
elif pybuild_name == 'oq-taxonomy3':
    egg_info.manifest_maker.template = 'MANIFEST_taxonomy3.in'

    def get_version():
        version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
        version = None

        package_init = 'openquake/taxonomy3/__init__.py'
        for line in open(package_init, 'r'):
            version_match = re.search(version_re, line, re.M)
            if version_match:
                version = version_match.group(1)
                break
        else:
            sys.exit('__version__ variable not found in %s' % package_init)

        return version

    version = get_version()

    url = "https://github.com/gem/oq-platform-taxtweb3"

    install_requires = []
    extras_require = {}

    setup(
        name="openquake.taxonomy3",
        version=version,
        author="GEM Foundation",
        author_email="devops@openquake.org",
        maintainer='GEM Foundation',
        maintainer_email='devops@openquake.org',
        description=("Computes earthquake hazard and risk."),
        license="AGPL3",
        keywords="earthquake seismic risk taxonomy version 3",
        url=url,
        long_description=README,
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Education',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 3',
            'License :: OSI Approved :: GNU Affero General Public License v3',
            'Operating System :: OS Independent',
            'Topic :: Scientific/Engineering',
            'Environment :: Console',
            'Environment :: Web Environment',
        ],
        packages=['openquake', 'openquake.taxonomy3'],
        include_package_data=True,
        package_data={"openquake.taxonomy3": [
            "README.md", "LICENSE"]},
        namespace_packages=['openquake'],
        install_requires=install_requires,
        extras_require=extras_require,
        entry_points={
            'console_scripts': [
                'taxonomy2human = openquake.taxonomy3.'
                'taxonomy2human:taxonomy2human_cmd'],
        },
        #test_loader='openquake.baselib.runtests:TestLoader',
        #test_suite='openquake.risklib,openquake.commonlib,openquake.calculators',
        zip_safe=True,
        )

