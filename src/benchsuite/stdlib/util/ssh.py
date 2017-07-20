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


def run_ssh_cmd(vm, cmd, needs_pty=False):
    '''
    
    
    sometime /etc/sudoers is configured to require a tty to execute a command with sudo. In this case, set needs_pty to
    True. But if needs_pty is True, you cannot run a command asyncrounously
    
    Defaults    !requiretty

    :param vm: 
    :param cmd: 
    :param needs_pty: 
    :return: 
    '''

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if vm.keyfile:
            ssh.connect(hostname=vm.ip, port=22, username=vm.username, key_filename=vm.keyfile)
        else:
            ssh.connect(hostname=vm.ip, port=22, username=vm.username, password=vm.password)

        stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=needs_pty)
        exit_status = stdout.channel.recv_exit_status()

        out = stdout.read().decode("utf-8")
        err = stderr.read().decode("utf-8")
        #print('out: {0}\nerr: {1}\nexit status: {2}'.format(out, err, exit_status))
        return (exit_status, out, err)

        # chan = ssh.get_transport().open_session()
        # chan.get_pty()
        # chan.exec_command(cmd)
        # print(chan.recv(1024))

    finally:
        ssh.close()
