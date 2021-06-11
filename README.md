# ec2-check-maintenance-scheduled
AWS EC2 get events status about maintenance scheduled and create Jira ticket

Set virtual environment:

```
pip3 install virtualenv

python3 -m venv venv

source venv/bin/activate

pip3 install boto3 requests python-dotenv

pip3 freeze > requirements.txt
```

Environment variables:

`AWS_KEY_ID` = aws key id

`AWS_KEY_SECRET` = aws key secret

`JIRA_URL` = https://{organization}.atlassian.net/rest/api/3/issue

`EMAIL_ADDRESS` = user.name@domain

`JIRA_API_TOKEN` = jira api token

`LIST_AWS_ACCOUNTS` = aws_account_id_1,aws_account_id_2, ...


IAM USER Role `EC2-check-maintenance-scheduled` from source account:

Policy: `EC2-check-maintenance-scheduled-assume-role`

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": [
                "arn:aws:iam::*:role/EC2-check-maintenance-scheduled"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": [
                "arn:aws:iam::*:role/EC2-check-maintenance-scheduled"
            ]
        }
    ]
}

```

IAM  Role `EC2-check-maintenance-scheduled` from source account:

Policy: `check-maintenance-scheduled-ec2`

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "ec2:DescribeInstanceStatus",
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeRegions"
            ],
            "Resource": "*"
        }
    ]
}
```



IAM Role `EC2-check-maintenance-scheduled` from destination account:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "ec2:DescribeInstanceStatus",
            "Resource": "*"
        },
        {
            "Sid": "VisualEditor1",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeAvailabilityZones",
                "ec2:DescribeRegions"
            ],
            "Resource": "*"
        }
    ]
}
```

Trust relationships:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{aws_source_account_id}:user/ec2-check-maintenance-scheduled"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```