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

import re
import logging

from io import StringIO

import paramiko


#
# def get_data_dir():
#     d = user_data_dir('BenchmarkingSuite', None)
#     if not os.path.exists(d):
#         os.makedirs(d)
#     return d
#
# def get_executions_storage():
#     return get_data_dir() + os.path.sep + 'executions.dat'
#
#
# def get_environments_storage():
#     return get_data_dir() + os.path.sep + 'environments.dat'
from paramiko import RSAKey


logger = logging.getLogger(__name__)

def ssh_transfer_output(vm, name, dest):
    out = '/tmp/' + name + '.out'
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=vm.ip, port=22, username=vm.username, key_filename=vm.keyfile)
        sftp = ssh.open_sftp()
        sftp.get(out, dest)
    finally:
        ssh.close()



def run_ssh_cmd(vm, cmd, async=False, needs_pty=False):
    '''
    
    
    sometime /etc/sudoers is configured to require a tty to execute a command with sudo. In this case, set needs_pty to
    True. But if needs_pty is True, you cannot run a command asyncrounously (check if this is really true)
    
    Defaults    !requiretty

    If aysnc is true, return code is 0 and stdout and stderr are both empty strings. That's because the function
    returns before they are available

    :param vm: 
    :param cmd: 
    :param needs_pty: 
    :return: 
    '''

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if vm.priv_key:
            pkey = RSAKey.from_private_key(StringIO(vm.priv_key))  # assuming it is an RSAKey
            ssh.connect(hostname=vm.ip, port=22, username=vm.username, pkey=pkey)
        else:
            ssh.connect(hostname=vm.ip, port=22, username=vm.username, password=vm.password)

        logger.debug('Executing command on the remote host: "' + cmd+'"')
        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=needs_pty)

        if async:
            return (0, '', '')

        exit_status = stdout.channel.recv_exit_status()

        out = sanitize_output(stdout.read().decode("utf-8"))
        err = sanitize_output(stderr.read().decode("utf-8"))

        return (exit_status, out, err)

        # chan = ssh.get_transport().open_session()
        # chan.get_pty()
        # chan.exec_command(cmd)
        # print(chan.recv(1024))

    finally:
        ssh.close()



def sanitize_output(strin):
    # remove ansi escape sequences
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', strin)
