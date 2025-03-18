# Using AWS Roles with AWS Inventory

This document explains how to use AWS roles with the AWS Inventory application.

## Overview

AWS Inventory supports using AWS IAM roles for accessing AWS resources. This is particularly useful when:
- Working with AWS Organizations and cross-account access
- Using temporary credentials from AWS STS
- Implementing role-based access control (RBAC)

## Role Configuration

### 1. Create an IAM Role

First, create an IAM role with the necessary permissions. Here's an example IAM policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeVpcs",
                "dynamodb:ListTables",
                "s3:ListBuckets",
                "elasticloadbalancing:DescribeTargetGroups"
            ],
            "Resource": "*"
        }
    ]
}
```

### 2. Configure Role Assumption

1. Create a new AWS profile in the application
2. Set the following credentials:
   - AWS Access Key ID: Your IAM user's access key
   - AWS Secret Access Key: Your IAM user's secret key
   - AWS Session Token: Leave empty (will be populated automatically)
   - AWS Region: Your target region

3. Add the following to your profile's session token field:
```json
{
    "RoleArn": "arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME",
    "RoleSessionName": "aws_inventory_session"
}
```

Replace:
- `ACCOUNT_ID` with your AWS account ID
- `ROLE_NAME` with the name of your IAM role

### 3. Example Usage

Here's an example of a complete profile configuration:

```json
{
    "name": "cross-account-role",
    "aws_access_key_id": "AKIAXXXXXXXXXXXXXXXX",
    "aws_secret_access_key": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "aws_session_token": {
        "RoleArn": "arn:aws:iam::123456789012:role/AWSInventoryRole",
        "RoleSessionName": "aws_inventory_session"
    },
    "aws_region": "us-east-1"
}
```

## Security Considerations

1. **Least Privilege**: Always follow the principle of least privilege when creating IAM roles
2. **Session Duration**: Role sessions are temporary and will expire
3. **Access Key Rotation**: Regularly rotate your IAM user's access keys
4. **Audit Trail**: Enable AWS CloudTrail to monitor role assumption

## Troubleshooting

If you encounter issues:

1. Verify the IAM user has permission to assume the role
2. Check the role's trust relationship allows your account/user
3. Ensure the role has the necessary permissions
4. Review CloudWatch logs for detailed error messages

## Additional Resources

- [AWS IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [AWS STS AssumeRole](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [Cross-Account Access](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html) 