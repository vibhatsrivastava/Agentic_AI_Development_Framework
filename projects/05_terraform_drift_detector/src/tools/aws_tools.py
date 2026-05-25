"""AWS cloud resource fetching tools."""

import json
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from langchain_core.tools import tool
from common.utils import get_logger, require_env
from common.rate_limiter import TokenBucketRateLimiter

logger = get_logger(__name__)
rate_limiter = TokenBucketRateLimiter(tokens_per_second=2, bucket_capacity=5)


@tool
def fetch_cloud_resources(resource_ids: str, resource_type: str) -> str:
    """
    Fetch current state of resources from AWS cloud.
    
    Args:
        resource_ids: Comma-separated list of AWS resource IDs (e.g., "i-abc123,i-def456")
        resource_type: Terraform resource type (e.g., "aws_instance")
    
    Returns:
        JSON string with current resource state: {"resource_type": str, "resources": [...]}
    """
    # Parse resource IDs
    if not resource_ids:
        return json.dumps({"error": "No resource IDs provided"})
    
    id_list = [rid.strip() for rid in resource_ids.split(",") if rid.strip()]
    if not id_list:
        return json.dumps({"error": "Invalid resource_ids format (expected comma-separated list)"})
    
    # Get AWS credentials
    try:
        aws_access_key_id = require_env("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = require_env("AWS_SECRET_ACCESS_KEY")
        aws_region = require_env("AWS_DEFAULT_REGION")
    except EnvironmentError as e:
        return json.dumps({"error": f"AWS credentials not configured: {str(e)}"})
    
    # Route to appropriate fetcher based on resource type
    try:
        if resource_type == "aws_instance":
            return _fetch_ec2_instances(id_list, aws_access_key_id, 
                                       aws_secret_access_key, aws_region)
        elif resource_type == "aws_db_instance":
            return _fetch_rds_instances(id_list, aws_access_key_id,
                                       aws_secret_access_key, aws_region)
        elif resource_type == "aws_security_group":
            return _fetch_security_groups(id_list, aws_access_key_id,
                                          aws_secret_access_key, aws_region)
        elif resource_type == "aws_s3_bucket":
            return _fetch_s3_buckets(id_list, aws_access_key_id,
                                    aws_secret_access_key, aws_region)
        elif resource_type == "aws_ssm_parameter":
            return _fetch_ssm_parameters(id_list, aws_access_key_id,
                                         aws_secret_access_key, aws_region)
        else:
            return json.dumps({"error": f"Unsupported resource type: {resource_type}"})
    
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "Throttling":
            return json.dumps({"error": "AWS API rate limit exceeded. Retry in a few seconds."})
        elif error_code in ["InvalidInstanceID.NotFound", "InvalidGroup.NotFound"]:
            return json.dumps({"error": f"Resource not found in AWS: {error_code}"})
        return json.dumps({"error": f"AWS API error: {error_code} - {e.response['Error'].get('Message', '')}"})
    except BotoCoreError as e:
        return json.dumps({"error": f"AWS SDK error: {str(e)}"})
    except Exception as e:
        logger.exception("Unexpected error fetching cloud resources")
        return json.dumps({"error": f"Unexpected error: {str(e)}"})


def _fetch_ec2_instances(instance_ids: list[str], access_key: str, 
                        secret_key: str, region: str) -> str:
    """Fetch EC2 instance details from AWS."""
    rate_limiter.acquire()
    
    ec2_client = boto3.client(
        "ec2",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    
    response = ec2_client.describe_instances(InstanceIds=instance_ids)
    
    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            tags_dict = {tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])}
            attributes = {
                "id": instance["InstanceId"],
                "instance_type": instance.get("InstanceType"),
                "ami": instance.get("ImageId"),
                "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
                "vpc_security_group_ids": [sg["GroupId"] for sg in instance.get("SecurityGroups", [])],
                "tags": tags_dict,
                # Optionally add more fields as needed
            }
            instances.append({
                "id": instance["InstanceId"],
                "type": "aws_instance",
                "name": instance.get("Tags", [{}])[0].get("Value", "") if instance.get("Tags") else "",
                "tags": tags_dict,
                "instance_type": instance.get("InstanceType"),
                "ami": instance.get("ImageId"),
                "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
                "vpc_security_group_ids": [sg["GroupId"] for sg in instance.get("SecurityGroups", [])],
                "attributes": attributes
            })
    logger.info(f"Fetched {len(instances)} EC2 instances from AWS")
    result_json = json.dumps({
        "resource_type": "aws_instance",
        "resources": instances
    }, indent=2)
    print("[DEBUG] _fetch_ec2_instances JSON output:\n" + result_json)
    return result_json


