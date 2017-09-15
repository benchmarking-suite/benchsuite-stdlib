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

import re

from benchsuite.core.model.execution import ExecutionResultParser


logger = logging.getLogger(__name__)



class FileBenchResultParser(ExecutionResultParser):

    def get_metrics(self, stdout, stderr):
        '''
        see https://github.com/filebench/filebench/wiki/Collected-metrics
        :param stdout: 
        :param stderr: 
        :return: 
        '''

        # isolate the line with the IO Summary
        lines = stdout.split('\n')
        summary_line = [l for l in lines if 'IO Summary' in l][0]
        logger.debug('Extracted IO Summary: %s', summary_line)

        # isolate metrics
        metrics = re.sub(r'^.*IO Summary:', '', summary_line).split(',')

        # extract metrics
        n_ops = re.sub(r'ops', '', metrics[0]).strip()
        logger.debug('ops: %s', n_ops)

        ops_s = re.sub(r'ops/s', '', metrics[1]).strip()
        logger.debug('ops/s: %s', ops_s)

        throughput = re.sub(r'mb/s','', metrics[3]).strip()
        logger.debug('throughput (mb/s): %s', throughput)

        speed = re.sub(r'us\ cpu/op', '', metrics[4]).strip()
        logger.debug('cpu time (us cpu/s): %s', speed)

        latency = re.sub(r'ms\ latency', '', metrics[5]).strip()
        logger.debug('latency (ms): %s', latency)

        return {
            'n_ops': n_ops,
            'ops/s': ops_s,
            'throuput': throughput,
            'cpu_time': speed,
            'latency': latency
        }