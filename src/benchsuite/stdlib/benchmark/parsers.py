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
import json
import logging

import re

from benchsuite.core.model.execution import ExecutionResultParser


logger = logging.getLogger(__name__)



class WebFrameworksBenchmarksParser(ExecutionResultParser):

    def get_metrics(self, tool, workload, logs):

        stdout = logs[0]['stdout']

        # the tool puts the results in the results.json file. This file is
        # printed in the stdout and delimited by the
        # "@@@ results.json content @@@" and "@@@@@@" lines. We isolate the
        # content of the file and parse it in a json object
        lines = stdout.split('\n')
        start = lines.index('@@@ results.json content @@@') + 2
        end = lines.index('@@@@@@')
        results_str = '\n'.join(lines[start:end])
        results = json.loads(results_str)

        # find the framework and the test executed
        framework = results['frameworks'][0]
        test = list(results['verify'][framework].keys())[0]

        data = results['rawData'][test][framework]
        iterations = results['concurrencyLevels']

        if test == 'update' or test == 'query':
            iterations = results['queryIntervals']

        if test == 'plaintext':
            iterations = results['pipelineConcurrencyLevels']

        metrics = {}
        c = 0
        for res in data:
            iter = iterations[c]
            metrics.update({'totalRequests_{0}'.format(iter): {'value': res['totalRequests'], 'unit':'num'}})
            if 'timeout' in res:
                metrics.update({'timeout_{0}'.format(iter): {'value': res['timeout'], 'unit':'num'}})
            metrics.update({'duration_{0}'.format(iter): {'value': res['endTime'] - res['startTime'], 'unit':'s'}})
            metrics.update({'latencyAvg_{0}'.format(iter): self.__split_value_unit(res['latencyAvg'])})
            metrics.update({'latencyMax_{0}'.format(iter): self.__split_value_unit(res['latencyMax'])})
            metrics.update({'latencyStdev_{0}'.format(iter): self.__split_value_unit(res['latencyStdev'])})
            c+=1

        return metrics


    def __split_value_unit(self, s):
        '''
        values are stored in results.json as string that contain both the value and the unit
        (e.g. "10.23ms", "4.2s", "3.8us")
        :param s: the result string
        :return:
        '''
        val = re.findall(r"\d*\.\d+|\d+", s)[0]
        unit = s.replace(val,'').strip()
        return {'value': val, 'unit': unit}


class YCSBResultParser(ExecutionResultParser):

    def get_metrics(self, tool, workload, logs):

        #
        # Metrics in the YCSB outputs appears in this format:
        # [<operation_type>], <metrics>, <value>
        # e.g.
        # [INSERT], MaxLatency(us), 14423.0
        # [SCAN], Operations, 4748.0

        stdout = logs[0]['stdout']

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

        # keep only interesting metrics, do some sanitization of names
        out = {
            'ops_throughput': {'value': float(parsed_metrics['overall']['Throughput(ops/sec)']), 'unit': 'ops/s'}
        }

        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'insert'))
        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'read'))
        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'update'))
        out.update(self.__get_metrics_by_operation_type(parsed_metrics, 'scan'))

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

    def get_metrics(self, tool, workload, logs):
        '''
        see https://github.com/filebench/filebench/wiki/Collected-metrics
        :param stdout: 
        :param stderr: 
        :return: 
        '''

        stdout = logs[0]['stdout']
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
            'latency_avg': {'value': float(latency), 'unit': 'ms'}
        }


class DaCapoResultParser(ExecutionResultParser):

    def get_metrics(self, tool, workload, logs):
        """
        DaCapo benchmark works executing a variable number of warmup iterations
        until the completion time converge (a variance <= 3% in the latest 3
        iterations).

        Two metrics are collected:
        1) "timed_duration": the duration of the latest run
        2) "warmup_iters": the number of iterations required to converge

        :param stdout:
        :param stderr:
        :return:
        """

        stderr = logs[0]['stderr']
        lines = stderr.split('\n')

        # timed duration is the only the one in the "PASSED" line
        passed = [l for l in lines if 'PASSED' in l][0]
        # time is the only number in the line
        timed_duration = [n for n in passed.split() if n.isdigit()][0]

        # there is a line with "completed warmup" for each warmup executed
        warmup_iters = len([l for l in lines if 'completed warmup' in l])

        return {
            'timed_duration': {'value': int(timed_duration), 'unit': 'ms'},
            'warmup_iters': {'value': int(warmup_iters), 'unit': 'num'}
        }

