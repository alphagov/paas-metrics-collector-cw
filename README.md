# PaaS metrics collector

Collects Cloud Foundry application metrics regularly and sends them to AWS CloudWatch. Currently cpu, memory and disk usage values are collected.

The metrics values are sent to CloudWatch with the CLOUDWATCH_NAMESPACE namespace at SCHEDULE_INTERVAL interval.
If an application has multiple instances the minimum and maximum values are calculated as well (together with sum and count).

## Installation

You need Ruby installed to generate the manifest file.

```
CF_SPACE=<space name> CF_ORG=<org name> make cf-push
```

For additional variables please check the manifest.yml.erb file.

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

 * CF_USE_SERVICE=0
 * AWS_SECRET_ACCESS_KEY
 * AWS_ACCESS_KEY_ID
 * CF_USERNAME
 * CF_PASSWORD
