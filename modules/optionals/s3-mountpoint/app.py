#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import CfnOutput

from stack import S3Mountpoint

deployment_name = os.getenv("ADDF_DEPLOYMENT_NAME", "")
module_name = os.getenv("ADDF_MODULE_NAME", "")
app_prefix = f"addf-{deployment_name}-{module_name}"


def _param(name: str) -> str:
    return f"ADDF_PARAMETER_{name}"


namespace = os.getenv(_param("NAMESPACE"), "default")
cluster_name = os.getenv(_param("EKS_CLUSTER_NAME"))
oidc_provider_arn = os.getenv(_param("OIDC_PROVIDER_ARN"))
eks_master_role_arn = os.getenv(_param("EKS_MASTER_ROLE_ARN"))


environment = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"],
)

app = cdk.App()
stack = S3Mountpoint(
    scope=app,
    construct_id=app_prefix,
    env=environment,
    namespace=namespace,
    cluster_name=cluster_name,
    oidc_provider_arn=oidc_provider_arn,
    eks_master_role_arn=eks_master_role_arn,
)

app.synth()
