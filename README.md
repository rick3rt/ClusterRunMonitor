# ClusterRunMonitor

<!-- TOC -->

- [ClusterRunMonitor](#clusterrunmonitor)
    - [Features](#features)
    - [Setup](#setup)
        - [Configuring the monitor](#configuring-the-monitor)
    - [Batch script and folder structure](#batch-script-and-folder-structure)
    - [Future functionality](#future-functionality)

<!-- /TOC -->

Small python application that can be used to monitor jobs running on the cluster. Tested using python 2.6.6, only built-in modules needed.
Especially usefull when running many batch jobs, and their log files are stored in one folder (see section [Batch script structure](#batch-script-and-folder-structure))

## Features
See overview of completed and running jobs:
```
$ crm -l
|-----------------------------------------------------------------------------------------------------|
|   JobNum    | JobID     | JobName    | Duration    | State        | Start          | End            |
|-----------------------------------------------------------------------------------------------------|
|   10        | 150143    | JOB_001    | 00:05:40    | COMPLETED    | 07-28 07:34    | 07-28 07:40    |
|   9         | 150144    | JOB_002    | 00:03:32    | COMPLETED    | 07-28 07:40    | 07-28 07:43    |
|   8         | 150145    | JOB_003    | 00:05:55    | COMPLETED    | 07-28 07:43    | 07-28 07:49    |
|   7         | 150146    | JOB_004    | 00:36:15    | COMPLETED    | 07-28 07:49    | 07-28 08:25    |
|   6         | 150147    | JOB_005    | 00:03:13    | COMPLETED    | 07-28 08:04    | 07-28 08:08    |
|   5         | 150148    | JOB_006    | 00:03:59    | COMPLETED    | 07-28 08:08    | 07-28 08:12    |
|   4         | 150149    | JOB_007    | 00:30:48    | COMPLETED    | 07-28 08:12    | 07-28 08:42    |
|   3         | 150150    | JOB_008    | 00:03:14    | COMPLETED    | 07-28 08:25    | 07-28 08:29    |
|   2         | 150151    | JOB_009    | 00:03:55    | COMPLETED    | 07-28 08:29    | 07-28 08:33    |
|   1         | 150152    | JOB_010    | 00:30:49    | COMPLETED    | 07-28 08:33    | 07-28 09:03    |
|-----------------------------------------------------------------------------------------------------|
```

See contents of `output` and `error` files of jobs (where `-j` corresponds to short `JobNum`). Use `-o` or `--output` for output log file:
```
$ crm -j 1 -o
|-----------------------------------------------------------------------------------------------------|
|   JobNum    | JobID     | JobName    | Duration    | State        | Start          | End            |
|-----------------------------------------------------------------------------------------------------|
|   1         | 150152    | JOB_010    | 00:30:49    | COMPLETED    | 07-28 08:33    | 07-28 09:03    |
|-----------------------------------------------------------------------------------------------------|

Starting MATLAB job:
======================================================
MATLAB is selecting SOFTWARE OPENGL rendering.

                            < M A T L A B (R) >
                  Copyright 1984-2018 The MathWorks, Inc.
                   R2018b (9.5.0.944444) 64-bit (glnxa64)
                              August 28, 2018
...
```
And `-e` or `--error` for error log file:
```
$ crm -j 1 -e
|-----------------------------------------------------------------------------------------------------|
|   JobNum    | JobID     | JobName    | Duration    | State        | Start          | End            |
|-----------------------------------------------------------------------------------------------------|
|   1         | 150152    | JOB_010    | 00:30:49    | COMPLETED    | 07-28 08:33    | 07-28 09:03    |
|-----------------------------------------------------------------------------------------------------|

<contents of error file>
```

See all functions using `-h` or `--help`:
```
$ crm -h
usage: clusterRunMonitor.py [-h] [-l] [-j jn] [-o] [-e] [-N n] [-D d] [-c]

List running slurm jobs, and monitor them.

optional arguments:
  -h, --help          show this help message and exit
  -l, --list          List running jobs
  -j jn, --jobNum jn  Select job number (not slurm reference, but see --list)
  -o, --output        Show output log for a job
  -e, --error         Show error log for a job
  -N n, --num n       Set number of jobs to list
  -D d, --numdays d   Set number of days to include in job history
  -c, --cat           cat or tail? Default: cat, add argument to tail
```

## Setup
Clone the repository to any directory. For easy use create an alias in your `.bashrc`, for example:
```
alias crm='python <path_to_ClusterRunMonitor>/clusterRunMonitor.py'
```
Restart your terminal or source the `.bashrc` and run the ClusterRunMonitor using `crm` (or your defined alias). This will create a config file in the ClusterRunMonitor directory.

### Configuring the monitor 
The config file `crm_config.ini` will contain the following fields:
```
[GENERAL]
log_file_path = <path_to_log_folder>
username = <username_used_to_submit_batch_jobs>
num_jobs_to_list = 10
num_days_history = 2
```
* The `log_file_path` should point to the directory where the log files (`error` and `output`) are stored by Slurm.
* `num_jobs_to_list` is the default maximum number of jobs to list 
* `num_days_history` is the default number of days of history to include in the list



## Batch script and folder structure
To use the functions to show the `output` and `error` log files, a certain file and folder structure is required. This looks like: 
```
projectRoot
│
│   SimulationToRun.m
│
└───batch_scripts
│   │   runFile001.sh
│   │   runFile002.sh
│   └   ...
│
└───log
│   │   JOB_001_err
│   │   JOB_001_out
│   │   JOB_002_err
│   │   JOB_002_out
│   └   ...
│   
└───data
    │   results_JOB_001.mat
    │   results_JOB_002.mat
    └   ...
```

The batch script to start a job, `runFile001.sh`, looks like:
```
#!/bin/bash -login

#SBATCH --job-name=JOB_001

## set outputfile name
#SBATCH -o log/JOB_001_out

## set errorfile name
#SBATCH -e log/JOB_001_err

## JOB TO RUN, e.g. MATLAB
module load matlab/2018b
matlab -nodesktop -nosplash -r "SimulationToRun(1, 'DataFolder', 'data')"

## OPTIONAL: Next job to run
sbatch batch_scripts/runFile002.sh
```
Last line is optional, can be used to start the next job when this job is finished (i.e. not overloading the cluster with xxx jobs at the same time). Important:
* Each `job-name` should be unique (i.e. contain an identifier, e.g. '`JOB`', and a number), to reference the `out` and `error` files. 
* `outputfile` name should have the pattern `<job-name>_out`
* `errorfile` name should have the pattern `<job-name>_err`



To start the first job, open a terminal in the `projectRoot`, and run
```
sbatch batch_scripts/runFile001.sh
```
This will make sure that the working directory of the bash script is the `projectRoot`, and the log files will be written to the appropriate location. If the `log` folder does not exist yet, the job will immediately fail. 

It is recommended to have some other script create the `runFiles` and handle 

## Future functionality
- [ ] Cancel job using `crm -j <shortjobnum> --cancel`
- [ ] Add scripts to create many, many batch jobs (upon request)