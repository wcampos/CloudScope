"""AWS service classes for interacting with various AWS resources."""

import json
import logging
from functools import wraps
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError
from models import AWSProfile

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
    def __init__(self, service_name: str, profile: AWSProfile):
        self.profile = profile
        if not self.profile:
            raise ValueError("No active AWS profile found")

        # Create initial session with user credentials
        self.session = boto3.Session(
            aws_access_key_id=self.profile.aws_access_key_id,
            aws_secret_access_key=self.profile.aws_secret_access_key,
            aws_session_token=self.profile.aws_session_token,
            region_name=self.profile.aws_region
        )

        # Check if role assumption is configured
        if self.profile.aws_session_token:
            try:
                role_config = json.loads(self.profile.aws_session_token)
                if isinstance(role_config, dict) and 'RoleArn' in role_config:
                    # Create STS client
                    sts_client = self.session.client('sts')
                    
                    # Assume the role
                    assumed_role = sts_client.assume_role(
                        RoleArn=role_config['RoleArn'],
                        RoleSessionName=role_config.get('RoleSessionName', 'aws_inventory_session')
                    )
                    
                    # Create new session with temporary credentials
                    self.session = boto3.Session(
                        aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
                        aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
                        aws_session_token=assumed_role['Credentials']['SessionToken'],
                        region_name=self.profile.aws_region
                    )
            except json.JSONDecodeError:
                # If session_token is not JSON, use it as is (for regular session tokens)
                pass
            except Exception as e:
                logger.error("Error assuming role: %s", str(e))
                raise

        self.client = self.session.client(service_name)
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
    def __init__(self, profile: AWSProfile):
        super().__init__("elbv2", profile)

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
    def __init__(self, profile: AWSProfile):
        super().__init__("lambda", profile)

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
    def __init__(self, profile: AWSProfile):
        super().__init__("dynamodb", profile)

    @aws_error_handler
    def describe_dynamodb(self) -> List[Dict[str, Any]]:
        dyn_data = self.client.list_tables()
        return [{'Name': table_name} for table_name in dyn_data['TableNames']]

