# -*- coding: utf-8 -*-
import os
from copy import deepcopy

import boto3
import pytest
from moto import mock_aws

from ecr_cleaner import config
from ecr_cleaner.cleaner import ECRCleaner
from ecr_cleaner.manager import ECRManager, ECSManager
from ecr_cleaner.notifier import SlackNotifier
from ecr_cleaner.test.fixtures.test_data import MockDataGenerator

"""Mocked AWS Credentials for moto."""
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = config.AWS_REGION
os.environ["LAMBDA_TASK_ROOT"] = "this"

generator = MockDataGenerator()


@pytest.fixture(scope="function")
def ecr_data():
    return deepcopy(generator.ecr_data)


@pytest.fixture(scope="function")
def ecs_data():
    return deepcopy(generator.ecs_data)


@pytest.fixture(scope="function")
def ecs_data():
    return generator.ecs_data


@pytest.fixture(scope="function")
def slack_notifier():
    slack_token = "fake-token"
    return SlackNotifier(slack_token)


@pytest.fixture(scope="function")
def ecr_manager(monkeypatch, ecr_data):
    with mock_aws():
        ecr_manager = ECRManager(
            ecr_client=boto3.client("ecr", region_name=config.AWS_REGION)
        )

        for repository_name, images_details in ecr_data.items():
            ecr_manager.ecr_client.create_repository(repositoryName=repository_name)

            for image in images_details["images"]:
                ecr_manager.ecr_client.put_image(
                    repositoryName=repository_name,
                    imageManifest=image["imageManifest"],
                    imageDigest=image["imageDigest"],
                    imageManifestMediaType="application/vnd.docker.distribution.manifest.v2+json",
                    imageTag=image["imageTag"],
                )

        def mock_describe_images(*args, **kwargs):
            image_details = []
            repo_name = kwargs.get("repositoryName")

            for image_data in ecr_data[repo_name]["images"]:
                image_details.append(
                    {
                        "imagePushedAt": image_data["imagePushedAt"],
                        "imageDigest": image_data["imageDigest"],
                        "imageTag": image_data["imageTag"],
                        "imageTags": image_data["imageTags"],
                    }
                )
            return {"imageDetails": image_details}

        monkeypatch.setattr(
            ecr_manager.ecr_client, "describe_images", mock_describe_images
        )

        yield ecr_manager


@pytest.fixture(scope="function")
def ecs_manager(ecs_data):
    """
    Creates ECS Cluster with mock_aws , so we can use it , ideally
    we should use all data coming from mock_task_data, but we are not there yet
    """
    with mock_aws():
        # Create VPC, needed for ecs cluster
        ec2_client = boto3.client("ec2", region_name=config.AWS_REGION)
        vpc_response = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc_response["Vpc"]["VpcId"]

        subnet_response = ec2_client.create_subnet(
            CidrBlock="10.0.1.0/24", VpcId=vpc_id
        )
        subnet_id = subnet_response["Subnet"]["SubnetId"]

        security_group_response = ec2_client.create_security_group(
            GroupName="mock-sg", Description="mock security group", VpcId=vpc_id
        )
        security_group_id = security_group_response["GroupId"]

        ecs_manager = ECSManager(
            ecs_client=boto3.client("ecs", region_name=config.AWS_REGION)
        )

        for cluster_name, tasks in ecs_data.items():
            ecs_manager.ecs_client.create_cluster(clusterName=cluster_name)

            # Create task definition
            for task in tasks:

                task_definition = ecs_manager.ecs_client.register_task_definition(
                    family=task["taskId"],
                    containerDefinitions=task["containerDefinitions"],
                    requiresCompatibilities=["FARGATE"],
                    networkMode="awsvpc",
                    memory="512",
                    cpu="256",
                )

                task_definition_arn = task_definition["taskDefinition"][
                    "taskDefinitionArn"
                ]

                running_task = ecs_manager.ecs_client.run_task(
                    cluster=cluster_name,
                    taskDefinition=task_definition_arn,
                    count=1,
                    launchType="FARGATE",
                    networkConfiguration={
                        "awsvpcConfiguration": {
                            "subnets": [subnet_id],
                            "securityGroups": [security_group_id],
                            "assignPublicIp": "ENABLED",
                        }
                    },
                )

                if task["isRunning"]:
                    running_task["tasks"][0]["lastStatus"] = "RUNNING"
                else:
                    running_task["tasks"][0]["lastStatus"] = "STOPPED"

        yield ecs_manager


@pytest.fixture(scope="function")
def ecr_cleaner(ecr_manager, ecs_manager):
    with mock_aws():
        ecr_cleaner = ECRCleaner(aws_region=config.AWS_REGION, slack_token="fake-token")
        ecr_cleaner.ecr_manager = ecr_manager
        ecr_cleaner.ecs_manager = ecs_manager
        yield ecr_cleaner
