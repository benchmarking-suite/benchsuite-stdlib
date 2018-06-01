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
from benchsuite.stdlib.execution.sshexecutor import RemoteSSHExecutor
from benchsuite.core.model.benchmark import Benchmark

logger = logging.getLogger(__name__)

class BashCommandBenchmark(Benchmark):

    def __init__(self, tool_id, workload_id, tool_name, workload_name, workload_categories, workload_description):
        super().__init__(tool_id, workload_id, tool_name, workload_name,
                         workload_categories, workload_description)
        self._props = {}

    def get_env_request(self):
        return VMSetExecutionEnvironmentRequest(1)

    def prepare(self, execution):
        executor = RemoteSSHExecutor(execution)
        executor.install()

    def execute(self, execution, async=False):
        executor = RemoteSSHExecutor(execution)
        executor.run(async=async)

    def get_result(self, execution):
        executor = RemoteSSHExecutor(execution)
        return executor.collect_results()

    def get_runtime(self, execution, phase):
        executor = RemoteSSHExecutor(execution)
        return executor.get_runtime(phase)

    def get_install_script(self, platform, interpolation_dict = {}):
        return self.__get_script('install', platform, interpolation_dict)

    def get_postinstall_script(self, platform, interpolation_dict = {}):
        return self.__get_script('postinstall', platform, interpolation_dict)

    def get_execute_script(self, platform, interpolation_dict = {}):
        return self.__get_script('execute', platform, interpolation_dict)

    def get_remove_script(self, platform, interpolation_dict = {}):
        return self.__get_script('remove', platform, interpolation_dict)

    def __get_script(self, type, platform, interpolation_dict):

        # First try to search keys that have a combination of <type>_<platform_tokens>
        # The platform is tokenized at "_" characters
        # E.g. if the platform is 'ubuntu_14_04_r2' try with:
        # - install_ubuntu_14_04_r2
        # - install_ubuntu_14_04
        # - install_ubuntu_14
        # - install_ubuntu
        # the first one (or if there are no _ in the platform string) will be
        # the exact platform string
        t = platform.split('_')

        for i in range(len(t), 0, -1):
            prop = self._props.get(type + '_' + '_'.join(t[0:i]))
            if prop:
                return textwrap.dedent(
                    self.__replace_cp_properties(prop, interpolation_dict)).strip()

        # try without the platform (e.g. install)
        if type in self._props:
            return textwrap.dedent(self.__replace_cp_properties(
                self._props[type], interpolation_dict)).strip()

        return None


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

        if 'categories' in config[workload]:
            categories =[i.strip() for i in
                            config[workload]['categories'].split(',')]
        else:
            categories = None

        description = config[workload].get('workload_description')
        if not description:
            description = config[workload].get('description')

        instance = BashCommandBenchmark(
            tool, workload,
            config[workload].get('tool_name'),
            config[workload].get('workload_name'),
            categories,
            description
        )

        for k, v in config.items(workload):
            instance._props[k] = v

        instance.parser = parser

        return instance