class Ec2(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("ec2", profile)

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
            idict = {
                'Rule Id': rule['SecurityGroupRuleId'],
                'Group Id': rule['GroupId'],
                'Protocol': rule['IpProtocol'],
                'From Port': rule.get('FromPort', 'all'),
                'To Port': rule.get('ToPort', 'all'),
                'Cidr': rule.get('CidrIpv4', 'unknown'),
                'Description': rule.get('Description', '')
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Rule Id'])

    @aws_error_handler
    def describe_volumes(self) -> List[Dict[str, Any]]:
        volumes_data = self.client.describe_volumes()
        ilist = []
        
        for volume in volumes_data['Volumes']:
            tags = self._extract_tags(volume.get('Tags', []))
            
            idict = {
                'Name': tags['Name'],
                'Environment': tags['Environment'],
                'Volume Id': volume['VolumeId'],
                'Size': f"{volume['Size']} GB",
                'Type': volume['VolumeType'],
                'State': volume['State'],
                'Availability Zone': volume['AvailabilityZone'],
                'Encrypted': volume['Encrypted'],
                'Attachments': [att['InstanceId'] for att in volume['Attachments']] if volume['Attachments'] else []
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_amis(self) -> List[Dict[str, Any]]:
        amis_data = self.client.describe_images(Owners=['self'])
        ilist = []
        
        for ami in amis_data['Images']:
            tags = self._extract_tags(ami.get('Tags', []))
            
            idict = {
                'Name': tags['Name'],
                'Environment': tags['Environment'],
                'AMI Id': ami['ImageId'],
                'State': ami['State'],
                'Architecture': ami['Architecture'],
                'Platform': ami.get('Platform', 'Linux/UNIX'),
                'Creation Date': ami['CreationDate'],
                'Description': ami.get('Description', ''),
                'Root Device Type': ami['RootDeviceType'],
                'Virtualization Type': ami['VirtualizationType']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_snapshots(self) -> List[Dict[str, Any]]:
        snapshots_data = self.client.describe_snapshots(OwnerIds=['self'])
        ilist = []
        
        for snapshot in snapshots_data['Snapshots']:
            tags = self._extract_tags(snapshot.get('Tags', []))
            
            idict = {
                'Name': tags['Name'],
                'Environment': tags['Environment'],
                'Snapshot Id': snapshot['SnapshotId'],
                'Volume Id': snapshot['VolumeId'],
                'Size': f"{snapshot['VolumeSize']} GB",
                'State': snapshot['State'],
                'Progress': snapshot['Progress'],
                'Start Time': snapshot['StartTime'],
                'Description': snapshot.get('Description', ''),
                'Encrypted': snapshot['Encrypted']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class ECS(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("ecs", profile)

    @aws_error_handler
    def describe_clusters(self) -> List[Dict[str, Any]]:
        clusters_data = self.client.describe_clusters()
        ilist = []
        
        for cluster in clusters_data['clusters']:
            idict = {
                'Name': cluster['clusterName'],
                'Status': cluster['status'],
                'Running Tasks': cluster['runningTasksCount'],
                'Pending Tasks': cluster['pendingTasksCount'],
                'Active Services': cluster['activeServicesCount'],
                'Registered Container Instances': cluster['registeredContainerInstancesCount']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_services(self) -> List[Dict[str, Any]]:
        services_data = self.client.list_services()
        ilist = []
        
        for service_arn in services_data['serviceArns']:
            service_details = self.client.describe_services(cluster='default', services=[service_arn])
            service = service_details['services'][0]
            
            idict = {
                'Name': service['serviceName'],
                'Status': service['status'],
                'Desired Count': service['desiredCount'],
                'Running Count': service['runningCount'],
                'Pending Count': service['pendingCount'],
                'Launch Type': service['launchType']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class EKS(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("eks", profile)

    @aws_error_handler
    def describe_clusters(self) -> List[Dict[str, Any]]:
        clusters_data = self.client.list_clusters()
        ilist = []
        
        for cluster_name in clusters_data['clusters']:
            cluster_details = self.client.describe_cluster(name=cluster_name)
            cluster = cluster_details['cluster']
            
            idict = {
                'Name': cluster['name'],
                'Status': cluster['status'],
                'Version': cluster['version'],
                'Endpoint': cluster['endpoint'],
                'Role Arn': cluster['roleArn'],
                'Created At': cluster['createdAt']
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class RDS(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("rds", profile)

    @aws_error_handler
    def describe_rds(self) -> List[Dict[str, Any]]:
        rds_data = self.client.describe_db_instances()
        ilist = []
        for instance in rds_data['DBInstances']:
            endpoint = instance.get('Endpoint') or {}
            idict = {
                'Name': instance['DBInstanceIdentifier'],
                'Engine': instance['Engine'],
                'Status': instance['DBInstanceStatus'],
                'Class': instance['DBInstanceClass'],
                'Storage': instance.get('AllocatedStorage', ''),
                'Multi AZ': instance.get('MultiAZ', False),
                'Public Access': instance.get('PubliclyAccessible', False),
                'Endpoint': endpoint.get('Address', '—'),
                'Port': endpoint.get('Port', '—'),
            }
            ilist.append(idict)
        return sorted(ilist, key=lambda i: i['Name'])

    @aws_error_handler
    def describe_rds_clusters(self) -> List[Dict[str, Any]]:
        """Aurora and other RDS clusters."""
        try:
            data = self.client.describe_db_clusters()
        except Exception as e:
            self.logger.warning("describe_db_clusters: %s", e)
            return []
        ilist = []
        for c in data.get('DBClusters', []):
            ilist.append({
                'Name': c.get('DBClusterIdentifier', ''),
                'Engine': c.get('Engine', ''),
                'Status': c.get('Status', ''),
                'Endpoint': c.get('Endpoint', '—'),
                'Port': c.get('Port', '—'),
            })
        return sorted(ilist, key=lambda i: i['Name'])

class ElastiCache(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("elasticache", profile)

    @aws_error_handler
    def describe_elasticache(self) -> List[Dict[str, Any]]:
        data = self.client.describe_cache_clusters()
        ilist = []
        for c in data.get('CacheClusters', []):
            ilist.append({
                'Name': c.get('CacheClusterId', ''),
                'Engine': c.get('Engine', ''),
                'Status': c.get('CacheClusterStatus', ''),
                'Node Type': c.get('CacheNodeType', ''),
                'Nodes': c.get('NumCacheNodes', 0),
            })
        return sorted(ilist, key=lambda i: i['Name'])


class DocumentDB(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("docdb", profile)

    @aws_error_handler
    def describe_documentdb(self) -> List[Dict[str, Any]]:
        data = self.client.describe_db_clusters()
        ilist = []
        for c in data.get('DBClusters', []):
            ilist.append({
                'Name': c.get('DBClusterIdentifier', ''),
                'Engine': c.get('Engine', ''),
                'Status': c.get('Status', ''),
                'Endpoint': c.get('Endpoint', '—'),
                'Port': c.get('Port', '—'),
            })
        return sorted(ilist, key=lambda i: i['Name'])


class SQS(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("sqs", profile)

    @aws_error_handler
    def describe_queues(self) -> List[Dict[str, Any]]:
        ilist = []
        paginator = self.client.get_paginator("list_queues")
        for page in paginator.paginate():
            for url in page.get("QueueUrls", []):
                name = url.split("/")[-1] if "/" in url else url
                ilist.append({"Name": name, "Queue URL": url})
        return sorted(ilist, key=lambda i: i["Name"])


class SNS(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("sns", profile)

    @aws_error_handler
    def describe_topics(self) -> List[Dict[str, Any]]:
        ilist = []
        paginator = self.client.get_paginator("list_topics")
        for page in paginator.paginate():
            for topic in page.get("Topics", []):
                arn = topic.get("TopicArn", "")
                name = arn.split(":")[-1] if arn else ""
                ilist.append({"Name": name, "Topic ARN": arn})
        return sorted(ilist, key=lambda i: i["Name"])


class CloudFront(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("cloudfront", profile)

    @aws_error_handler
    def describe_distributions(self) -> List[Dict[str, Any]]:
        ilist = []
        data = self.client.list_distributions()
        for d in data.get("DistributionList", {}).get("Items", []):
            ilist.append({
                "Name": d.get("Id", ""),
                "Domain": d.get("DomainName", ""),
                "Status": d.get("Status", ""),
                "Enabled": d.get("Enabled", False),
                "Origin": d.get("Origins", {}).get("Items", [{}])[0].get("DomainName", "—") if d.get("Origins", {}).get("Items") else "—",
            })
        return sorted(ilist, key=lambda i: i["Name"])


class ApiGateway(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("apigateway", profile)

    @aws_error_handler
    def describe_rest_apis(self) -> List[Dict[str, Any]]:
        ilist = []
        paginator = self.client.get_paginator("get_rest_apis")
        for page in paginator.paginate():
            for api in page.get("items", []):
                ilist.append({
                    "Name": api.get("name", ""),
                    "Id": api.get("id", ""),
                    "Description": api.get("description", "—") or "—",
                    "Created": api.get("createdDate", "—"),
                })
        return sorted(ilist, key=lambda i: i["Name"])


class ApiGatewayV2(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("apigatewayv2", profile)

    @aws_error_handler
    def describe_http_apis(self) -> List[Dict[str, Any]]:
        ilist = []
        paginator = self.client.get_paginator("get_apis")
        for page in paginator.paginate():
            for api in page.get("Items", []):
                ilist.append({
                    "Name": api.get("Name", ""),
                    "Api Id": api.get("ApiId", ""),
                    "Protocol": api.get("ProtocolType", "—"),
                    "Endpoint": api.get("ApiEndpoint", "—"),
                })
        return sorted(ilist, key=lambda i: i["Name"])


class S3(AWSBase):
    def __init__(self, profile: AWSProfile):
        super().__init__("s3", profile)

    @aws_error_handler
    def describe_s3(self) -> List[Dict[str, Any]]:
        buckets_data = self.client.list_buckets()
        ilist = []
        
        for bucket in buckets_data['Buckets']:
            try:
                location = self.client.get_bucket_location(Bucket=bucket['Name'])
                region = location['LocationConstraint'] or 'us-east-1'
            except:
                region = 'unknown'
                
            idict = {
                'Name': bucket['Name'],
                'Created': bucket['CreationDate'],
                'Region': region
            }
            ilist.append(idict)
            
        return sorted(ilist, key=lambda i: i['Name'])

class CommonAWSServices:
    """Class to aggregate resources from multiple AWS services."""

    def __init__(self, profile: AWSProfile):
        self.ec2 = Ec2(profile)
        self.rds = RDS(profile)
        self.s3 = S3(profile)
        self.lambda_ = AwsLambda(profile)
        self.dynamodb = DynamoDB(profile)
        self.elasticache = ElastiCache(profile)
        self.documentdb = DocumentDB(profile)
        self.alb = Alb(profile)
        self.ecs = ECS(profile)
        self.eks = EKS(profile)
        self.sqs = SQS(profile)
        self.sns = SNS(profile)
        self.cloudfront = CloudFront(profile)
        self.apigateway = ApiGateway(profile)
        self.apigatewayv2 = ApiGatewayV2(profile)
        self.logger = logging.getLogger("aws_inventory.CommonAWSServices")

    def _safe_get_resources(self, service_name: str, method_name: str) -> List[Dict[str, Any]]:
        """Safely get resources from a service method, handling errors gracefully."""
        try:
            service = getattr(self, service_name)
            method = getattr(service, method_name)
            return method()
        except Exception as e:
            self.logger.error(f"Error fetching {service_name}.{method_name}: {str(e)}")
            return []

    def get_compute_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all compute-related resources."""
        return {
            'EC2 Instances': self._safe_get_resources('ec2', 'describe_ec2'),
            'EC2 Volumes': self._safe_get_resources('ec2', 'describe_volumes'),
            'EC2 AMIs': self._safe_get_resources('ec2', 'describe_amis'),
            'EC2 Snapshots': self._safe_get_resources('ec2', 'describe_snapshots'),
            'ECS Clusters': self._safe_get_resources('ecs', 'describe_clusters'),
            'ECS Services': self._safe_get_resources('ecs', 'describe_services'),
            'EKS Clusters': self._safe_get_resources('eks', 'describe_clusters'),
            'Lambda Functions': self._safe_get_resources('lambda_', 'describe_lambda')
        }

    def get_data_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get data stores: RDS, DynamoDB, DocumentDB."""
        return {
            'RDS Instances': self._safe_get_resources('rds', 'describe_rds'),
            'RDS Clusters (Aurora)': self._safe_get_resources('rds', 'describe_rds_clusters'),
            'DynamoDB Tables': self._safe_get_resources('dynamodb', 'describe_dynamodb'),
            'DocumentDB Clusters': self._safe_get_resources('documentdb', 'describe_documentdb'),
        }

    def get_cache_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get cache systems: ElastiCache."""
        return {
            'ElastiCache Clusters': self._safe_get_resources('elasticache', 'describe_elasticache'),
        }

    def get_storage_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get object/block storage: S3."""
        return {
            'S3 Buckets': self._safe_get_resources('s3', 'describe_s3'),
        }

    def get_messaging_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get messaging and queues: SQS, SNS."""
        return {
            'SQS Queues': self._safe_get_resources('sqs', 'describe_queues'),
            'SNS Topics': self._safe_get_resources('sns', 'describe_topics'),
        }

    def get_network_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all network-related resources."""
        return {
            'VPCs': self._safe_get_resources('ec2', 'describe_vpcs'),
            'Subnets': self._safe_get_resources('ec2', 'describe_subnets'),
            'Security Groups': self._safe_get_resources('ec2', 'describe_security_groups'),
            'Security Group Rules': self._safe_get_resources('ec2', 'describe_security_group_rules')
        }

    def get_cdn_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get CDN: CloudFront."""
        return {
            'CloudFront Distributions': self._safe_get_resources('cloudfront', 'describe_distributions'),
        }

    def get_api_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get API / serverless: API Gateway REST and HTTP APIs."""
        return {
            'API Gateway REST APIs': self._safe_get_resources('apigateway', 'describe_rest_apis'),
            'API Gateway HTTP APIs': self._safe_get_resources('apigatewayv2', 'describe_http_apis'),
        }

    def get_service_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all service-related resources."""
        return {
            'Load Balancers': self._safe_get_resources('alb', 'describe_loadbalancers'),
            'Target Groups': self._safe_get_resources('alb', 'describe_target_groups')
        }

    def get_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all resources from all services."""
        try:
            return {
                **self.get_compute_resources(),
                **self.get_data_resources(),
                **self.get_cache_resources(),
                **self.get_storage_resources(),
                **self.get_network_resources(),
                **self.get_messaging_resources(),
                **self.get_cdn_resources(),
                **self.get_api_resources(),
                **self.get_service_resources()
            }
        except Exception as e:
            self.logger.error(f"Error getting all resources: {str(e)}")
            return {}
