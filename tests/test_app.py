"""Tests for the CloudScope Flask application."""

from unittest.mock import patch
import os

import pytest
from botocore.exceptions import ClientError

from src.models import AWSProfile, db

@pytest.fixture
def active_profile(app):
    """Create an active test AWS profile."""
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

def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200

def test_settings_page(client):
    """Test that the settings page loads successfully."""
    response = client.get('/settings')
    assert response.status_code == 200
    assert b'Application Settings' in response.data
    
def test_version_info(client):
    """Test that version information is displayed on settings page."""
    os.environ['FLASK_ENV'] = 'development'
    response = client.get('/settings')
    assert response.status_code == 200
    assert b'Version Information' in response.data
    assert b'development' in response.data

@patch('src.aws_classes.Alb.describe_target_groups')
@patch('src.aws_classes.Alb.describe_loadbalancers')
def test_alb_route(mock_lb, mock_tg, client, active_profile):
    """Test ALB route with mocked AWS responses."""
    # Mock the AWS responses
    mock_tg.return_value = [{'Name': 'test-tg'}]
    mock_lb.return_value = [{'Name': 'test-lb'}]
    
    response = client.get('/alb')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.DynamoDB.describe_dynamodb')
def test_dynamodb_route(mock_dynamo, client, active_profile):
    """Test DynamoDB route with mocked AWS response."""
    # Mock the AWS response
    mock_dynamo.return_value = [{'Name': 'test-table'}]
    
    response = client.get('/dynamodb')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.Ec2.describe_ec2')
def test_ec2_route(mock_ec2, client, active_profile):
    """Test EC2 route with mocked AWS response."""
    # Mock the AWS response
    mock_ec2.return_value = [{'Name': 'test-instance'}]
    
    response = client.get('/ec2')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.AwsLambda.describe_lambda')
def test_lambda_route(mock_lambda, client, active_profile):
    """Test Lambda route with mocked AWS response."""
    # Mock the AWS response
    mock_lambda.return_value = [{'Name': 'test-function'}]
    
    response = client.get('/lambda')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.Ec2.describe_vpcs')
@patch('src.aws_classes.Ec2.describe_subnets')
def test_networks_route(mock_subnets, mock_vpcs, client, active_profile):
    """Test networks route with mocked AWS responses."""
    # Mock the AWS responses
    mock_vpcs.return_value = [{'VPC Name': 'test-vpc'}]
    mock_subnets.return_value = [{'Subnet Name': 'test-subnet'}]
    
    response = client.get('/networks')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.Rds.describe_rds')
def test_rds_route(mock_rds, client, active_profile):
    """Test RDS route with mocked AWS response."""
    # Mock the AWS response
    mock_rds.return_value = [{'Name': 'test-db'}]
    
    response = client.get('/rds')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.S3.describe_s3')
def test_s3_route(mock_s3, client, active_profile):
    """Test S3 route with mocked AWS response."""
    # Mock the AWS response
    mock_s3.return_value = [{'Name': 'test-bucket'}]
    
    response = client.get('/s3')
    assert response.status_code == 302  # Redirect to dashboard

@patch('src.aws_classes.Ec2.describe_security_groups')
@patch('src.aws_classes.Ec2.describe_security_group_rules')
def test_sgs_route(mock_rules, mock_groups, client, active_profile):
    """Test security groups route with mocked AWS responses."""
    # Mock the AWS responses
    mock_groups.return_value = [{'Name': 'test-sg'}]
    mock_rules.return_value = [{'Rule Id': 'test-rule'}]
    
    response = client.get('/sgs')
    assert response.status_code == 302  # Redirect to dashboard

def test_404_error(client):
    """Test 404 error handler."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert b'Page not found' in response.data

@patch('src.aws_classes.Ec2.describe_ec2')
def test_aws_error_handling(mock_ec2, client, active_profile):
    """Test error handling for AWS API errors."""
    # Mock AWS error
    mock_ec2.side_effect = ClientError(
        error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        operation_name='DescribeInstances'
    )
    
    response = client.get('/ec2')
    assert response.status_code == 302  # Redirect to dashboard 