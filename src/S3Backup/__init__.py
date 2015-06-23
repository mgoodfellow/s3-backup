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
from S3Backup import config_loader
from time import strftime, gmtime
import boto.ses

logger = logging.getLogger(name='S3BackupTool')

class S3BackupTool:

    def __init__(self, config_file="config.json", log_file="s3backup.log"):
        logger.info('Initialising...')

        try:
            self.CONFIGURATION = config_loader.config_setup(config_file)
        except Exception, e:
            logger.fatal('Failed to load configuration: %s', e)
            raise e

        logger.info('Loaded configuration')

    def run_plans(self):
        if len(self.CONFIGURATION['Plans']) == 0:
            logger.warn('No plans to execute')
            return

        counter = 1
        for plan in self.CONFIGURATION['Plans']:
            logger.info('Executing plan %d of %d', counter, len(self.CONFIGURATION['Plans']))

            try:
                plan.run()
                self.__send_status_email(plan, True)
            except Exception, e:
                logger.error('Failed to run plan: ', e)
                self.__send_status_email(plan, False, e)

            counter += 1

        logger.info('Finished running backup plans')

    def __send_status_email(self, plan, success, exception=None):
        if self.CONFIGURATION['EMAIL_FROM'] is None or self.CONFIGURATION['EMAIL_TO'] is None:
            logger.debug('Email not provided, so status update not sent')
            return

        conn = boto.ses.connect_to_region(
            self.CONFIGURATION['AWS_REGION'],
            aws_access_key_id=self.CONFIGURATION['AWS_KEY'],
            aws_secret_access_key=self.CONFIGURATION['AWS_SECRET'])

        result = 'SUCCESS'
        if not success:
            result = 'FAILURE'

        body = 'The backup plan, %s, run at %s was %s' % (
            plan.name,
            strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()),
            result)

        if exception is not None:
            body += '\n\nDetailed failure information:\n\n%s' % exception

        try:
            conn.send_email(
                self.CONFIGURATION['EMAIL_FROM'],
                '[S3-Backup] [%s] - Plan: %s' % (result, plan.name),
                body,
                [self.CONFIGURATION['EMAIL_TO']])
        except Exception, e:
            logger.error('Failed to send email to {0:s} regarding plan: {1:s}'.format(self.CONFIGURATION['EMAIL_TO'],
                                                                                      plan.name),
                         e)
