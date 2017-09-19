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

import logging
import re
import textwrap

import sys

from benchsuite.stdlib.execution.vm_environment import VMSetExecutionEnvironmentRequest
from benchsuite.stdlib.execution.sshworker import PureRemoteBashExecutor
from benchsuite.core.model.benchmark import Benchmark

logger = logging.getLogger(__name__)

#
# DEFAULT_INSTALL_REDHAT = '''
# sudo wget http://etics.res.eng.it/repository/pm/registered/repomd/global/artist/centos6.5_x86_64_gcc447/etics-registered-artist.repo -O /etc/yum.repos.d/artist.repo;
# sudo yum -y install %(required_packages)s
# '''
#
# DEFAULT_POSTINSTALL_REDHAT = '''
# echo Nothing to execute
# '''
#
# DEFAULT_INSTALL_DEBIAN = '''
# sudo wget http://etics.res.eng.it/repository/pm/registered/apt/global/artist/deb7.4_x86_64_gcc472-5/etics-registered-artist.list -O /etc/apt/sources.list.d/Artist.list
# sudo apt-get update;
# sudo apt-get -y --force-yes install %(required_packages)s
# '''
#
# DEFAULT_POSTINSTALL_DEBIAN = '''
# echo Nothing to execute
# '''
#
# DEFAULT_POSTINSTALL_CENTOS = '''
# echo Nothing to execute
# '''
#
#
# DEFAULT_INSTALL_UBUNTU = '''
# echo "Nothing to execute"
# '''
#
# DEFAULT_POSTINSTALL_UBUNTU = '''
# echo "Nothing to execute"
# '''

#
#
# class BenchmarkFactory:
#
#     def __init__(self, config_folder):
#         self.config_folder = config_folder
#
#     def get_all_benchmark_tests(self, benchmark_name=None):
#         pass
#

class BashCommandBenchmark(Benchmark):

    def __init__(self, tool_id, workload_id, tool_name, workload_name, workload_description):
        super().__init__(tool_id, workload_id, tool_name, workload_name, workload_description)
        self._props = {}

    def get_env_request(self):
        return VMSetExecutionEnvironmentRequest(1)

    def prepare(self, execution):
        executor = PureRemoteBashExecutor(execution)
        executor.install()

    def execute(self, execution, async=False):
        executor = PureRemoteBashExecutor(execution)
        executor.run(async=async)

    def get_result(self, execution):
        executor = PureRemoteBashExecutor(execution)
        return executor.collect_results()

    def get_install_script(self, platform, interpolation_dict = {}):
        return self.__get_script('install', platform, interpolation_dict)

    def get_postinstall_script(self, platform, interpolation_dict = {}):
        return self.__get_script('postinstall', platform, interpolation_dict)

    def get_execute_script(self, platform, interpolation_dict = {}):
        return self.__get_script('execute', platform, interpolation_dict)

    def get_remove_script(self, platform, interpolation_dict = {}):
        return self.__get_script('remove', platform, interpolation_dict)

    def __get_script(self, type, platform, interpolation_dict):

        # try with the exact platform name (e.g. install_ubuntu_16.04)
        if type + '_' + platform in self._props:
            return textwrap.dedent(self.__replace_cp_properties(
                self._props[type + '_' + platform], interpolation_dict)).strip()

        # try with the first token of the platform (e.g. install_ubuntu) assuming
        # the platform name is in the form <platformName>_<release>
        t = platform.split('_')
        if len(t) > 1:
            if type + '_' + t[0] in self._props:
                return textwrap.dedent(self.__replace_cp_properties(
                    self._props[type + '_' + t[0]], interpolation_dict)).strip()

        # try without the platform (e.g. install)
        if type in self._props:
            return textwrap.dedent(self.__replace_cp_properties(
                self._props[type], interpolation_dict)).strip()

        return None
        # default = getattr(sys.modules[__name__],
        #                   'DEFAULT_' + type.upper() + '_' + platform.upper())
        #
        # return self.__replace_cp_properties(
        #     default % self.__dict__, interpolation_dict)

    def __replace_cp_properties(self, string, interpolation_dict):

        for occ in re.findall('\$\$.*\$\$', string):
            if occ[2:-2] in interpolation_dict:
                string = string.replace(occ, interpolation_dict[occ[2:-2]])

        return string


    @staticmethod
    def load_from_config_file(config, tool, workload):

        if 'parser' in config['DEFAULT']:
            parser_class = config['DEFAULT']['parser']
            module_name, class_name = parser_class.rsplit('.', 1)

            __import__(module_name)
            module = sys.modules[module_name]
            parser = getattr(module, class_name)()
        else:
            parser = None

        instance = BashCommandBenchmark(
            tool, workload,
            config[workload]['tool_name'] if 'tool_name' in config[workload] else None,
            config[workload]['workload_name'] if 'workload_name' in config[workload] else None,
            config[workload]['workload_description'] if 'workload_description' in config[workload] else None
        )

        for k, v in config.items(workload):
            instance._props[k] = v

        instance.parser = parser

        return instance


