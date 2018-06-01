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
import sys

from benchsuite.core.model.execution import ExecutionEnvironmentRequest
from benchsuite.stdlib.provider.libcloud import LibcloudComputeProvider

if __name__ == '__main__':

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    config = {
        'provider': {
            'name': 'MyTestingProvider',
            'driver': 'openstack',
            'access_id': 'gabriele.giammatteo@eng.it',
            'secret_key': '9fnvF5cHX2uC',
            'auth_url': 'http://130.206.84.8:4730',
            'auth_version': '2.0_password',
            'tenant': 'cloudperfect testbed',
            'region': 'Vicenza',
        },

        'service1': {
            'image': 'base_ubuntu_14.04',
            'size': 'm1.medium',
            #'vm_user': 'ubuntu',
            #'platform': 'ubuntu_14'
        }
    }


    config_ote = {
        'provider': {
            'name': 'MyTestingProvider2',
            'driver': 'openstack',
            'access_id': 'demo',
            'secret_key': 'cloudp_demo',
            'auth_url': 'http://10.0.16.11:5000/',
            'network': 'selfservice',
            #'tenant': 'pippo'
        },

        'service1': {
            'image': 'ubuntu-14-server',
            'size': 'm1.medium',
            #'vm_user': 'ubuntu',
            #'platform': 'ubuntu_14'
        }
    }

    config_ulm = {
        'provider': {
            'name': 'MyTestingProvider3',
            'driver': 'openstack',
            'access_id': 'giammatteo',
            'secret_key': 'EphaeKah5iveesaech7A',
            'auth_url': 'https://omistack.e-technik.uni-ulm.de:5000/',
            'tenant': 'cloudperfect-testing',
            'network': 'shared-private-net'
        },

        'service1': {
            'image': 'Ubuntu Server 14.04.2 AMD64 LTS',
            'size': 'medium',
            #'vm_user': 'ubuntu',
            #'platform': 'ubuntu_14'
        }
    }


    config_ec2 = {
        'provider': {
            'name': 'MyTestingProvider3',
            'driver': 'ec2',
            'access_id': 'AKIAJ23QA2D52FVO4IBA',
            'secret_key': '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',
            'region': 'us-west-1'
        },

        'service1': {
            'image': 'ami-b2527ad2',
            'size': 't2.micro',
            #'vm_user': 'ubuntu',
            #'platform': 'ubuntu_14'
        }
    }


    prov = LibcloudComputeProvider.load_from_config_file(config_ulm, 'service1')
    req = ExecutionEnvironmentRequest()
    req.n_vms = 1
    prov.get_execution_environment(req)