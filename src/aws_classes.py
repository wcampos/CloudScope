"""AWS service classes for interacting with various AWS resources."""

import logging
from functools import wraps
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError
from src.models import AWSProfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def aws_error_handler(func):
    """Decorator to handle AWS API errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            logger.error("AWS API error in %s: %s", func.__name__, str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error in %s: %s", func.__name__, str(e))
            raise
    return wrapper

class AWSBase:
    def __init__(self, service_name: str):
        self.profile = AWSProfile.get_active_profile()
        if self.profile:
            self.session = boto3.Session(
                aws_access_key_id=self.profile.aws_access_key_id,
                aws_secret_access_key=self.profile.aws_secret_access_key,
                aws_session_token=self.profile.aws_session_token,
                region_name=self.profile.aws_region
            )
            self.client = self.session.client(service_name)
        else:
            raise ValueError("No active AWS profile found")
        
        self.logger = logging.getLogger(f"aws_inventory.{service_name}")

    def _extract_tags(self, tags: List[Dict[str, str]], default: str = 'empty') -> Dict[str, str]:
        result = {'Name': default, 'Environment': default}
        if tags:
            for tag in tags:
                if tag['Key'] == 'Name':
                    result['Name'] = tag['Value']
                elif tag['Key'] == 'Env':
                    result['Environment'] = tag['Value']
        return result

class Alb(AWSBase):
    def __init__(self):
        super().__init__("elbv2")

    @aws_error_handler
    def describe_target_groups(self) -> List[Dict[str, Any]]:
        target_data = self.client.describe_target_groups()
        ilist = []
        
        for target in target_data['TargetGroups']:
            idict = {
                'Name': target['TargetGroupName'],
                'Protocol': target['Protocol'],
                'Port': target['Port'],
                'Type': target['TargetType'],
                'Vpc Id': target['VpcId'],
                'LB Arn': target['LoadBalancerArns'],
                'Health Check Protocol': target['HealthCheckProtocol'],
                'Health Check Port': target['HealthCheckPort'],
                'Health Check Path': target.get('HealthCheckPath', 'unknown'),
                'Health Check HTTP Matcher': target.get('Matcher', {}).get('HttpCode', 'unknown')
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_loadbalancers(self) -> List[Dict[str, Any]]:
        lb_data = self.client.describe_load_balancers()
        ilist = []
        
        for loadbalancer in lb_data['LoadBalancers']:
            idict = {
                'Name': loadbalancer['LoadBalancerName'],
                'Scheme': loadbalancer['Scheme'],
                'State': loadbalancer['State']['Code'],
                'Type': loadbalancer['Type'],
                'IpAddressType': loadbalancer['IpAddressType'],
                'Arn': loadbalancer['LoadBalancerArn'],
                'DNS Name': loadbalancer['DNSName']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class AwsLambda(AWSBase):
    def __init__(self):
        super().__init__("lambda")

    @aws_error_handler
    def describe_lambda(self) -> List[Dict[str, Any]]:
        ld_data = self.client.list_functions()
        ilist = []
        
        for ld_func in ld_data['Functions']:
            idict = {
                'Name': ld_func['FunctionName'],
                'Runtime': ld_func['Runtime'],
                'Handler': ld_func['Handler'],
                'Memory': ld_func['MemorySize'],
                'Storage Size': ld_func['EphemeralStorage']['Size'],
                'Package Type': ld_func['PackageType'],
                'Last Modified': ld_func['LastModified']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class DynamoDB(AWSBase):
    def __init__(self):
        super().__init__("dynamodb")

    @aws_error_handler
    def describe_dynamodb(self) -> List[Dict[str, Any]]:
        dyn_data = self.client.list_tables()
        return [{'Name': table_name} for table_name in dyn_data['TableNames']]

class Ec2(AWSBase):
    def __init__(self):
        super().__init__("ec2")

    @aws_error_handler
    def describe_ec2(self) -> List[Dict[str, Any]]:
        ec2_data = self.client.describe_instances()
        ilist = []
        
        for reservation in ec2_data['Reservations']:
            for instance in reservation['Instances']:
                tags = self._extract_tags(instance.get('Tags', []))
                
                idict = {
                    'Name': tags['Name'],
                    'Environment': tags['Environment'],
                    'Instance Id': instance['InstanceId'],
                    'Instance Type': instance['InstanceType'],
                    'Vpc Id': instance['VpcId'],
                    'Subnet Id': instance['SubnetId'],
                    'Security Group': instance['SecurityGroups'][0]['GroupId'],
                    'IAM Instance profile': instance['IamInstanceProfile']['Arn'].split("/", 1)[-1],
                    'Lauched Time': instance['LaunchTime'],
                    'Private IP': instance['PrivateIpAddress'],
                    'State': instance['State']['Name'],
                    'OS Family': instance['PlatformDetails']
                }
                ilist.append(idict)
                
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_vpcs(self) -> List[Dict[str, Any]]:
        vpc_data = self.client.describe_vpcs()
        ilist = []
        
        for vpc in vpc_data['Vpcs']:
            tags = self._extract_tags(vpc.get('Tags', []))
            
            idict = {
                'VPC Name': tags['Name'],
                'Environment': tags['Environment'],
                'VPC Id': vpc['VpcId'],
                'VPC Cidr Block': vpc['CidrBlock']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['VPC Name'])

    @aws_error_handler
    def describe_subnets(self) -> List[Dict[str, Any]]:
        sn_data = self.client.describe_subnets()
        ilist = []
        
        for subnet in sn_data['Subnets']:
            tags = self._extract_tags(subnet.get('Tags', []))
            
            idict = {
                'Subnet Name': tags['Name'],
                'Environment': tags['Environment'],
                'Subnet Id': subnet['SubnetId'],
                'Subnet Cidr Block': subnet['CidrBlock'],
                'VpcId': subnet['VpcId'],
                'AvailabilityZone': subnet['AvailabilityZone']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Subnet Name'])

    @aws_error_handler
    def describe_security_groups(self) -> List[Dict[str, Any]]:
        sg_data = self.client.describe_security_groups()
        ilist = []
        
        for sec_grp in sg_data['SecurityGroups']:
            idict = {
                'Name': sec_grp['GroupName'],
                'Id': sec_grp['GroupId'],
                'VPC': sec_grp['VpcId'],
                'Description': sec_grp['Description']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_security_group_rules(self) -> List[Dict[str, Any]]:
        rules_data = self.client.describe_security_group_rules()
        ilist = []
        
        for rule in rules_data['SecurityGroupRules']:
            direction = 'Egress' if rule['IsEgress'] else 'Ingress'
            
            idict = {
                'Rule Id': rule['SecurityGroupRuleId'],
                'Security Group': rule['GroupId'],
                'Direction': direction,
                'IP Protocol': rule.get('IpProtocol', 'all'),
                'From Port': rule.get('FromPort', 'all'),
                'To Port': rule.get('ToPort', 'all'),
                'Cidr': rule.get('CidrIpv4', rule.get('CidrIpv6', 'N/A'))
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Rule Id'])

class Rds(AWSBase):
    def __init__(self):
        super().__init__("rds")

    @aws_error_handler
    def describe_rds(self) -> List[Dict[str, Any]]:
        rds_data = self.client.describe_db_instances()
        ilist = []
        
        for rds_instance in rds_data['DBInstances']:
            idict = {
                'Name': rds_instance['DBInstanceIdentifier'],
                'Engine': rds_instance['Engine'],
                'Version': rds_instance['EngineVersion'],
                'Size': rds_instance['DBInstanceClass'],
                'Storage': rds_instance['AllocatedStorage'],
                'Status': rds_instance['DBInstanceStatus'],
                'Endpoint': rds_instance['Endpoint']['Address'],
                'Port': rds_instance['Endpoint']['Port']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class S3(AWSBase):
    def __init__(self):
        super().__init__("s3")

    @aws_error_handler
    def describe_s3(self) -> List[Dict[str, Any]]:
        s3_data = self.client.list_buckets()
        ilist = []
        
        for bucket in s3_data['Buckets']:
            try:
                location = self.client.get_bucket_location(Bucket=bucket['Name'])
                region = location['LocationConstraint'] or 'us-east-1'
            except ClientError:
                region = 'unknown'
            
            idict = {
                'Name': bucket['Name'],
                'Creation Date': bucket['CreationDate'],
                'Region': region
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class CommonAWSServices(AWSBase):
    """Class to handle common AWS services operations"""
    
    def __init__(self):
        super().__init__("ec2")  # We'll use EC2 as the default service
        self.ec2 = Ec2()
        self.rds = Rds()
        self.s3 = S3()
        self.lambda_client = AwsLambda()
        self.dynamodb = DynamoDB()
        self.alb = Alb()

    def get_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all AWS resources"""
        return {
            'EC2 Instances': self.ec2.describe_ec2(),
            'RDS Instances': self.rds.describe_rds(),
            'S3 Buckets': self.s3.describe_s3(),
            'Lambda Functions': self.lambda_client.describe_lambda(),
            'DynamoDB Tables': self.dynamodb.describe_dynamodb(),
            'Load Balancers': self.alb.describe_loadbalancers(),
            'Security Groups': self.ec2.describe_security_groups(),
            'Security Group Rules': self.ec2.describe_security_group_rules()
        }

    def get_network_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get network-related resources"""
        return {
            'VPCs': self.ec2.describe_vpcs(),
            'Subnets': self.ec2.describe_subnets(),
            'Security Groups': self.ec2.describe_security_groups(),
            'Security Group Rules': self.ec2.describe_security_group_rules(),
            'Load Balancers': self.alb.describe_loadbalancers()
        }

    def get_compute_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get compute-related resources"""
        return {
            'EC2 Instances': self.ec2.describe_ec2(),
            'Lambda Functions': self.lambda_client.describe_lambda()
        }

    def get_storage_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get storage-related resources"""
        return {
            'S3 Buckets': self.s3.describe_s3(),
            'RDS Instances': self.rds.describe_rds(),
            'DynamoDB Tables': self.dynamodb.describe_dynamodb()
        }

    def get_service_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get service-related resources"""
        return {
            'Load Balancers': self.alb.describe_loadbalancers(),
            'Target Groups': self.alb.describe_target_groups(),
            'Lambda Functions': self.lambda_client.describe_lambda(),
            'DynamoDB Tables': self.dynamodb.describe_dynamodb()
        }
