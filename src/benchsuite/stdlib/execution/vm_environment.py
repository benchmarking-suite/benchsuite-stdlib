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

    def __init__(self, id, ip, username, platform, working_dir=None, keyfile=None, password=None):
        self.ip = ip
        self.id = id
        self.username = username
        self.keyfile = keyfile
        self.platform = platform
        self.password = password
        self.working_dir = working_dir or '/home/' + self.username

    def __str__(self) -> str:
        return "VM[ip: {0}]".format(self.ip)


class VMSetExecutionEnvironment(ExecutionEnvironment):

    def __init__(self, vms: List[VM]):
        super().__init__()
        self.vms = vms

    def __str__(self) -> str:

        return 'Execution Environment[' + ', '.join([str(v) for v in self.vms]) + ']'

class VMSetExecutionEnvironmentRequest(ExecutionEnvironmentRequest):

    def __init__(self, n_vms):
        self.n_vms = n_vms