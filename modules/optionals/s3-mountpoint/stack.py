from typing import Any, Optional

import cdk_nag
from aws_cdk import Aspects, Stack, CfnJson, Aws
from aws_cdk import aws_eks as eks
from aws_cdk import aws_iam as iam
from aws_cdk.aws_s3_assets import Asset
from constructs import Construct


class S3Mountpoint(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        namespace: str,
        cluster_name: str,
        oidc_provider_arn: str,
        eks_master_role_arn: str,
        **kwargs: Optional[Any],
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        eks_cluster = eks.Cluster.from_cluster_attributes(
            self,
            "EKSCluster",
            cluster_name=cluster_name,
            kubectl_role_arn=eks_master_role_arn,
        )

        oidc_provider_id = oidc_provider_arn.split("/")[-1]
        oidc_provider = f"oidc.eks.{Aws.REGION}.amazonaws.com/id/{oidc_provider_id}"
        self.service_account_name = "s3-mountpoint-sa"
        self.service_account_role = iam.Role(
            self,
            "S3MountpointServiceAccountRole",
            role_name="s3-mountpoint-role",
            assumed_by=iam.PrincipalWithConditions(
                iam.WebIdentityPrincipal(oidc_provider_arn),
                conditions={
                    "StringEquals": CfnJson(
                        self,
                        "ServiceAccountRoleTrustPolicy",
                        value={
                            f"{oidc_provider}:aud": "sts.amazonaws.com",
                            f"{oidc_provider}:sub": f"system:serviceaccount:{namespace}:{self.service_account_name}",
                        },
                    ),
                },
            ),
        )

        self.service_account_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:*",
                ],
                resources=["*"],
            )
        )

        self.local_helm_chart = Asset(
            self,
            "Chart",
            path="helm",
        )

        # Deploy the S3 mountpoint
        s3_mountpoint_chart = eks_cluster.add_helm_chart(
            "s3-mountpoint",
            chart_asset=self.local_helm_chart,
            namespace=namespace,
            values={
                "serviceAccount": {
                    "create": False,
                    "name": self.service_account_name,
                }
            },
        )

        s3_mountpoint_chart.node.add_dependency(self.service_account_role)

        # cdk_nag.NagSuppressions.add_resource_suppressions(
        #     self.service_account_role,
        #     [
        #         cdk_nag.NagPackSuppression(
        #             id="AwsSolutions-IAM4",
        #             reason="Lambda basic execution role allowing for cloudwatch logs",
        #         )
        #     ],
        # )

        # cdk_nag.NagSuppressions.add_stack_suppressions(
        #     self,
        #     [
        #         cdk_nag.NagPackSuppression(
        #             id="AwsSolutions-IAM5",
        #             reason="This is s3 mountpoint application. This service account should get permission to execute all S3 api calls",
        #         )
        #     ],
        # )

        # Aspects.of(self).add(cdk_nag.AwsSolutionsChecks())
