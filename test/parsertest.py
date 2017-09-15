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

from benchsuite.core.config import CONFIG_FOLDER_VARIABLE_NAME
from benchsuite.stdlib.benchmark.parsers import FileBenchResultParser



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

    os.environ[CONFIG_FOLDER_VARIABLE_NAME] = '/home/ggiammat/projects/ENG.CloudPerfect/workspace/testing/bsconfig'

    p = FileBenchResultParser()

    p.get_metrics(FILEBENCH_TEST_OUT, 'ciao')