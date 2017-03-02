# PaaS metrics collector

Collects Cloud Foundry application metrics regularly and sends them to AWS CloudWatch. Currently cpu, memory and disk usage values are collected.

The metrics values are sent to CloudWatch with the CLOUDWATCH_NAMESPACE namespace at SCHEDULE_INTERVAL interval.
If an application has multiple instances the minimum and maximum values are calculated as well (together with sum and count).

## Installation

Copy the manifest.yml.dist file as manifest.yml and fill out the environment variables to your needs.

Run ```cf push``` as usual.

## Authentication

For handling the authentication you have two choices:

1. Define a user-provided service named "paas-metrics-collector-cw" with the following parameters:

```
{
  "aws_access_key_id": "...",
  "aws_secret_access_key": "...",
  "cf_username": "...",
  "cf_password": "..."
}
```

```
cf create-user-provided-service paas-metrics-collector-cw -p '<json>'
```

2. Pass in all secrets as environment variables:

You need the define the following extra variables:

 * AWS_SECRET_ACCESS_KEY
 * AWS_ACCESS_KEY_ID
 * CF_USERNAME
 * CF_PASSWORD

In this case you need to remove the services block from the manifest.yml and the "run.sh" from the command definition.
