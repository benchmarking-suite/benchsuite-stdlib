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
import time
from configparser import ConfigParser

from libcloud.compute.drivers.ec2 import EC2NetworkSubnet
from libcloud.compute.providers import get_driver
from os import read

from benchsuite.core.model.exception import ProviderConfigurationException
from benchsuite.stdlib.util.ssh import run_ssh_cmd
from benchsuite.core.model.execution import ExecutionEnvironmentRequest, ExecutionEnvironment
from benchsuite.core.model.provider import ServiceProvider
from benchsuite.stdlib.execution.vm_environment import VMSetExecutionEnvironment, VM

logger = logging.getLogger(__name__)


class LibcloudComputeProvider(ServiceProvider):

    def __init__(self, name, service_type, driver, access_id, secret_key):
        super().__init__(name, service_type)
        self.libcloud_type = driver
        self.access_id = access_id
        self.secret_key = secret_key
        self.extra_params = None
        self.image = None
        self.size = None
        self.key_name = None
        self.ssh_private_key = None
        self.vm_user = None
        self.platform = None
        self.working_dir = None
        self.post_create_script = 'echo "Hello World!"'
        self.vms_pool = []


    def get_execution_environment(self, request: ExecutionEnvironmentRequest) -> ExecutionEnvironment:
        if len(self.vms_pool) < request.n_vms:
            for i in range(request.n_vms - len(self.vms_pool)):
                self.vms_pool.append(self.__create_vm())

        return VMSetExecutionEnvironment(self.vms_pool[:request.n_vms])

    def destroy_service(self):
        driver = self.__get_libcloud_drv()
        nodes_id = [v.id for v in self.vms_pool]
        to_delete = [n for n in driver.list_nodes() if n.id in nodes_id]
        logger.info('{0} nodes to delete'.format(len(to_delete)))
        for n in to_delete:
            logger.info('Deleting node ' + n.id)
            n.destroy()

    def __get_libcloud_drv(self):
        drv = get_driver(self.libcloud_type)
        driver = drv(self.access_id, self.secret_key, **self.extra_params)
        return driver

    def __create_vm(self):

        #1. get the driver
        driver = self.__get_libcloud_drv()

        #2. select the correct image and size
        sizes = driver.list_sizes()
        images = driver.list_images()
        size = [s for s in sizes if s.id == self.size or s.name == self.size][0]
        image = [i for i in images if i.id == self.image or i.name == self.image][0]

        logger.debug('Creating new Instance with image %s and size %s', image.name, size.name)

        self.set_up_network_params()


        #3. create the node and wait until RUNNING
        node = driver.create_node(name='benchsuite-node', image=image, size=size, ex_keyname=self.key_name, **self.extra_params)
        driver.wait_until_running([node], wait_period=10)

        #4. refresh the info of the node
        node = [i for i in driver.list_nodes() if i.uuid == node.uuid][0]

        logger.debug('New Instance created with node_id=%s', node.id)


        # if the node has not public ips, try to assign one
        if not node.public_ips:
            ip = self.assign_floating_ip(driver, node)

            if ip:
                node.public_ips = [ip]

        if node.public_ips:
            vm_id = node.public_ips[0]
        else:
            vm_id = node.private_ips[0]

        vm = VM(node.id, vm_id, self.vm_user, self.platform, working_dir=self.working_dir, priv_key=self.ssh_private_key)

        vm.set_sizes(
            # OpenStack driver put the number of cpu in the vcpus attribute, the Amazon driver put it in extra['cpu']
            size.vcpus if hasattr(size, 'vcpus') else (size.extra['cpu'] if 'cpu' in size.extra else 0),
            size.ram,
            size.disk)

        self.__execute_post_create(vm, 5)
        logger.info('New VM %s created and initialized', vm)

        return vm

    def set_up_network_params(self):

        driver = self.__get_libcloud_drv()

        if self.libcloud_type == 'openstack':

            networks = driver.ex_list_networks()
            network = None

            if 'network' in self.extra_params:
                network = [n for n in networks if n.name == self.extra_params['network'] or n.id == self.extra_params['network']]
                if network:
                     logger.debug('Using network {0} as specified in the configuration'.format(network))
                else:
                    logger.error('The network {0} specified in the configuration does not exist.')
            else:
                if len(networks) == 1:
                    network = networks
                    logger.info('Automatically selecting the only existing network: {0}'.format(network[0]))

            if network:
                self.extra_params['networks'] = network
            else:
                logger.warning('Failed to configure the network. The creation of instances could fail')

            return

        if self.libcloud_type == 'ec2':

            networks = driver.ex_list_subnets()
            network = None


            # TODO: re-use the same code used above

            if 'network' in self.extra_params:
                network = [n for n in networks if n.name == self.extra_params['network'] or n.id == self.extra_params['network']]
                if network:
                    logger.debug('Using network {0} as specified in the configuration'.format(network))
                else:
                    logger.error('The network {0} specified in the configuration does not exist.')
            else:
                if len(networks) == 1:
                    network = networks
                    logger.info('Automatically selecting the only existing network: {0}'.format(network[0]))

            if network:
                self.extra_params['ex_subnet'] = network[0] # this changes wrt openstack. Here only one network is accepted
            else:
                logger.warning('Failed to configure the network. The creation of instances could fail')


            sec_groups = driver.ex_get_security_groups()
            sec_group = None

            if 'security_group' in self.extra_params:
                sec_group = [s for s in sec_groups if s.name == self.extra_params['security_group'] or s.id == self.extra_params['security_group']]
                if sec_group:
                    logger.debug('Using the security group {0} as specified in the configuration'.format(sec_group))
                else:
                    logger.error('The security group {0} specified in the configuration does not exist.')
            else:
                if len(sec_groups) == 1:
                    sec_group = sec_groups[0]
                    logger.info('Automatically selecting the only existing security group: {0}'.format(sec_group))

            if sec_group:
                self.extra_params['ex_security_group_ids'] = [sec_group.id]
            else:
                logger.warning('Failed to configure the security group. The creation of instances could fail')

            return



    def assign_floating_ip(self, driver, node):

        if not self.libcloud_type == 'openstack':
            # supported only by openstack driver
            logger.debug('Public IP assignment only supported for Openstack.')
            return

        if 'benchsuite.openstack.no_floating_ip' in self.extra_params and \
            self.extra_params['benchsuite.openstack.no_floating_ip'] == 'true':
            # explicitly skip the floating ip assignment
            logger.debug('Public IP assigment will be skipped because '
                         'benchsuite.openstack.no_floating_ip is set to true')
            return

        p_ip = self.__get_available_public_ip(driver)

        if p_ip:
            logger.debug('Trying to assign the public ip %s to the new instance', p_ip)
            driver.ex_attach_floating_ip_to_node(node, p_ip)
            return p_ip.ip_address
        else:
            logger.error('No floating public IPs available! Cannot assign a public ip to the instance')

    def __get_available_public_ip(self, driver):
        public_ips = driver.ex_list_floating_ips()

        if public_ips:
            av = [i for i in public_ips if not i.node_id]
            if av:
                return av[0]
        return None

    def __execute_post_create(self, vm, retries):
        logger.info('Trying to connect to the new instance (max_retries={0})'.format(retries))
        try:
            run_ssh_cmd(vm, self.post_create_script, needs_pty=True)
        except Exception as ex:
            retries -= 1

            if retries > 0:
                logger.warning('Error connecting ({0}). The instance could be not ready yet. '
                               'Waiting 10 seconds and retry for {1} times'.format(str(ex), retries))
                time.sleep(10)
                self.__execute_post_create(vm,retries)
            else:
                logger.warning('Error connecting ({0}). Max number of retries achived. Raising the exception'.format(str(ex)))
                raise ex

    def get_provder_properties_dict(self):
        return {
            'id': self.name,
            'size': self.size,
            'image': self.image,
            'service_type': self.service_type
        }

    @staticmethod
    def load_from_config_file(config: ConfigParser, service_type: str) -> ServiceProvider:

        cp = LibcloudComputeProvider(
            config['provider']['name'],
            service_type,
            config['provider']['driver'],
            config['provider']['access_id'],
            config['provider']['secret_key']
        )

        libcloud_additional_params = {}

        # consider all remaining properties in the [provider] section as libcloud extra params
        for k, v in config['provider'].items():
            if k not in ['name', 'driver', 'access_id', 'secret_key']:
                libcloud_additional_params[k] = v

        # continue to support old format (with libcloud extra parameter in their own section)
        if 'libcloud_extra_params' in config:
            for k in config['libcloud_extra_params']:
                libcloud_additional_params[k] = config['libcloud_extra_params'][k]


        # sanitize auth url parameter. If it ends with "/" libcloud does not behave correctly
        if 'ex_force_auth_url' in libcloud_additional_params:
            libcloud_additional_params['ex_force_auth_url'] = \
                libcloud_additional_params['ex_force_auth_url'].rstrip('/')


        cp.extra_params = libcloud_additional_params

        if service_type not in config:
            raise ProviderConfigurationException(
                'Service Type "{0}" does not exist in the configuration'.format(service_type))

        cloud_service_config = config[service_type]

        cp.image = cloud_service_config['image']
        cp.size = cloud_service_config['size']
        cp.key_name = cloud_service_config['key_name']
        cp.vm_user = cloud_service_config['vm_user']
        cp.working_dir = '/home/' + cloud_service_config['vm_user'] # default value
        cp.platform = cloud_service_config['platform']

        if 'ssh_private_key' in cloud_service_config:
            cp.ssh_private_key = cloud_service_config['ssh_private_key']
        else:
            cp.ssh_private_key = open(cloud_service_config['key_path']).read()


        if 'working_dir' in cloud_service_config:
            cp.working_dir = cloud_service_config['working_dir']

        if 'post_create_script' in cloud_service_config:
            cp.post_create_script = cloud_service_config['post_create_script']

        return cp
