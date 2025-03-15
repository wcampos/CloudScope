"""Tests for AWS service classes."""

from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError

from src.aws_classes import Alb, DynamoDB, Ec2
from src.models import AWSProfile, db

@pytest.fixture
def aws_profile(app):
    """Create a test AWS profile."""
    with app.app_context():
        profile = AWSProfile(
            name='test-profile',
            aws_access_key_id='test-key',
            aws_secret_access_key='test-secret',
            aws_region='us-east-1',
            is_active=True
        )
        db.session.add(profile)
        db.session.commit()
        yield profile
        db.session.delete(profile)
        db.session.commit()

@patch('boto3.Session.client')
def test_alb_describe_target_groups(mock_boto3_client, app, _):  # pylint: disable=unused-argument
    """Test ALB target groups description."""
    # Mock response data
    mock_response = {
        'TargetGroups': [{
            'TargetGroupName': 'test-tg',
            'Protocol': 'HTTP',
            'Port': 80,
            'VpcId': 'vpc-123',
            'TargetType': 'instance',
            'LoadBalancerArns': ['arn:aws:123'],
            'HealthCheckProtocol': 'HTTP',
            'HealthCheckPort': '80',
            'HealthCheckPath': '/health',
            'Matcher': {'HttpCode': '200'}
        }]
    }

    # Setup mock
    mock_client = Mock()
    mock_client.describe_target_groups.return_value = mock_response
    mock_boto3_client.return_value = mock_client

    # Test
    with app.app_context():
        alb = Alb()
        result = alb.describe_target_groups()

    assert len(result) == 1
    assert result[0]['Name'] == 'test-tg'
    assert result[0]['Protocol'] == 'HTTP'
    assert result[0]['Port'] == 80

@patch('boto3.Session.client')
def test_dynamodb_describe_tables(mock_boto3_client, app, _):  # pylint: disable=unused-argument
    """Test DynamoDB tables description."""
    # Mock response data
    mock_response = {
        'TableNames': ['table1', 'table2']
    }

    # Setup mock
    mock_client = Mock()
    mock_client.list_tables.return_value = mock_response
    mock_boto3_client.return_value = mock_client

    # Test
    with app.app_context():
        dynamodb = DynamoDB()
        result = dynamodb.describe_dynamodb()

    assert len(result) == 2
    assert result[0]['Name'] == 'table1'
    assert result[1]['Name'] == 'table2'

@patch('boto3.Session.client')
def test_ec2_describe_instances(mock_boto3_client, app, _):  # pylint: disable=unused-argument
    """Test EC2 instances description."""
    # Mock response data
    mock_response = {
        'Reservations': [{
            'Instances': [{
                'InstanceId': 'i-123',
                'InstanceType': 't2.micro',
                'VpcId': 'vpc-123',
                'SubnetId': 'subnet-123',
                'SecurityGroups': [{'GroupId': 'sg-123'}],
                'IamInstanceProfile': {'Arn': 'arn:aws:iam::123:role/test-role'},
                'LaunchTime': '2023-01-01T00:00:00Z',
                'PrivateIpAddress': '10.0.0.1',
                'State': {'Name': 'running'},
                'PlatformDetails': 'Linux',
                'Tags': [
                    {'Key': 'Name', 'Value': 'test-instance'},
                    {'Key': 'Env', 'Value': 'test'}
                ]
            }]
        }]
    }

    # Setup mock
    mock_client = Mock()
    mock_client.describe_instances.return_value = mock_response
    mock_boto3_client.return_value = mock_client

    # Test
    with app.app_context():
        ec2 = Ec2()
        result = ec2.describe_ec2()

    assert len(result) == 1
    assert result[0]['Name'] == 'test-instance'
    assert result[0]['Instance Id'] == 'i-123'
    assert result[0]['Instance Type'] == 't2.micro'

@patch('boto3.Session.client')
def test_error_handling(mock_boto3_client, app, _):  # pylint: disable=unused-argument
    """Test AWS error handling."""
    # Setup mock to raise an error
    mock_client = Mock()
    mock_client.describe_instances.side_effect = ClientError(
        error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        operation_name='DescribeInstances'
    )
    mock_boto3_client.return_value = mock_client

    # Test
    with app.app_context():
        ec2 = Ec2()
        with pytest.raises(ClientError):
            ec2.describe_ec2() 