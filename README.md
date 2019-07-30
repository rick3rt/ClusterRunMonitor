# ClusterRunMonitor

Small python application that can be used to monitor jobs running on the cluster. 

Especially usefull when running many batch jobs, and their log files are stored in one folder (see section [Batch script structure](#batch-script-and-folder-structure))

## Features
See overview of completed and running jobs:
```
$ crm -l
|-----------------------------------------------------------------------------------------------------|
|   JobNum    | JobID     | JobName    | Duration    | State        | Start          | End            |
|-----------------------------------------------------------------------------------------------------|
|   10        | 150143    | M261       | 00:05:40    | COMPLETED    | 07-28 07:34    | 07-28 07:40    |
|   9         | 150144    | M265       | 00:03:32    | COMPLETED    | 07-28 07:40    | 07-28 07:43    |
|   8         | 150145    | M269       | 00:05:55    | COMPLETED    | 07-28 07:43    | 07-28 07:49    |
|   7         | 150146    | M273       | 00:36:15    | COMPLETED    | 07-28 07:49    | 07-28 08:25    |
|   6         | 150147    | M278       | 00:03:13    | COMPLETED    | 07-28 08:04    | 07-28 08:08    |
|   5         | 150148    | M282       | 00:03:59    | COMPLETED    | 07-28 08:08    | 07-28 08:12    |
|   4         | 150149    | M286       | 00:30:48    | COMPLETED    | 07-28 08:12    | 07-28 08:42    |
|   3         | 150150    | M277       | 00:03:14    | COMPLETED    | 07-28 08:25    | 07-28 08:29    |
|   2         | 150151    | M281       | 00:03:55    | COMPLETED    | 07-28 08:29    | 07-28 08:33    |
|   1         | 150152    | M285       | 00:30:49    | COMPLETED    | 07-28 08:33    | 07-28 09:03    |
|-----------------------------------------------------------------------------------------------------|
```

See contents of `output` and `error` files of jobs (where `-j` corresponds to short `JobNum`). Use `-o` or `--output` for output log file:
```
$ crm -j 1 -o
|-----------------------------------------------------------------------------------------------------|
|   JobNum    | JobID     | JobName    | Duration    | State        | Start          | End            |
|-----------------------------------------------------------------------------------------------------|
|   1         | 150152    | M285       | 00:30:49    | COMPLETED    | 07-28 08:33    | 07-28 09:03    |
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
|   1         | 150152    | M285       | 00:30:49    | COMPLETED    | 07-28 08:33    | 07-28 09:03    |
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

## Usage
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