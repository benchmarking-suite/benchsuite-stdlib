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
from benchsuite.core.model.execution import ExecutionEnvironmentRequest, ExecutionEnvironment
from benchsuite.core.model.provider import ServiceProvider
from benchsuite.stdlib.execution.vm_environment import VM, VMSetExecutionEnvironment


class ExistingVMProvider(ServiceProvider):
    """
    This provider is used to execute benchmarks against an already existing VM.
    """

    def __init__(self, name, service_type):
        super().__init__(name, service_type)
        self.ip_address = None
        self.user = None
        self.ssh_private_key = None
        self.platform = None
        self.password = None
        self.vm = None

    def destroy_service(self):
        pass

    def get_execution_environment(self, request: ExecutionEnvironmentRequest) -> ExecutionEnvironment:

        if not self.vm:
            self.vm = VM('existing_vm_'+self.ip_address, self.ip_address, self.user, self.platform, priv_key=self.ssh_private_key, password=self.password)

        return VMSetExecutionEnvironment([self.vm])

    @staticmethod
    def load_from_config_file(config, service_type):
        cp = ExistingVMProvider(config['provider']['name'], service_type)

        vm_config = config[service_type]

        cp.ip_address = vm_config['ip_address']
        cp.user = vm_config['user']
        cp.platform = vm_config['platform']

        if 'ssh_private_key' in vm_config:
            cp.ssh_private_key = vm_config['ssh_private_key']
        elif 'key_path' in vm_config:
            cp.ssh_private_key = open(vm_config['key_path']).read()
        elif 'password' in vm_config:
            cp.password = vm_config['password']

        return cp