class SysbenchResultParser(ExecutionResultParser):

    start_pattern = re.compile("^###([a-zA-Z]+)###([0-9]+)###$")

    cpu_metrics_patterns = {
        'events_rate': (re.compile("^.*events per second:(.*)$"), 'num/s'),
        'total_time':  (re.compile("^.*total time:(.*)s$"), 's'),
        'latency_min': (re.compile("^.*min:(.*)$"), 'ms'),
        'latency_max': (re.compile("^.*max:(.*)$"), 'ms'),
        'latency_avg': (re.compile("^.*avg:(.*)$"), 'ms'),
        'latency_95':  (re.compile("^.*95th percentile:(.*)$"), 'ms')
    }

    def get_metrics(self, tool, workload, logs):
        """
        https://wiki.gentoo.org/wiki/Sysbench

        """
        stdout = [e for e in logs if e['vm'] == 'default'][0]['stdout']
        lines = stdout.split('\n')

        # detect the different tool executions
        execs_out = []
        istart = iend = 0
        while istart < len(lines):
            match = self.start_pattern.match(lines[istart])
            if match:
                iend = istart
                while iend < len(lines):
                    if lines[iend] == '###END###':
                        execs_out.append((match.group(1), int(match.group(2)), istart, iend))
                        istart = iend
                        break
                    iend+=1
            istart+=1

        res = {}
        for exec in execs_out:
            if exec[0] == 'cpu':
                res.update(self.get_cpu_metrics(lines[exec[2]:exec[3]+1], exec[1]))

        return res


    def get_cpu_metrics(self, output, n_threads):
        res = {}

        for l in output:
            for k,v in self.cpu_metrics_patterns.items():
                pattern, unit = v
                m = pattern.match(l)
                if(m):
                    res['{0}_{1}'.format(k, n_threads)] = {'value':float(m.group(1).strip()), 'unit': unit}

        return res



class IPerfResultParser(ExecutionResultParser):

    def get_metrics(self, tool, workload, logs):

        stdout = [e for e in logs if e['vm'] == 'default'][0]['stdout']


        if 'udp' in workload:
            return self.__get_udp_metrics(stdout)
        else:
            return self.__get_tcp_metrics(stdout)

    def __get_tcp_metrics(self, stdout):

        res = {}
        lines = stdout.split("\n")
        data = [l.split(',') for l in lines if len(l.split(',')) == 9]

        c = 1
        for i in range(0, len(data) -1) if len(data) > 1 else range(0,1):
            res['transferred_'+str(c)] = {'value': int(data[i][7]), 'unit': 'bytes'}
            res['bandwidth_'+str(c)] = {'value': int(data[i][8]), 'unit': 'bit/s'}
            c+=1

        if len(data) > 1:
            res['transferred_sum'] =  {'value': int(data[c-1][7]), 'unit': 'bytes'}
            res['bandwidth_sum'] =    {'value': int(data[c-1][8]), 'unit': 'bit/s'}

        return res

    def __get_udp_metrics(self, stdout):

        res = {}
        lines = stdout.split("\n")
        data = [l.split(',') for l in lines if len(l.split(',')) == 14]

        c = 1
        for i in data:
            res['transferred_'+str(c)] = {'value': int(i[7]), 'unit': 'bytes'}
            res['bandwidth_'+str(c)] =    {'value': int(i[8]), 'unit': 'bit/s'}
            res['total_datagrams_'+str(c)] = {'value': int(i[11]), 'unit': 'num'}
            res['lost_datagrams'+str(c)] = {'value': int(i[10]), 'unit': 'num'}
            res['jitter_'+str(c)] = {'value': i[9], 'unit': 'ms'}
            res['outoforder_'+str(c)] = {'value': int(i[13]), 'unit': 'num'}
            c+=1

        tavg = sum([int(x[7]) for x in data]) / len(data)
        bavg = sum([int(x[8]) for x in data]) / len(data)
        davg = sum([int(x[11]) for x in data]) / len(data)
        lavg = sum([int(x[10]) for x in data]) / len(data)
        javg = sum([float(x[9]) for x in data]) / len(data)
        oavg = sum([int(x[13]) for x in data]) / len(data)
        res['transferred_avg'] = {'value': tavg, 'unit': 'bytes'}
        res['bandwidth_avg'] =  {'value': bavg, 'unit': 'bit/s'}
        res['total_datagrams_avg'] =  {'value': davg, 'unit': 'num'}
        res['lost_datagrams_avg'] =  {'value': lavg, 'unit': 'num'}
        res['jitter_avg'] =  {'value': javg, 'unit': 'ms'}
        res['outoforder_avg'] =  {'value': oavg, 'unit': 'num'}

        return res