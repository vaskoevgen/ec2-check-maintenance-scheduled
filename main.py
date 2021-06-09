# https://github.com/ronidas39/jira_automation/blob/main/tutorial1.py

import requests
from requests.auth import HTTPBasicAuth
import json
import boto3
import logging
import os

APP_VERSION = "1.0.0"

def init_logger(name, level):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    prefix = '[%(levelname)s]: %(message)s'
    formatter = logging.Formatter(prefix, "%d-%m-%Y %H:%M:%S")
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

def assume_iam_role(aws_account_id):

    log.info('Assumed role to aws account id: %s', aws_account_id)

    # session = boto3.Session(profile_name='ec2-check-maintenance-scheduled')
    session = boto3.Session(aws_access_key_id = os.getenv('AWS_KEY_ID'), aws_secret_access_key = os.getenv('AWS_KEY_SECRET'))
    sts_client = session.client('sts')

    # Call the assume_role method of the STSConnection object and pass the role
    # ARN and a role session name.
    assumed_role_object=sts_client.assume_role(
        RoleArn="arn:aws:iam::" + aws_account_id + ":role/EC2-check-maintenance-scheduled",
        RoleSessionName="AssumeRoleSession"
    )

    # From the response that contains the assumed role, get the temporary 
    # credentials that can be used to make subsequent API calls
    credentials=assumed_role_object['Credentials']
    return credentials

def get_aws_regions(credentials,region):
    ec2_client = boto3.client(
        'ec2',
        region_name=region,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    # Retrieves all regions/endpoints that work with EC2
    response = ec2_client.describe_regions()
    list_regions = list()
    for i in response["Regions"]:
        list_regions.append(i["RegionName"])

    return list_regions

def fill_in_report(content,event,key):
    try:
        content += key + ": " + str(event[key]) + "\n"
        log.info('%s: %s', key, str(event[key]))
    except:
        log.error('Key %s is not accessible', key)
    
    return content

def get_ec2_events(account,credentials,region):
    ec2_client = boto3.client(
        'ec2',
        region_name=region,
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    response = ec2_client.describe_instance_status(
        Filters=[
            {
                'Name': 'event.code',
                'Values': [
                    'instance-reboot',
                    'system-reboot',
                    'system-maintenance',
                    'instance-retirement',
                    'instance-stop'
                ],
            },
        ],
    )

    count = 0
    description = ""
    
    for instance in response['InstanceStatuses']:
        
        try:
            events = instance['Events']
        except:
            log.info('Key [Events] is not accessible')

        for event in events:
            if count == 0:
                description += "AWS accountId: " + account + "\n"
                log.info('AWS accountId: %s', account)
                
                description += "AWS region: " + region + "\n"
                log.info('AWS region: %s', region)

                description += "InstanceId: " + instance['InstanceId'] + "\n"
                log.info('InstanceId: %s', instance['InstanceId'])
                count = 1

            description = fill_in_report(description +" "*2,event,"InstanceEventId")
            description = fill_in_report(description +" "*2,event,"Code")
            description = fill_in_report(description +" "*2,event,"Description")
            description = fill_in_report(description +" "*2,event,"NotAfter")
            description = fill_in_report(description +" "*2,event,"NotBefore")
            description = fill_in_report(description +" "*2,event,"NotBeforeDeadline")

    return description

def create_jira_ticket(project,description):
    url=os.getenv('JIRA_URL')

    headers={
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload=json.dumps(
        {
        "fields": {
        "project":
        {
            "key": str(project)
        },
        "summary": "EC2 instances maintenance scheduled",
        "description": {
          "type": "doc",
          "version": 1,
          "content": [
            {
              "type": "paragraph",
              "content": [
                {
                  "type": "text",
                  "text": str(description)
                }
              ]
            }
          ]
        },
        "issuetype": {
            "name": "Task"
        }
    }
    }
    )
    response=requests.post(url,headers=headers,data=payload,auth=(os.getenv('EMAIL_ADDRESS'),os.getenv('JIRA_API_TOKEN')))
    data=response.json()
    print(data) 

def start():
    global log
    log = init_logger('main', 'INFO')

    log.info("ec2-check-maintenance-scheduled v%s started", APP_VERSION)

    list_aws_accounts = [
        os.getenv('LIST_AWS_ACCOUNTS')
    ]
    description = ""
    for account in list_aws_accounts:
        credentials = assume_iam_role(account)
        list_regions = get_aws_regions(credentials, "us-east-1")
        for region in list_regions:
            description += get_ec2_events(account, credentials, region) + "---\n"
    print(str(description))
    # create_jira_ticket("DO", description)
        
    log.info("ec2-check-maintenance-scheduled finished")

if __name__ == '__main__':
    start()
