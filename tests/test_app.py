import pytest
from unittest.mock import patch
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200

@patch('src.aws_classes.Alb.describe_target_groups')
@patch('src.aws_classes.Alb.describe_loadbalancers')
def test_alb_route(mock_lb, mock_tg, client):
    # Mock the AWS responses
    mock_tg.return_value = [{'Name': 'test-tg'}]
    mock_lb.return_value = [{'Name': 'test-lb'}]
    
    response = client.get('/alb')
    assert response.status_code == 200

@patch('src.aws_classes.DynamoDB.describe_dynamodb')
def test_dynamodb_route(mock_dynamo, client):
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