def _fetch_ssm_parameters(parameter_names: list[str], access_key: str,
                          secret_key: str, region: str) -> str:
    """Fetch SSM parameter metadata from AWS."""
    rate_limiter.acquire()

    ssm_client = boto3.client(
        "ssm",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    parameters = []
    for name in parameter_names:
        try:
            response = ssm_client.get_parameter(Name=name, WithDecryption=False)
            parameter = response.get("Parameter", {})

            tags_dict = {}
            try:
                tags_response = ssm_client.list_tags_for_resource(
                    ResourceType="Parameter",
                    ResourceId=name,
                )
                tags_dict = {tag["Key"]: tag["Value"] for tag in tags_response.get("Tags", [])}
            except ClientError as e:
                logger.warning(f"Unable to fetch tags for SSM parameter {name}: {e}")

            attributes = {
                "id": parameter.get("Name"),
                "type": parameter.get("Type"),
                "arn": parameter.get("ARN"),
                "description": parameter.get("Description"),
                "key_id": parameter.get("KeyId") if parameter.get("Type") == "SecureString" else None,
                "tags": tags_dict,
            }
            parameters.append({
                "id": parameter.get("Name"),
                "type": "aws_ssm_parameter",
                "name": parameter.get("Name"),
                "tags": tags_dict,
                "attributes": attributes
            })
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterNotFound":
                logger.warning(f"SSM parameter not found: {name}")
            else:
                raise

    logger.info(f"Fetched {len(parameters)} SSM parameters from AWS")
    return json.dumps({
        "resource_type": "aws_ssm_parameter",
        "resources": parameters
    }, indent=2)


def _fetch_rds_instances(db_instance_ids: list[str], access_key: str,
                        secret_key: str, region: str) -> str:
    """Fetch RDS database instance details from AWS."""
    rate_limiter.acquire()
    
    rds_client = boto3.client(
        "rds",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    
    instances = []
    for db_id in db_instance_ids:
        try:
            response = rds_client.describe_db_instances(DBInstanceIdentifier=db_id)
            for db_instance in response.get("DBInstances", []):
                instances.append({
                    "id": db_instance["DBInstanceIdentifier"],
                    "engine": db_instance.get("Engine"),
                    "engine_version": db_instance.get("EngineVersion"),
                    "instance_class": db_instance.get("DBInstanceClass"),
                    "allocated_storage": db_instance.get("AllocatedStorage"),
                    "tags": {tag["Key"]: tag["Value"] for tag in db_instance.get("TagList", [])},
                })
        except ClientError as e:
            if e.response["Error"]["Code"] == "DBInstanceNotFound":
                logger.warning(f"RDS instance not found: {db_id}")
            else:
                raise
    
    logger.info(f"Fetched {len(instances)} RDS instances from AWS")
    return json.dumps({
        "resource_type": "aws_db_instance",
        "resources": instances
    }, indent=2)


def _fetch_security_groups(sg_ids: list[str], access_key: str,
                          secret_key: str, region: str) -> str:
    """Fetch security group details from AWS."""
    rate_limiter.acquire()
    
    ec2_client = boto3.client(
        "ec2",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    
    response = ec2_client.describe_security_groups(GroupIds=sg_ids)
    
    security_groups = []
    for sg in response.get("SecurityGroups", []):
        security_groups.append({
            "id": sg["GroupId"],
            "name": sg.get("GroupName"),
            "description": sg.get("Description"),
            "vpc_id": sg.get("VpcId"),
            "ingress": sg.get("IpPermissions", []),
            "egress": sg.get("IpPermissionsEgress", []),
            "tags": {tag["Key"]: tag["Value"] for tag in sg.get("Tags", [])},
        })
    
    logger.info(f"Fetched {len(security_groups)} security groups from AWS")
    return json.dumps({
        "resource_type": "aws_security_group",
        "resources": security_groups
    }, indent=2)


def _fetch_s3_buckets(bucket_names: list[str], access_key: str,
                     secret_key: str, region: str) -> str:
    """Fetch S3 bucket details from AWS."""
    rate_limiter.acquire()
    
    s3_client = boto3.client(
        "s3",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    
    buckets = []
    for bucket_name in bucket_names:
        try:
            # Get bucket tags
            try:
                tags_response = s3_client.get_bucket_tagging(Bucket=bucket_name)
                tags = {tag["Key"]: tag["Value"] for tag in tags_response.get("TagSet", [])}
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchTagSet":
                    tags = {}
                else:
                    raise
            
            # Get bucket versioning
            versioning_response = s3_client.get_bucket_versioning(Bucket=bucket_name)
            
            buckets.append({
                "id": bucket_name,
                "bucket": bucket_name,
                "region": region,
                "versioning": versioning_response.get("Status", "Disabled"),
                "tags": tags,
            })
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchBucket":
                logger.warning(f"S3 bucket not found: {bucket_name}")
            else:
                raise
    
    logger.info(f"Fetched {len(buckets)} S3 buckets from AWS")
    return json.dumps({
        "resource_type": "aws_s3_bucket",
        "resources": buckets
    }, indent=2)
