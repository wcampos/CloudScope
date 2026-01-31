"""Profile-related helpers (session token resolution, etc.)."""
import json
import logging

import boto3

from schemas import ProfileCreate

logger = logging.getLogger(__name__)


def resolve_session_token(data: ProfileCreate) -> str | None:
    """Resolve aws_session_token from form-like payload (role_type, role_name, etc.)."""
    if data.role_type == "existing":
        if not data.role_name:
            raise ValueError("Role name is required when using an existing role")
        temp_session = boto3.Session(
            aws_access_key_id=data.aws_access_key_id,
            aws_secret_access_key=data.aws_secret_access_key,
            region_name=data.aws_region,
        )
        sts_client = temp_session.client("sts")
        account_id = sts_client.get_caller_identity()["Account"]
        role_config = {
            "RoleArn": f"arn:aws:iam::{account_id}:role/{data.role_name}",
            "RoleSessionName": "aws_inventory_session",
        }
        return json.dumps(role_config)

    if data.role_type == "custom" and data.aws_session_token:
        raw = data.aws_session_token
        try:
            role_config = json.loads(raw)
            if isinstance(role_config, dict) and "RoleArn" in role_config:
                if not role_config["RoleArn"].startswith("arn:aws:iam::"):
                    raise ValueError("Invalid role ARN format")
                if not role_config.get("RoleSessionName"):
                    role_config["RoleSessionName"] = "aws_inventory_session"
                return json.dumps(role_config)
        except json.JSONDecodeError:
            pass
        return raw

    return data.direct_session_token
