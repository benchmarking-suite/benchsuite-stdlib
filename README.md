This repository contains a basic Benchmarking Suite configuration. This is a good starting point to configure your Benchmarking Suite installation.

The Benchmarking Suite configuration directory contains two sub-directories:
- **benchmarks**: for the configuration files of the benchmark tests
- **providers**: for the configuration files of the service providers to test

While the benchmark configuration files in this repository are directly usable from the Benchmarking Suite, the providers configuration files must be customized (e.g. access credentials). 

# Quick Start
Download the repository content and set the `BENCHSUITE_CONFIG_FOLDER` environment variable.
~~~
git clone https://github.com/benchmarking-suite/benchsuite-configuration.git
export BENCHSUITE_CONFIG_FOLDER=`pwd`/benchsuite-configuration
~~~
You can add the configuration to your .bashrc for convenience 
~~~
echo "export BENCHSUITE_CONFIG_FOLDER=`pwd`/benchsuite-configuration" >> ~/.bashrc
source ~/.bashrc
~~~

## Amazon AWS provider

Make your own provider configuration file starting from the provided template
~~~
cp $BENCHSUITE_CONFIG_FOLDER/providers/amazon.conf.example $BENCHSUITE_CONFIG_FOLDER/providers/my-amazon.conf
~~~

Open `my-amazon.conf` and complete the missing data with your personal Amazon AWS information :
```ini
[provider]
class = benchsuite.provider.libcloud.LibcloudComputeProvider

type = ec2

access_id = <your access_id>
secret_key = <your secret_key>

[libcloud_extra_params]
region = us-west-1
ex_security_group_ids = <id of the security group>
ex_subnet = <id of the subnet>

[ubuntu_micro]
image = ami-73f7da13
size = t2.micro
key_name = <your keypair name>
key_path = <path to your private key file>
vm_user = ubuntu
platform = ubuntu_16
```

Now you can use the provider configuration :bowtie::
```commandline
python -m benchsuite.cli exec --provider my-amazon --service ubuntu_micro --tool ycsb-mongodb --workload WorkloadA
```
