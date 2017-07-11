import os
from distutils import log

import pkg_resources
import sys
from setuptools import find_packages, setup
from setuptools.command.install import install


class PostInstallConfigFiles(install):

    def run(self):

        # if we use do_egg_install() here,  the bdist_wheel command will fail
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

setup(
    name='benchsuite.stdlib',
    version='2.0.0-dev30',
    packages=find_packages('src'),
    namespace_packages=['benchsuite'],
    package_dir={'': 'src'},
    url='https://github.com/benchmarking-suite/benchsuite-stdlib',
    license='',
    author='Gabriele Giammatteo',
    author_email='gabriele.giammatteo@eng.it',
    description='',
    install_requires = ['paramiko', 'apache-libcloud'],
    #data_files = [('share/benchmarking-suite', ['data/benchmarks/cfd.conf'])],
    # include_package_data=True,
    cmdclass=cmdclass,
    #include_package_data=True,
    setup_requires=['appdirs']

)
