"""
The MIT License (MIT)

Copyright (c) 2015 Mike Goodfellow

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
import os
import subprocess
from zipfile import ZipFile
import formic

required_plan_values = ['Name', 'Src', 'Output']
optional_plan_values = ['Command']

logger = logging.getLogger(name='Plan')

class Plan:

    def __init__(self, raw_plan):
        failed = False

        for required_value in required_plan_values:
            if required_value not in raw_plan:
                failed = True
                logger.error('Missing plan configuration value: %s', required_value)

        self.name = raw_plan['Name']
        self.src = raw_plan['Src']
        self.output = raw_plan['Output']
        self.command = None

        if 'Command' in raw_plan:
            self.command = raw_plan['Command']

        if failed:
            raise Exception('Missing keys from data. See log for details.')

    def run(self):
        """
            The plan is run in the following order:
                1) (if applicable) Run the external command provided
                2) Zip source file(s) to destination file
                3) Upload destination file to S3 bucket
        """
        logger.info('Running plan "%s"', self.name)

        # 1) (if applicable) Run the external command provided
        if self.command is not None:
            self.__run_command()

        # 2) Zip the source file to the destination file
        self.__zip_files()

        # 3) Upload destination file to S3 bucket
        self.__upload()

    def __run_command(self):
        logger.info('Executing custom command...')

        try:
            fnull = open(os.devnull, "w")
            retcode = subprocess.call(self.command, shell=True, stdout=fnull, stderr=subprocess.STDOUT)

            if retcode != 0:
                raise Exception('Failed with code %d' % retcode)

        except subprocess.CalledProcessError, e:
            logger.error('Failed with code %d : %s', e.returncode, e.output)
            raise

    def __zip_files(self):
        fileset = formic.FileSet(include=[self.src])

        # Check there are files in the file set
        if len(fileset.files()) == 0:
            raise Exception('No input files retrieved from pattern: %s' % self.src)

        with ZipFile(self.output, 'w') as myzip:
            for file_name in fileset:
                try:
                    myzip.write(file_name)
                except Exception, e:
                    logger.error('Error while adding file to the archive: %s', file_name)
                    raise

    def __upload(self):
        logger.info('Placeholder')
