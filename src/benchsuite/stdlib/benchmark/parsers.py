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


class YCSBResultParser(ExecutionResultParser):

    def get_metrics(self, stdout, stderr):

        #
        # Metrics in the YCSB outputs appears in this format:
        # [<operation_type>], <metrics>, <value>
        # e.g.
        # [INSERT], MaxLatency(us), 14423.0
        # [SCAN], Operations, 4748.0


        lines = stdout.split('\n')

        # filter-out all the non-metrics lines
        metrics_lines = [l for l in lines if l.startswith('[')]

        # parse all the metrics from the output
        parsed_metrics = {}
        for l in metrics_lines:
            m = re.search('^\[(.+)\],\ (.+),\ (.+)$', l)
            op_type = m.group(1).lower()
            op_met = m.group(2)
            met_val = m.group(3)

            if op_type not in parsed_metrics:
                parsed_metrics[op_type] = {}

            parsed_metrics[op_type][op_met] = met_val


        #keep only interesting metrics, do some sanitization of names
        out = {
            'ops_throughput': {'value': parsed_metrics['overall']['Throughput(ops/sec)'], 'unit': 'ops/s'}
        }

        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'insert'))
        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'read'))
        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'update'))


        return out


    def __get_metrics_by_operation_type(self, parsed_metrics, op_type):

        if op_type not in parsed_metrics:
            return {}

        return {
            op_type+'_ops': {'value': int(float(parsed_metrics[op_type]['Operations'])), 'unit': 'num'},
            op_type+'_latency_avg': {'value': float(parsed_metrics[op_type]['AverageLatency(us)']), 'unit': 'us'},
            op_type+'_latency_min': {'value': float(parsed_metrics[op_type]['MinLatency(us)']), 'unit': 'us'},
            op_type+'_latency_max': {'value': float(parsed_metrics[op_type]['MaxLatency(us)']), 'unit': 'us'},
            op_type+'_latency_95': {'value': float(parsed_metrics[op_type]['95thPercentileLatency(us)']), 'unit': 'us'},
            op_type+'_latency_99': {'value': float(parsed_metrics[op_type]['99thPercentileLatency(us)']), 'unit': 'us'}
        }

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
            'ops': {'value': int(float(n_ops)), 'unit': 'num'},
            'ops_throughput': {'value': float(ops_s), 'unit': 'ops/s'},
            'throughput': {'value': float(throughput), 'unit': 'mb/s'},
            'cputime': {'value': float(speed), 'unit': 'us cpu/s'},
            'latency_avg': {'value': float(latency), 'unit': 'us'}
        }