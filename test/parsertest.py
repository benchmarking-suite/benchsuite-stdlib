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

import sys

from benchsuite.stdlib.benchmark.parsers import FileBenchResultParser, YCSBResultParser

YCSB_OUT_1 = '''
Adding shard node URL: jdbc:mysql://127.0.0.1:3306/benchmark
Using shards: 1, batchSize:-1, fetchSize: -1
[OVERALL], RunTime(ms), 3221.0
[OVERALL], Throughput(ops/sec), 310.4625892579944
[TOTAL_GCS_MarkSweepCompact], Count, 0.0
[TOTAL_GC_TIME_MarkSweepCompact], Time(ms), 0.0
[TOTAL_GC_TIME_%_MarkSweepCompact], Time(%), 0.0
[TOTAL_GCS_Copy], Count, 1.0
[TOTAL_GC_TIME_Copy], Time(ms), 6.0
[TOTAL_GC_TIME_%_Copy], Time(%), 0.18627755355479667
[TOTAL_GCs], Count, 1.0
[TOTAL_GC_TIME], Time(ms), 6.0
[TOTAL_GC_TIME_%], Time(%), 0.18627755355479667
[CLEANUP], Operations, 1.0
[CLEANUP], AverageLatency(us), 987.0
[CLEANUP], MinLatency(us), 987.0
[CLEANUP], MaxLatency(us), 987.0
[CLEANUP], 95thPercentileLatency(us), 987.0
[CLEANUP], 99thPercentileLatency(us), 987.0
[READ], Operations, 509.0
[READ], AverageLatency(us), 316.64636542239685
[READ], MinLatency(us), 200.0
[READ], MaxLatency(us), 3645.0
[READ], 95thPercentileLatency(us), 429.0
[READ], 99thPercentileLatency(us), 1496.0
[READ], Return=OK, 509
[UPDATE], Operations, 491.0
[UPDATE], AverageLatency(us), 5505.596741344196
[UPDATE], MinLatency(us), 2256.0
[UPDATE], MaxLatency(us), 19263.0
[UPDATE], 95thPercentileLatency(us), 6439.0
[UPDATE], 99thPercentileLatency(us), 9095.0
[UPDATE], Return=OK, 491
'''

YCSB_OUT_2 = '''
Adding shard node URL: jdbc:mysql://127.0.0.1:3306/benchmark
Using shards: 1, batchSize:-1, fetchSize: -1
[OVERALL], RunTime(ms), 3895.0
[OVERALL], Throughput(ops/sec), 1283.6970474967907
[TOTAL_GCS_MarkSweepCompact], Count, 0.0
[TOTAL_GC_TIME_MarkSweepCompact], Time(ms), 0.0
[TOTAL_GC_TIME_%_MarkSweepCompact], Time(%), 0.0
[TOTAL_GCS_Copy], Count, 61.0
[TOTAL_GC_TIME_Copy], Time(ms), 45.0
[TOTAL_GC_TIME_%_Copy], Time(%), 1.1553273427471118
[TOTAL_GCs], Count, 61.0
[TOTAL_GC_TIME], Time(ms), 45.0
[TOTAL_GC_TIME_%], Time(%), 1.1553273427471118
[SCAN], Operations, 4748.0
[SCAN], AverageLatency(us), 401.94945240101094
[SCAN], MinLatency(us), 112.0
[SCAN], MaxLatency(us), 9535.0
[SCAN], 95thPercentileLatency(us), 620.0
[SCAN], 99thPercentileLatency(us), 1939.0
[SCAN], Return=OK, 4748
[CLEANUP], Operations, 1.0
[CLEANUP], AverageLatency(us), 1002.0
[CLEANUP], MinLatency(us), 1002.0
[CLEANUP], MaxLatency(us), 1002.0
[CLEANUP], 95thPercentileLatency(us), 1002.0
[CLEANUP], 99thPercentileLatency(us), 1002.0
[INSERT], Operations, 252.0
[INSERT], AverageLatency(us), 5983.214285714285
[INSERT], MinLatency(us), 4336.0
[INSERT], MaxLatency(us), 14423.0
[INSERT], 95thPercentileLatency(us), 8131.0
[INSERT], 99thPercentileLatency(us), 10975.0
[INSERT], Return=OK, 252
'''

FILEBENCH_TEST_OUT = '''
16845: 0.000: Allocated 170MB of shared memory
16845: 0.001: Varmail Version 3.0 personality successfully loaded
16845: 0.001: Creating/pre-allocating files and filesets
16845: 0.002: Fileset bigfileset: 1000 files, 0 leafdirs, avg dir width = 1000000, avg dir depth = 0.5, 14.959MB
16845: 0.003: Removed any existing fileset bigfileset in 1 seconds
16845: 0.003: making tree for filset /tmp/bigfileset
16845: 0.004: Creating fileset bigfileset...
16845: 0.026: Preallocated 805 of 1000 of fileset bigfileset in 1 seconds
16845: 0.026: waiting for fileset pre-allocation to finish
16849: 0.026: Starting 1 filereader instances
16850: 0.027: Starting 16 filereaderthread threads
16845: 1.053: Running...
16845: 301.079: Run took 300 seconds...
16845: 301.080: Per-Operation Breakdown
closefile4           138237ops      461ops/s   0.0mb/s      0.0ms/op      535us/op-cpu [0ms - 0ms]
readfile4            138238ops      461ops/s   7.2mb/s      0.1ms/op      550us/op-cpu [0ms - 157ms]
openfile4            138240ops      461ops/s   0.0mb/s      0.0ms/op      518us/op-cpu [0ms - 2ms]
closefile3           138243ops      461ops/s   0.0mb/s      0.0ms/op      563us/op-cpu [0ms - 1ms]
fsyncfile3           138243ops      461ops/s   0.0mb/s     12.7ms/op     4532us/op-cpu [3ms - 1169ms]
appendfilerand3      138243ops      461ops/s   3.6mb/s      0.1ms/op      645us/op-cpu [0ms - 487ms]
readfile3            138243ops      461ops/s   7.2mb/s      0.1ms/op      621us/op-cpu [0ms - 488ms]
openfile3            138248ops      461ops/s   0.0mb/s      0.0ms/op      591us/op-cpu [0ms - 1ms]
closefile2           138252ops      461ops/s   0.0mb/s      0.0ms/op      658us/op-cpu [0ms - 0ms]
fsyncfile2           138252ops      461ops/s   0.0mb/s     11.5ms/op     3949us/op-cpu [4ms - 1168ms]
appendfilerand2      138253ops      461ops/s   3.6mb/s      0.0ms/op      413us/op-cpu [0ms - 16ms]
createfile2          138253ops      461ops/s   0.0mb/s      0.1ms/op      489us/op-cpu [0ms - 31ms]
deletefile1          138253ops      461ops/s   0.0mb/s      0.2ms/op      617us/op-cpu [0ms - 157ms]
16845: 301.080: IO Summary: 1797198 ops, 5990.130 ops/s, (922/922 r/w),  21.6mb/s,    331us cpu/op,   6.2ms latency
16845: 301.080: Shutting down processes
'''

if __name__ == '__main__':

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    #os.environ[CONFIG_FOLDER_VARIABLE_NAME] = '/home/ggiammat/projects/ENG.CloudPerfect/workspace/testing/bsconfig'

    p = YCSBResultParser()

    x = p.get_metrics(YCSB_OUT_1, 'ciao')

    print(x)