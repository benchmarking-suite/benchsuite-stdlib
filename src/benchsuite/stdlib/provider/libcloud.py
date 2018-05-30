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
import random
import string
import time
from configparser import ConfigParser

from libcloud.compute.providers import get_driver

from benchsuite.core.model.exception import ProviderConfigurationException
from benchsuite.stdlib.util.libcloud_helper import get_helper, guess_platform, \
    guess_username
from benchsuite.stdlib.util.ssh import run_ssh_cmd
from benchsuite.core.model.execution import ExecutionEnvironmentRequest, ExecutionEnvironment
from benchsuite.core.model.provider import ServiceProvider
from benchsuite.stdlib.execution.vm_environment import VMSetExecutionEnvironment, VM

logger = logging.getLogger(__name__)


known_extra_keys = [
    'region',
    'network',
    'security_group',
    'auth_url',
    'auth_version',
    'tenant',
    'new_vm.connection_retry_period',
    'new_vm.connection_retry_times',
    'benchsuite.openstack.no_floating_ip'
]

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
        self.keypair_generated = False
        self.vm_user = None
        self.platform = None
        self.working_dir = None
        self.post_create_script = 'echo "Hello World!"'
        self.vms_pool = []

        # used to cache some values, but not persisted
        self._driver = None
        self._newvm_network = None
        self._newvm_security_group = None
        self._helper = None
        self._sizes = None
        self._images = None



    def __get_helper(self):
        if not self._helper:
            self._helper = get_helper(self.libcloud_type)
        return self._helper

    def __getstate__(self):
        state = self.__dict__.copy()

        # exclude some fields used only for caching
        del state['_driver']
        del state['_newvm_network']
        del state['_newvm_security_group']
        del state['_images']
        del state['_sizes']
        del state['_helper']

        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

        self._driver = None
        self._newvm_network = None
        self._newvm_security_group = None
        self._images = None
        self._sizes = None
        self._helper = None


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

        if self.keypair_generated:
            self.__get_helper().destroy_keypair(driver, self.key_name)

    def __create_vm(self):

        #1. get the driver
        driver = self.__get_libcloud_drv()

        #2. select the correct image and size
        # cache values
        if not self._sizes:
            self._sizes = driver.list_sizes()
        if not self._images:
            self._images = driver.list_images()

        size = [s for s in self._sizes if s.id == self.size or s.name == self.size][0]
        image = [i for i in self._images if i.id == self.image or i.name == self.image][0]

        logger.debug('Creating new Instance with image %s and size %s', image.name, size.name)


        #3. create the node and wait until RUNNING
        rand_name = ''.join(
            [random.choice(string.ascii_lowercase + string.digits) for i in range(6)])

        name = 'benchsuite-'+rand_name

        if not self.key_name or not self.ssh_private_key:
            self.key_name, self.ssh_private_key = self.__get_helper().create_keypair(driver)
            self.keypair_generated = True

        extra_args = self.extra_params.copy()
        extra_args.update(self.__get_newvm_network_param() or {})
        extra_args.update(self.__get_newvm_security_group_param() or {})

        logger.debug('Creating node with:')
        logger.debug(' - name: %s', str(name))
        logger.debug(' - image: %s', str(image.name))
        logger.debug(' - size: %s', str(size.name))
        logger.debug(' - keyname: %s', str(self.key_name))
        logger.debug(' - extra_args: %s', extra_args)
        node = driver.create_node(name=name, image=image, size=size, ex_keyname=self.key_name, **extra_args)
        driver.wait_until_running([node], wait_period=10, ssh_interface='private_ips')

        #4. refresh the info of the node
        node = [i for i in driver.list_nodes() if i.uuid == node.uuid][0]

        logger.debug('New Instance created with node_id=%s', node.id)


        # if the node has not public ips, try to assign one
        if not node.public_ips:
            ip = self.__assign_floating_ip(driver, node)

            if ip:
                node.public_ips = [ip]

        if node.public_ips:
            vm_id = node.public_ips[0]
        else:
            vm_id = node.private_ips[0]


        platform = self.platform
        if not platform:
            platform = guess_platform(image)
            logger.warning('"platform" not specified. Using "%s"', platform)

        username = self.vm_user
        if not username:
            username = guess_username(platform)
            logger.warning('"username" not specified. Using "%s"', username)

        vm = VM(node.id, vm_id, username, platform,
                working_dir=self.working_dir,
                priv_key=self.ssh_private_key)

        vm.set_sizes(
            # OpenStack driver put the number of cpu in the vcpus attribute, the Amazon driver put it in extra['cpu']
            size.vcpus if hasattr(size, 'vcpus') else (size.extra['cpu'] if 'cpu' in size.extra else 0),
            size.ram,
            size.disk)


        # exexute post-creation scripts. This is also used to verify that the VM is accessible
        # through ssh. If the execution fails, we destroy the VM
        try :
            self.__execute_post_create(vm, int(self.extra_params.get('new_vm.connection_retry_times', 20)))
            logger.info('New VM %s created and initialized', vm)

        except Exception as ex:
            logger.error('{0} occurred during VM initialization: {1}'.format(
                ex.__class__.__name__, str(ex)))
            logger.error('Destroying VM due to the initialization errors')

            # destroying the node created
            node.destroy()
            raise ex

        return vm


    def __assign_floating_ip(self, driver, node):

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
                period = self.extra_params.get('new_vm.connection_retry_period', 30)
                logger.warning('Error connecting ({0}). The instance could be not ready yet. '
                               'Waiting {2} seconds and retry for {1} times'.format(str(ex), retries, period))
                time.sleep(int(period))
                self.__execute_post_create(vm,retries)
            else:
                logger.warning('Error connecting ({0}). Max number of retries achieved. Raising the exception'.format(str(ex)))
                raise ex

    def get_provder_properties_dict(self):
        return {
            'id': self.name,
            'size': self.size,
            'image': self.image,
            'service_type': self.service_type
        }

    def __get_libcloud_drv(self):

        if not self._driver:  # caches the driver in the self._driver variable
            self._driver = self.__get_helper().get_driver(self.access_id, self.secret_key, self.extra_params)

        return self._driver


    def __get_newvm_network_param(self):

        if not self._newvm_network:
            self._newvm_network = self.__get_helper().get_network(
                    self.__get_libcloud_drv(), self.extra_params.get('network'))

        return self._newvm_network

    def __get_newvm_security_group_param(self):

        if not self._newvm_security_group:
                self._newvm_security_group = self.__get_helper().get_security_group(
                    self.__get_libcloud_drv(),
                    self.extra_params.get('security_group'))

        return self._newvm_security_group


    @staticmethod
    def __load_extra_params(config):

        # start with default values
        extra_params = {}
        extra_params['tenant'] = config['provider']['access_id']

        for k, v in config['provider'].items():
            if k in known_extra_keys or k.startswith('ex_'):
                if v:
                    extra_params[k] = v

        logger.debug('Loaded following extra parameters: ' + str(extra_params))

        # continue to support old format (with libcloud extra parameter in their own section)
        if 'libcloud_extra_params' in config:
            extra_params.update(config['libcloud_extra_params'])

        # map some parames to the Openstack drvier parameters
        if 'auth_url' in extra_params and not 'ex_force_auth_url' in extra_params:
            extra_params['ex_force_auth_url'] = extra_params['auth_url']

        if 'auth_version' in extra_params and not 'ex_force_auth_version' in extra_params:
            extra_params['ex_force_auth_version'] = extra_params['auth_version']

        if 'region' in extra_params and not 'ex_force_service_region' in extra_params:
            extra_params['ex_force_service_region'] = extra_params['region']

        if 'tenant' in extra_params and not 'ex_tenant_name' in extra_params:
            extra_params['ex_tenant_name'] = extra_params['tenant']

        # sanitize auth url parameter. If it ends with "/" libcloud does not behave correctly
        if 'ex_force_auth_url' in extra_params:
            extra_params['ex_force_auth_url'] = \
                extra_params['ex_force_auth_url'].rstrip('/')
        if 'auth_url' in extra_params:
            extra_params['auth_url'] = extra_params['auth_url'].rstrip('/')

        return extra_params


    def getdriver(self):
        return self.__get_libcloud_drv()

    @staticmethod
    def load_from_config_file(config: ConfigParser, service_type: str) -> ServiceProvider:


        assert 'provider' in config, '"provider" section is mandatory in the configuration'
        assert 'name' in config['provider'], '"name" parameter is mandatory in the configuration'
        assert 'driver' in config['provider'], '"driver" parameter is mandatory in the configuration'
        assert 'access_id' in config['provider'], '"access_id" parameter is mandatory in the configuration'
        assert 'secret_key' in config['provider'], '"secret_key" parameter is mandatory in the configuration'

        cp = LibcloudComputeProvider(
            config['provider']['name'],
            service_type,
            config['provider']['driver'],
            config['provider']['access_id'],
            config['provider']['secret_key']
        )

        cp.extra_params = LibcloudComputeProvider.__load_extra_params(config)


        if service_type not in config:
            raise ProviderConfigurationException(
                'Service Type "{0}" does not exist in the configuration'.format(service_type))

        cloud_service_config = config[service_type]

        cp.image = cloud_service_config['image']
        cp.size = cloud_service_config['size']
        cp.vm_user = cloud_service_config.get('vm_user')
        cp.working_dir = '/tmp' if not cp.vm_user else '/home/' + cp.vm_user
        cp.platform = cloud_service_config.get('platform')


        if 'key_name' in cloud_service_config:
            cp.key_name = cloud_service_config['key_name']

        if cp.key_name:
            if 'ssh_private_key' in cloud_service_config:
                cp.ssh_private_key = cloud_service_config['ssh_private_key']
            if 'key_path' in cloud_service_config:
                cp.ssh_private_key = open(cloud_service_config['key_path']).read()

        if 'working_dir' in cloud_service_config:
            cp.working_dir = cloud_service_config['working_dir']

        if 'post_create_script' in cloud_service_config:
            cp.post_create_script = cloud_service_config['post_create_script']

        return cp
