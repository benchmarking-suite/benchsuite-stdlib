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

from benchsuite.core.model.exception import ProviderConfigurationException

logger = logging.getLogger(__name__)


def get_openstack_network(driver, requested_network):

    all_networks = driver.ex_list_networks()

    selected_networks = [n for n in all_networks
               if n.name == requested_network or n.id == requested_network]

    if not selected_networks:
        raise ProviderConfigurationException('The requested network "{0}" does not exist'.format(requested_network))

    if len(selected_networks) > 1:
        logger.warning('Multiple networks matches the requested network. Selecting the first one')

    return {'networks': [selected_networks[0]]}


def get_openstack_security_group(driver, requested_security_group):

    all_security_groups = driver.ex_list_security_groups()

    selected_security_groups = [s for s in all_security_groups
                if s.name == requested_security_group or s.id == requested_security_group]

    if not selected_security_groups:
        raise ProviderConfigurationException('The requested security group "{0}" does not exist'.format(requested_security_group))

    if len(selected_security_groups) > 1:
        logger.warning('Multiple security groups matches the requested security group. Selecting the frist one')

    return {'ex_security_groups': [selected_security_groups[0]]}


def get_ec2_network(driver, requested_network):

    all_networks = driver.ex_list_subnets()

    selected_networks = [n for n in all_networks
               if n.name == requested_network or n.id == requested_network]

    if not selected_networks:
        raise ProviderConfigurationException('The requested network "{0}" does not exist'.format(requested_network))

    if len(selected_networks) > 1:
        logger.warning('Multiple networks matches the requested network. Selecting the first one')

    return {'ex_subnet': selected_networks[0]}


def get_ec2_security_group(driver, requested_security_group):

    all_security_groups = driver.ex_get_security_groups()

    selected_security_groups = [s for s in all_security_groups
                if s.name == requested_security_group or s.id == requested_security_group]

    if not selected_security_groups:
        raise ProviderConfigurationException('The requested security group "{0}" does not exist'.format(requested_security_group))

    if len(selected_security_groups) > 1:
        logger.warning('Multiple security groups matches the requested security group. Selecting the frist one')

    return {'ex_security_group_ids': selected_security_groups[0].id}

