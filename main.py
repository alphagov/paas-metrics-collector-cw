import os
import boto3
import base64
import sched
import time
import random
from cloudfoundry_client.client import CloudFoundryClient

class MetricsCollector:
    def __init__(self):
        self.schedule_interval = int(os.environ['SCHEDULE_INTERVAL']) + 0.0
        self.schedule_delay = random.random() * self.schedule_interval
        self.scheduler = sched.scheduler(time.time, time.sleep)

        self.aws_region = os.environ['AWS_REGION']

        self.cloudwatch_client = boto3.client('cloudwatch', region_name=self.aws_region)
        self.cloudwatch_namespace = os.environ['CLOUDWATCH_NAMESPACE']

        self.cf_username = os.environ['CF_USERNAME']
        self.cf_password = os.environ['CF_PASSWORD']
        self.cf_api_url = os.environ['CF_API_URL']
        self.cf_org = os.environ['CF_ORG']
        self.cf_space = os.environ['CF_SPACE']
        self.cf_client = None

    def get_cloudfoundry_client(self):
        if self.cf_client is None:
            proxy = dict(http=os.environ.get('HTTP_PROXY', ''), https=os.environ.get('HTTPS_PROXY', ''))
            cf_client = CloudFoundryClient(self.cf_api_url, proxy=proxy)
            try:
                cf_client.init_with_user_credentials(self.cf_username, self.cf_password)
                self.cf_client = cf_client
            except BaseException as e:
                print('Failed to authenticate: {}, waiting 5 minutes and exiting'.format(str(e)))
                # The sleep is added to avoid automatically banning the user for too many failed login attempts
                time.sleep(5 * 60)

        return self.cf_client

    def reset_cloudfoundry_client(self):
        self.cf_client = None

    def get_cloudfoundry_app_stats(self):
        stats = {}
        cf_client = self.get_cloudfoundry_client()
        if cf_client is not None:
            try:
                for organization in cf_client.organizations:
                    if organization['entity']['name'] != self.cf_org:
                        continue
                    for space in organization.spaces():
                        if space['entity']['name'] != self.cf_space:
                            continue
                        for app in space.apps():

                                if app['entity']['state'] != 'STARTED':
                                    continue;
                                stats[app['entity']['name']] = cf_client.apps.get_stats(app['metadata']['guid'])
            except BaseException as e:
                print('Failed to get stats for app {}: {}'.format(app['entity']['name'], str(e)))
                self.reset_cloudfoundry_client()

        return stats

    def send_cloudwatch_metrics(self, app_name, app_stats, metric_name, metric_unit):
        count = 0
        value = 0
        value_min = None
        value_max = 0
        value_sum = 0
        time = None
        for index, app_stat in app_stats.items():
            if app_stat['state'] != 'RUNNING':
                continue
            value = round(app_stat['stats']['usage'][metric_name], 2)
            if value_min is None:
                value_min = value
            else:
                value_min = min(value_min, value)
            value_max = max(value_max, value)
            value_sum += value
            count = count + 1
            time = app_stat['stats']['usage']['time']

        if count == 0:
            print('No running instances found for {}'.format(app_name))
            return

        value_avg = value_sum / count

        print('{} ({}) {}: {} (min) {} (max) {} (avg)'.format(app_name, count, metric_name, value_min, value_max, value_avg))

        try:
            self.cloudwatch_client.put_metric_data(
                Namespace=self.cloudwatch_namespace,
                MetricData=[
                    {
                        'MetricName': 'cf-{}-{}'.format(app_name, metric_name),
                        'Timestamp': time,
                        'StatisticValues': {
                            'SampleCount': count,
                            'Minimum': value_min,
                            'Maximum': value_max,
                            'Sum': value_sum
                        },
                        'Unit': metric_unit
                    },
                ]
            )
        except Exception as e:
            print('Pushing metrics to Cloudwatch failed: {}'.format(str(e)))

    def schedule(self):
        current_time = time.time()
        run_at = current_time + self.schedule_interval - ((current_time - self.schedule_delay) % self.schedule_interval)
        self.scheduler.enterabs(run_at, 1, self.run_task)

    def run_task(self):
        stats = self.get_cloudfoundry_app_stats()
        for app_name, app_stats in stats.items():
            self.send_cloudwatch_metrics(app_name, app_stats, 'cpu', 'None')
            self.send_cloudwatch_metrics(app_name, app_stats, 'disk', 'Bytes')
            self.send_cloudwatch_metrics(app_name, app_stats, 'mem', 'Bytes')

        self.schedule()

    def run(self):
        print('API endpoint:   {}'.format(self.cf_api_url))
        print('User:           {}'.format(self.cf_username))
        print('Org:            {}'.format(self.cf_org))
        print('Space:          {}'.format(self.cf_space))

        self.schedule()
        while True:
            self.scheduler.run()

MetricsCollector().run()
