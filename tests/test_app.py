"""Tests for the AWS Inventory Flask application."""

import pytest
from unittest.mock import patch
from botocore.exceptions import ClientError
from app import app, db
from flask import url_for

@pytest.fixture
def client():
    """Test client fixture for Flask application."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg://test_user:test_password@localhost:5432/test_db'
    
    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()

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
    response = client.get('/settings')
    assert response.status_code == 200
    assert b'Version Information' in response.data
    # Version will be 'development' in test environment
    assert b'development' in response.data

@patch('src.aws_classes.Alb.describe_target_groups')
@patch('src.aws_classes.Alb.describe_loadbalancers')
def test_alb_route(mock_lb, mock_tg, client):
    """Test ALB route with mocked AWS responses."""
    # Mock the AWS responses
    mock_tg.return_value = [{'Name': 'test-tg'}]
    mock_lb.return_value = [{'Name': 'test-lb'}]
    
    response = client.get('/alb')
    assert response.status_code == 200

@patch('src.aws_classes.DynamoDB.describe_dynamodb')
def test_dynamodb_route(mock_dynamo, client):
    """Test DynamoDB route with mocked AWS response."""
    # Mock the AWS response
    mock_dynamo.return_value = [{'Name': 'test-table'}]
    
    response = client.get('/dynamodb')
    assert response.status_code == 200

@patch('src.aws_classes.Ec2.describe_ec2')
def test_ec2_route(mock_ec2, client):
    # Mock the AWS response
    mock_ec2.return_value = [{'Name': 'test-instance'}]
    
    response = client.get('/ec2')
    assert response.status_code == 200

@patch('src.aws_classes.AwsLambda.describe_lambda')
def test_lambda_route(mock_lambda, client):
    # Mock the AWS response
    mock_lambda.return_value = [{'Name': 'test-function'}]
    
    response = client.get('/lambda')
    assert response.status_code == 200

@patch('src.aws_classes.Ec2.describe_vpcs')
@patch('src.aws_classes.Ec2.describe_subnets')
def test_networks_route(mock_subnets, mock_vpcs, client):
    # Mock the AWS responses
    mock_vpcs.return_value = [{'VPC Name': 'test-vpc'}]
    mock_subnets.return_value = [{'Subnet Name': 'test-subnet'}]
    
    response = client.get('/networks')
    assert response.status_code == 200

@patch('src.aws_classes.Rds.describe_rds')
def test_rds_route(mock_rds, client):
    # Mock the AWS response
    mock_rds.return_value = [{'Name': 'test-db'}]
    
    response = client.get('/rds')
    assert response.status_code == 200

@patch('src.aws_classes.S3.describe_s3')
def test_s3_route(mock_s3, client):
    # Mock the AWS response
    mock_s3.return_value = [{'Name': 'test-bucket'}]
    
    response = client.get('/s3')
    assert response.status_code == 200

@patch('src.aws_classes.Ec2.describe_security_groups')
@patch('src.aws_classes.Ec2.describe_security_group_rules')
def test_sgs_route(mock_rules, mock_groups, client):
    # Mock the AWS responses
    mock_groups.return_value = [{'Name': 'test-sg'}]
    mock_rules.return_value = [{'Rule Id': 'test-rule'}]
    
    response = client.get('/sgs')
    assert response.status_code == 200

def test_404_error(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404

@patch('src.aws_classes.Ec2.describe_ec2')
def test_aws_error_handling(mock_ec2, client):
    from botocore.exceptions import ClientError
    
    # Mock AWS error
    mock_ec2.side_effect = ClientError(
        error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
        operation_name='DescribeInstances'
    )
    
    response = client.get('/ec2')
    assert response.status_code == 200  # Should still return 200 with error template
    assert b"An error occurred while fetching AWS resources" in response.data 