"""Tests for AWS service classes."""

from unittest.mock import Mock, patch

import pytest
from aws_classes import Alb, DynamoDB, Ec2
from botocore.exceptions import ClientError


@patch("boto3.Session.client")
def test_alb_describe_target_groups(mock_boto3_client, aws_profile):
    """Test ALB target groups description."""
    mock_response = {
        "TargetGroups": [
            {
                "TargetGroupName": "test-tg",
                "Protocol": "HTTP",
                "Port": 80,
                "VpcId": "vpc-123",
                "TargetType": "instance",
                "LoadBalancerArns": ["arn:aws:123"],
                "HealthCheckProtocol": "HTTP",
                "HealthCheckPort": "80",
                "HealthCheckPath": "/health",
                "Matcher": {"HttpCode": "200"},
            }
        ]
    }
    mock_client = Mock()
    mock_client.describe_target_groups.return_value = mock_response
    mock_boto3_client.return_value = mock_client

    alb = Alb(aws_profile)
    result = alb.describe_target_groups()

    assert len(result) == 1
    assert result[0]["Name"] == "test-tg"
    assert result[0]["Protocol"] == "HTTP"
    assert result[0]["Port"] == 80


@patch("boto3.Session.client")
def test_dynamodb_describe_tables(mock_boto3_client, aws_profile):
    """Test DynamoDB tables description."""
    mock_response = {"TableNames": ["table1", "table2"]}
    mock_client = Mock()
    mock_client.list_tables.return_value = mock_response
    mock_boto3_client.return_value = mock_client

    dynamodb = DynamoDB(aws_profile)
    result = dynamodb.describe_dynamodb()

    assert len(result) == 2
    assert result[0]["Name"] == "table1"
    assert result[1]["Name"] == "table2"


@patch("boto3.Session.client")
def test_ec2_describe_instances(mock_boto3_client, aws_profile):
    """Test EC2 instances description."""
    mock_response = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-123",
                        "InstanceType": "t2.micro",
                        "VpcId": "vpc-123",
                        "SubnetId": "subnet-123",
                        "SecurityGroups": [{"GroupId": "sg-123"}],
                        "IamInstanceProfile": {"Arn": "arn:aws:iam::123:role/test-role"},
                        "LaunchTime": "2023-01-01T00:00:00Z",
                        "PrivateIpAddress": "10.0.0.1",
                        "State": {"Name": "running"},
                        "PlatformDetails": "Linux",
                        "Tags": [
                            {"Key": "Name", "Value": "test-instance"},
                            {"Key": "Env", "Value": "test"},
                        ],
                    }
                ]
            }
        ]
    }
    mock_client = Mock()
    mock_client.describe_instances.return_value = mock_response
    mock_boto3_client.return_value = mock_client

    ec2 = Ec2(aws_profile)
    result = ec2.describe_ec2()

    assert len(result) == 1
    assert result[0]["Name"] == "test-instance"
    assert result[0]["Instance Id"] == "i-123"
    assert result[0]["Instance Type"] == "t2.micro"


@patch("boto3.Session.client")
def test_error_handling(mock_boto3_client, aws_profile):
    """Test AWS error handling."""
    mock_client = Mock()
    mock_client.describe_instances.side_effect = ClientError(
        error_response={"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
        operation_name="DescribeInstances",
    )
    mock_boto3_client.return_value = mock_client

    ec2 = Ec2(aws_profile)
    with pytest.raises(ClientError):
        ec2.describe_ec2()
