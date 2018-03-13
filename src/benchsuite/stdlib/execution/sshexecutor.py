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

import os
import logging
import time
import datetime

from benchsuite.stdlib.util.ssh import run_ssh_cmd
from benchsuite.core.model.common import TestExecutor
from benchsuite.core.model.exception import BashCommandExecutionFailedException, NoExecuteCommandsFound
from benchsuite.stdlib.util.timeutils import convert_to_h_m_s

logger = logging.getLogger(__name__)


class RemoteSSHExecutor(TestExecutor):

    def __init__(self, execution):
        self.id = execution.id
        self.test = execution.test
        self.env = execution.exec_env

    def _get_filename(self, phase, type):
        extensions = {
            'cmd_stdout': 'out',
            'cmd_stderr': 'err',
            'cmd_script': 'sh',
            'cmd_wrapper_script': 'wrapper.sh',
            'cmd_lock': 'lock',
            'cmd_time': 'time',
            'cmd_retcode': 'ret'
        }
        return '/tmp/{0}-{1}.{2}'.format(phase, self.id, extensions[type])


    def install(self):
        vm0 = self.env.vms[0]
        cmd = self.test.get_install_script(vm0.platform)
        if cmd:
            self.__execute_cmd(vm0, cmd, 'install')
        else:
            logger.warning('No install commands to execute')

        cmd = self.test.get_postinstall_script(vm0.platform)
        if cmd:
            self.__execute_cmd(vm0, cmd, 'post-install')
        else:
            logger.warning('No Post-install commands to execute')

    def run(self, async=False):
        vm0 = self.env.vms[0]
        cmd = self.test.get_execute_script(vm0.platform)
        if cmd:
            self.__execute_cmd(vm0, cmd, 'run', async=async)
        else:
            logger.error('No execute commands found for this platform ({0})'.format(vm0.platform))
            raise NoExecuteCommandsFound(logger.error('No execute commands found for platform {0}'.format(vm0.platform)))

    def collect_results(self):
        vm0 = self.env.vms[0]
        out = self.__get_cmd_output(vm0, 'cat ' + self._get_filename('run', 'cmd_stdout'))
        err = self.__get_cmd_output(vm0, 'cat ' + self._get_filename('run', 'cmd_stderr'))

        return out, err

    def get_runtime(self, phase):
        vm0 = self.env.vms[0]
        return int(self.__get_cmd_output(vm0, 'cat ' + self._get_filename(phase, 'cmd_time')))

    def cleanup(self):
        vm0 = self.env.vms[0]
        cmd = self.test_scripts.get_remove_script(vm0.platform)
        self.__execute_cmd(vm0, cmd, 'cleanup')

    @staticmethod
    def __get_cmd_output(vm, cmd):
        exit_status, stdout, stderr = run_ssh_cmd(vm, cmd)
        return stdout


    # TODO: at the moment there is no way of controlling poll_for_termination
    # value from the command line or settings/env variables
    def __execute_cmd(self, vm, cmd, phase, async=False, poll_for_termination=True):
        '''

        :param vm:
        :param cmd:
        :param phase:
        :param async: return immediately after the command has been launched
        :param poll_for_termination: if False, wait until the command is finished
        keeping the ssh connection up (that might lead to problems). If True,
        checks periodically if the lock file still exists
        :return: the exit code or 0 if async == True
        '''

        logger.info('Executing commands:\n******************\n{0}\n******************'.format(cmd))
        remote_script = self.__generate_remote_script(vm, cmd, phase)


        # if poll_for_termination, we just launch the command and then check
        # when it is finished by ourself
        exit_status, stdout, stderr = \
            run_ssh_cmd(vm, remote_script, async=poll_for_termination or async)

        if async:
            logger.info('Execution launched. Since async=True return immediately')
            return 0

        if poll_for_termination:
            waited_time = self._wait_for_cmd(vm, phase)

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug('Waited vs. Actual runtime: {0} vs. {1} seconds'.format(
                    int(waited_time.total_seconds()), self.get_runtime(phase)))

        exit_status = int(self.__get_cmd_output(vm, 'cat ' + self._get_filename(phase, 'cmd_retcode')))

        logger.info('Execution exited with status code {0}'.format(exit_status))

        if not exit_status == 0:
            cmd_out = self.__get_cmd_output(vm, 'cat ' + self._get_filename(phase, 'cmd_stdout'))
            cmd_err = self.__get_cmd_output(vm, 'cat ' + self._get_filename(phase, 'cmd_stderr'))

            e = BashCommandExecutionFailedException(
                'command {0} exit with status {1}. The output is: "{2}"'.format(cmd, exit_status, stdout))
            e.cmd = cmd
            e.exit_status = exit_status
            e.stdout = cmd_out
            e.stderr = cmd_err
            raise e

        return exit_status

    def _wait_for_cmd(self, vm, phase):
        t_start = datetime.datetime.now()

        # wait for 5 seconds to be sure that the lock file has been created
        time.sleep(5)

        lock_exists, _, _ = \
            run_ssh_cmd(vm, 'test ! -f ' + self._get_filename(phase, 'cmd_lock'))
        c = 0
        while lock_exists:
            c += 1
            sleep_time = RemoteSSHExecutor.__get_sleeptime(c)
            running_time = datetime.datetime.now() - t_start
            if logger.isEnabledFor(logging.INFO):
                logger.info('Running since {0}. Lock file still exists. '
                            'Waiting for {1} seconds'.format(
                    convert_to_h_m_s(running_time.total_seconds()), sleep_time))
            time.sleep(sleep_time)
            lock_exists, _, _ = \
                run_ssh_cmd(vm, 'test ! -f ' + self._get_filename(phase, 'cmd_lock'))

        return datetime.datetime.now() - t_start

    @staticmethod
    def __get_sleeptime(step):
        if step < 6:
            return 10
        if step < 20:
            return 30
        if step < 70:
            return 60

        return 300

    def __generate_remote_script(self, vm, cmd, phase):

        script = self._get_filename(phase, 'cmd_script')
        script_wrapper = self._get_filename(phase, 'cmd_wrapper_script')
        lock = self._get_filename(phase, 'cmd_lock')
        ret = self._get_filename(phase, 'cmd_retcode')
        out = self._get_filename(phase, 'cmd_stdout')
        err = self._get_filename(phase, 'cmd_stderr')
        runtime = self._get_filename(phase, 'cmd_time')

        working_dir = vm.working_dir + os.path.sep + self.id

        # removes empty lines
        cmd = os.linesep.join([s for s in cmd.splitlines() if s])

        decorated_cmd = '''cat << 'EOF' > {0}
touch {1}
mkdir -p {2}
cd {2}
cat << 'END2' > {3}
set -e
{4}
END2
SECONDS=0
bash -e  {3} 1> {5} 2> {6}
echo $? > {7}
echo $SECONDS > {8}
rm {1}
exit `cat {7}`
EOF
bash {0}'''.format(script_wrapper, lock, working_dir, script, cmd, out,
                   err, ret, runtime)

        decorated_cmd += '\n'

        return decorated_cmd


