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

from typing import List

from benchsuite.core.model.execution import ExecutionEnvironment, ExecutionEnvironmentRequest


class VM:

    def __init__(self, id, ip, username, platform, working_dir=None, priv_key=None, password=None):
        self.ip = ip
        self.id = id
        self.username = username
        self.priv_key = priv_key
        self.platform = platform
        self.password = password
        self.working_dir = working_dir or '/home/' + self.username
        self.cpu = 0
        self.memory = 0
        self.disk = 0

    def set_sizes(self, cpu, memory, disk):
        self.cpu = cpu
        self.memory = memory
        self.disk = disk

    def __str__(self) -> str:
        return "VM[ip: {0}]".format(self.ip)


class VMSetExecutionEnvironment(ExecutionEnvironment):

    def __init__(self, vms: List[VM]):
        super().__init__()
        self.vms = vms

    def get_specs_dict(self):
        res = {}
        res['type'] = 'VMSet'
        res['vms'] = []
        for v in self.vms:
            d = {}

            if v.cpu:
                d['cpu'] = v.cpu
            if v.memory:
                d['memory'] = v.memory
            if v.disk:
                d['disk'] = v.disk
            if v.platform:
                d['platform']= v.platform

            res['vms'].append(d)

        return res

    def __str__(self) -> str:
        return 'Execution Environment[' + ', '.join([str(v) for v in self.vms]) + ']'

class VMSetExecutionEnvironmentRequest(ExecutionEnvironmentRequest):

    def __init__(self, n_vms):
        self.n_vms = n_vms