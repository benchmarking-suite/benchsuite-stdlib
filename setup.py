# Benchmarking Suite
# Copyright 2014-2017 Engineering Ingegneria Informatica S.p.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Developed in the ARTIST EU project (www.artist-project.eu) and in the
# CloudPerfect EU project (https://cloudperfect.eu/)

import os
from distutils import log

import pkg_resources
import sys
from setuptools import find_packages, setup
from setuptools.command.install import install


class PostInstallConfigFiles(install):

    def run(self):

        # if we use do_egg_install() here, the bdist_wheel command will fail
        install.run(self)

        try:
            # install benchmarks
            from appdirs import user_config_dir
            dest_dir = os.path.join(user_config_dir('benchmarking-suite'), 'benchmarks')
            log.info('Installing default stdlib benchmarks configuration into {0}'.format(dest_dir))
            os.makedirs(dest_dir, exist_ok=True)
            #files = pkg_resources.resource_listdir(pkg_resources.Requirement.parse("benchsuite.stdlib"), '/'.join(('benchsuite','stdlib', 'data', 'benchmarks')))
            files = os.listdir('data/benchmarks')
            for f in [file for file in files if file.endswith('.conf')]:
                # content = pkg_resources.resource_string(pkg_resources.Requirement.parse("benchsuite.stdlib"),'/'.join(('benchsuite','stdlib', 'data', 'benchmarks', f)))
                with open('data/benchmarks/'+f, 'r') as myfile:
                    content = myfile.read()
                dest_file = os.path.join(dest_dir, f)
                log.info('Installing {0} in {1}'.format(f, dest_file))
                if os.path.isfile(dest_file):
                    log.debug('File {0} already exists. Renaming it to {1}'.format(dest_file, dest_file+'.bkp'))
                    os.rename(dest_file, dest_file + '.bkp')
                with open(dest_file, "w") as text_file:
                    text_file.write(content)

            # install providers
            dest_dir = os.path.join(user_config_dir('benchmarking-suite'), 'providers')
            log.info('Installing default stdlib providers configuration into {0}'.format(dest_dir))
            os.makedirs(dest_dir, exist_ok=True)
            #files = pkg_resources.resource_listdir(pkg_resources.Requirement.parse("benchsuite.stdlib"), '/'.join(('benchsuite','stdlib', 'data', 'providers')))
            files = os.listdir('data/providers')
            for f in [file for file in files if file.endswith('.conf.example')]:
                #content = pkg_resources.resource_string(pkg_resources.Requirement.parse("benchsuite.stdlib"),'/'.join(('benchsuite','stdlib', 'data', 'providers', f)))
                with open('data/providers/' + f, 'r') as myfile:
                    content = myfile.read()
                dest_file = os.path.join(dest_dir, f)
                log.info('Installing {0} in {1}'.format(f, dest_file))
                if os.path.isfile(dest_file):
                    log.debug('File {0} already exists. Renaming it to {1}'.format(dest_file, dest_file+'.bkp'))
                    os.rename(dest_file, dest_file + '.bkp')
                with open(dest_file, "w") as text_file:
                    text_file.write(content)

        except pkg_resources.DistributionNotFound as ex:
            # this might be normal when invoked with bdist_wheel because the package is not installed yet..??
            #
            raise ex



if 'install' in sys.argv or  'bdist_wheel' in sys.argv:
    cmdclass = {'install': PostInstallConfigFiles}
else:
    cmdclass={}


# import the VERSION from the source code
import sys
sys.path.append(os.getcwd() + '/src/benchsuite')
from stdlib import VERSION

setup(
    name='benchsuite.stdlib',
    version='.'.join(map(str, VERSION)),

    description='The standard library for Benchmarking Suite',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),

    url='https://github.com/benchmarking-suite/benchsuite-stdlib',

    author='Gabriele Giammatteo',
    author_email='gabriele.giammatteo@eng.it',

    license='Apache',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Topic :: System :: Benchmark',
        'Topic :: Utilities',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Environment :: Console',
        'Operating System :: Unix'
    ],
    keywords='benchmarking cloud testing performance',

    packages=find_packages('src'),
    namespace_packages=['benchsuite'],
    package_dir={'': 'src'},

    install_requires = ['paramiko', 'apache-libcloud'],
    setup_requires = ['appdirs'],

    cmdclass = cmdclass
)
