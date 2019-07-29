# A Python script that can be used to monitor cluster jobs.
# Not pretty, but does the job.
# Rick Waasdorp, 10-Jul-2019

import argparse
import subprocess
import os
from datetime import datetime, timedelta
import copy


class ClusterRunMonitor:
    def __init__(self):
        # parse input arguments
        self.input_arg_parser()

        # act based on args
        if self.args.list:
            self.listJobs()
            return

        elif self.args.jobNum:
            self.showJob()
            return

        else:
            self.listJobs()
            return

    def input_arg_parser(self):
        # input argument parser
        parser = argparse.ArgumentParser(
            description='List running slurm jobs, and monitor them.')

        parser.add_argument('-l', '--list', help='List running jobs', action="store_true")
        parser.add_argument(
            '-j', '--jobNum', help='Select job number (not slurm reference, but see --list)', type=int, metavar='jn')
        parser.add_argument('-o', '--output', help='Show output log for a job', action="store_true")
        parser.add_argument('-e', '--error', help='Show error log for a job', action="store_true")
        parser.add_argument('-N', '--num', help='Set number of jobs to list',
                            type=int, default=10, metavar='n')
        parser.add_argument('-D', '--numdays', help='Set number of days to include in job history',
                            type=int, default=2, metavar='d')
        parser.add_argument(
            '-c', '--cat', help='cat or tail? Default: cat, add argument to tail', action="store_true")

        self.args = parser.parse_args()

    def runCommand(self, cmd):
        command = cmd.split(' ')
        # command = "ls -l".split(' ')
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out, err

    def getRunningJobNames(self):
        '''Gets the current running job names
        Runs the following command:
            squeue -u rwaasdorp -o %j -h'''

        # run system command
        out, err = self.runCommand("squeue -u rwaasdorp -o %j -h")

        # split output in list (without newline char...)
        if out:
            # decode out and plit
            out = out.decode("utf-8").split('\n')
            # remove empty lists
            out = [x for x in out if x]
            return out
        elif err:
            print(err)
        else:
            return None

    def getJobInfo(self, numDays=2):
        '''Gets finished  job names
        Runs the following command:
            sacct -u rwaasdorp --format="jobname,elapsed,state,start,end" -n -X -P'''

        # get start time for slurm
        startTime = datetime.now() - timedelta(days=numDays)
        st_str = startTime.strftime('%Y-%m-%dT%H:%M:%S')

        # run system command
        out, err = self.runCommand(
            "sacct -u rwaasdorp --format=JobName,elapsed,state,start,end -n -X -P -S " + st_str)

        # split output in list (without newline char...)
        if out:
            # decode out and plit
            out = out.decode("utf-8").split('\n')
            # remove empty lists
            out = [x for x in out if x]
            # split contents of list
            out2 = [x.split('|') for x in out]
            # convert start and end to datetime
            jobNames = []
            for i in range(len(out2)):
                # 0JobName,1elapsed,2state,3start,4end
                jobNames.append(out2[i][0])
                for k in [3, 4]:
                    if 'Unknown' not in out2[i][k]:
                        # convert to datetime
                        dt = datetime.strptime(out2[i][k], '%Y-%m-%dT%H:%M:%S')
                        # make nive printable string
                        out2[i][k] = dt.strftime('%m-%d %H:%M')

            # return stuff
            return jobNames, out2
        elif err:
            print(err)
        else:
            return None, None

    def sortJobs(self, jobInfo):
        # categorize jobs: running, completed
        running = []
        completed = []
        for job in jobInfo:
            if job[4] == "Unknown":
                running.append(job)
            else:
                completed.append(job)

        # sort jobs in completed
        completed.sort(key=lambda x: x[4])
        return running, completed

    def printInfo(self, jobInfo, numJobs=10, numbered=True):
        # print in pretty format
        if numbered:
            header = ['JobNum', 'JobName', 'Duration', 'State', 'Start', 'End']
        else:
            header = ['JobName', 'Duration', 'State', 'Start', 'End']

        # select last 10 jobs or max
        numJobs = min(len(jobInfo), numJobs)
        jobInfoSel = jobInfo[-numJobs:]
        self.prettyPrint(jobInfoSel, header)

    def prettyPrint(self, data, header=None):
        # determine spacing
        data_comb = copy.deepcopy(data)
        if header:
            data_comb.append(header)
        spacing = [max(map(lambda x: len(str(x)), d)) for d in zip(*data_comb)]

        # print header
        if header:
            print '|--' + (sum(spacing) + len(spacing) * 6 - 1) * '-' + '|'
            print '|  ',
            for i, elem in enumerate(header):
                e = str(elem) + (spacing[i] - len(str(elem)) + 3) * ' '
                print e, '|',
            print
            print '|--' + (sum(spacing) + len(spacing) * 6 - 1) * '-' + '|'

        # print data
        for row in data:
            print '|  ',
            for i, elem in enumerate(row):
                e = str(elem) + (spacing[i] - len(str(elem)) + 3) * ' '
                print e, '|',
            print

        # close it
        print '|--' + (sum(spacing) + len(spacing) * 6 - 1) * '-' + '|'

    def numberJobs(self, jobInfo):
        # make deepcopy because i dont want to think about references at the moment
        jobInfoNumbered = copy.deepcopy(jobInfo)
        # add number
        [x.insert(0, num) for x, num in zip(jobInfoNumbered, range(len(jobInfoNumbered), 0, -1))]
        return jobInfoNumbered

    def listJobs(self):
        # get job info
        _, info = self.getJobInfo(self.args.numdays)
        # number them
        info = self.numberJobs(info)
        # print them
        self.printInfo(info, numJobs=self.args.num)

    def showJob(self):
        # get job info
        _, info = self.getJobInfo()
        # number them
        info = self.numberJobs(info)

        # select correct job
        for job in info:
            if job[0] == self.args.jobNum:
                jobinfo = job

        # what to do with the job
        jobName = jobinfo[1]
        self.printInfo([jobinfo])
        # cat ouput file
        if self.args.output or self.args.error:
            self.lookupFileAndShow(jobName)
            return

    def lookupFileAndShow(self, jobName):
        basePath = '/home/rwaasdorp/EMech_waves/mechanical_model/model/log/mega_batch'
        # select right files
        files = [f for f in os.listdir(basePath) if os.path.isfile(
            os.path.join(basePath, f)) and jobName in f]

        # set how to display file
        if self.args.cat:
            # set show command to tail
            showCommand = 'tail'
        else:
            # set show command to cat
            showCommand = 'cat'

        if self.args.output:
            file = [x for x in files if 'out' in x][0]
            filePath = os.path.join(basePath, file)
            out, err = self.runCommand(showCommand + ' ' + filePath)
            if out:
                print(out)
            if err:
                print(err)
            return

        if self.args.error:
            file = [x for x in files if 'err' in x][0]
            filePath = os.path.join(basePath, file)
            out, err = self.runCommand(showCommand + ' ' + filePath)
            if out:
                print(out)
            if err:
                print(err)
            return


if __name__ == '__main__':
    crm = ClusterRunMonitor()