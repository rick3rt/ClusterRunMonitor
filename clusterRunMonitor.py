# A Python script that can be used to monitor cluster jobs.
# Rick Waasdorp, 10-Jul-2019

import argparse
import ConfigParser
import subprocess
import os
from shutil import copyfile
from datetime import datetime, timedelta
import copy


class ClusterRunMonitor:
    def __init__(self):
        # load user settings
        self.load_settings()
        # parse input arguments
        self.input_arg_parser()

        # act based on args
        if self.args.set:
            self.set_setting(self.args.set[0], self.args.set[1])
            return

        elif self.args.get:
            # print(self.args.get)
            self.get_setting(self.args.get[0])
            return

        elif self.args.reset:
            self.reset_backup_settings()
            return

        elif self.args.list:
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
                            type=int, default=self.num_jobs_to_list, metavar='n')
        parser.add_argument('-D', '--numdays', help='Set number of days to include in job history',
                            type=int, default=self.num_days_history, metavar='d')
        parser.add_argument(
            '-c', '--cat', help='cat or tail? Default: cat, add argument to tail', action="store_true")

        # set and get
        parser.add_argument('--set', help='Set a setting in the ini',
                            type=str, nargs=2, metavar=('toSet', 'valToSet'))
        parser.add_argument('--get', help='Get (view) a setting from the ini. use \'--get all\' to list all settings',
                            type=str, nargs=1, metavar='toGet')
        parser.add_argument('--reset', help='Reset settings backup file, if exists.',
                            action="store_true")

        self.args = parser.parse_args()

    def load_settings(self):
        # config file name
        configFileName = 'crm_config.ini'
        filePath = os.path.dirname(os.path.realpath(__file__))
        configFilePath = os.path.join(filePath, configFileName)
        self.configFilePath = configFilePath
        # check if exists
        if os.path.isfile(configFilePath):
            self.load_config_file(configFilePath)
        else:
            print('creating new config file')
            self.create_config_file(configFilePath)
            print('load just created config file')
            self.load_config_file(configFilePath)

    def create_config_file(self, configFilePath):
        # create config parser:
        config = ConfigParser.ConfigParser(allow_no_value=True)
        # general settings
        config.add_section('GENERAL')
        config.set('GENERAL', 'log_file_path', '')
        config.set('GENERAL', 'username', '')
        config.set('GENERAL', 'num_jobs_to_list', '10')
        config.set('GENERAL', 'num_days_history', '2')

        # Writing our configuration file to
        with open(configFilePath, 'w') as configfile:
            config.write(configfile)

    def update_config_file(self, configFilePath, toSet, valToSet):
        # backup config
        copyfile(configFilePath, configFilePath + '.backup')

        # create config parser:
        config = ConfigParser.ConfigParser(allow_no_value=True)
        # load config file
        config.read(configFilePath)
        # general settings
        config.set('GENERAL', toSet, valToSet)
        # Writing our configuration file to
        with open(configFilePath, 'w') as configfile:
            config.write(configfile)

    def load_config_file(self, configFilePath):
        # create config parser:
        config = ConfigParser.ConfigParser(allow_no_value=True)
        # load config file
        config.read(configFilePath)

        # general section
        self.log_file_path = config.get('GENERAL', 'log_file_path')
        self.user_name = config.get('GENERAL', 'username')
        self.num_jobs_to_list = config.getint('GENERAL', 'num_jobs_to_list')
        self.num_days_history = config.getint('GENERAL', 'num_days_history')

        # write settings names for reference
        self.setting_names = ['log_file_path', 'username', 'num_jobs_to_list', 'num_days_history']

    def get_setting(self, toGet):
        if toGet == 'log_file_path':
            print('{}:\t{}'.format(toGet, self.log_file_path))
        elif toGet == 'username':
            print('{}:\t{}'.format(toGet, self.user_name))
        elif toGet == 'num_jobs_to_list':
            print('{}:\t{}'.format(toGet, self.num_jobs_to_list))
        elif toGet == 'num_days_history':
            print('{}:\t{}'.format(toGet, self.num_days_history))
        elif toGet == 'all' or toGet == '?':
            print('{}:\t{}'.format('log_file_path', self.log_file_path))
            print('{}:\t{}'.format('username', self.user_name))
            print('{}:\t{}'.format('num_jobs_to_list', self.num_jobs_to_list))
            print('{}:\t{}'.format('num_days_history', self.num_days_history))
        else:
            print('Unkown setting: {}'.format(toGet))

    def set_setting(self, toSet, valToSet):
        # check if valid setting
        if toSet in self.setting_names:
            self.update_config_file(self.configFilePath, toSet, valToSet)
            print('Updated settings')
            print('{}:\t{}'.format(toSet, valToSet))

    def reset_backup_settings(self):
        # check if backup file exists
        if os.path.isfile(self.configFilePath + '.backup'):
            copyfile(self.configFilePath + '.backup', self.configFilePath)
            print('Reverted to backup settings.')
        else:
            print('No backup found.')

    def runCommand(self, cmd):
        command = cmd.split(' ')
        # command = "ls -l".split(' ')
        p = subprocess.Popen(command, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out, err

    def getJobInfo(self, numDays=None):
        '''Gets finished  job names
        Runs the following command:
            sacct -u <username> --format="JobID,jobname,elapsed,state,start,end" -n -X -P'''

        if not numDays:
            numDays = self.num_days_history

        # get start time for slurm
        startTime = datetime.now() - timedelta(days=numDays)
        st_str = startTime.strftime('%Y-%m-%dT%H:%M:%S')

        # run system command
        out, err = self.runCommand(
            "sacct -u " + self.user_name + " --format=JobID,JobName,elapsed,state,start,end -n -X -P -S " + st_str)

        # split output in list (without newline char...)
        if out:
            # decode out and plit
            out = out.decode("utf-8").split('\n')
            # remove empty lists
            out = [x for x in out if x]
            # split contents of list
            jobInfo = [x.split('|') for x in out]

            # convert start and end to datetime
            jobNames = []
            for i in range(len(jobInfo)):
                # 0JobName,1elapsed,2state,3start,4end
                jobNames.append(jobInfo[i][0])
                for k in [4, 5]:
                    if 'Unknown' not in jobInfo[i][k]:
                        # convert to datetime
                        dt = datetime.strptime(jobInfo[i][k], '%Y-%m-%dT%H:%M:%S')
                        # make nive printable string
                        jobInfo[i][k] = dt.strftime('%m-%d %H:%M')

            # return stuff
            return jobNames, jobInfo
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
            header = ['JobNum', 'JobID', 'JobName', 'Duration', 'State', 'Start', 'End']
        else:
            header = ['JobID', 'JobName', 'Duration', 'State', 'Start', 'End']

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
        # check if there are jobs
        if info:
            # number them
            info = self.numberJobs(info)
            # print them
            self.printInfo(info, numJobs=self.args.num)
        else:
            print('No Jobs found (for given number of days, try option: -D numdays)')

    def showJob(self):
        # get job info
        _, info = self.getJobInfo(self.args.numdays)
        # number them
        if info:
            info = self.numberJobs(info)

            # select correct job
            for job in info:
                if job[0] == self.args.jobNum:
                    jobinfo = job

            # what to do with the job
            jobName = jobinfo[2]
            self.printInfo([jobinfo])
            # cat ouput file
            if self.args.output or self.args.error:
                self.lookupFileAndShow(jobName)
                return
        else:
            print('No Jobs found (for given number of days, try option: -D numdays)')

    def lookupFileAndShow(self, jobName):
        basePath = self.log_file_path
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

    def getRunningJobNames(self):
        '''Gets the current running job names
        Runs the following command:
            squeue -u <username> -o %j -h'''

        # run system command
        out, err = self.runCommand("squeue -u " + self.user_name + " -o %j -h")

        # split output in list (without newline char...)
        if out:
                # decode out and split
            out = out.decode("utf-8").split('\n')
            # remove empty lists
            out = [x for x in out if x]
            return out
        elif err:
            print(err)
        else:
            return None


if __name__ == '__main__':
    # cd to file dir
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    # run the monitor
    crm = ClusterRunMonitor()
