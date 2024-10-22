# -*- coding: utf-8 -*-
import logging

import boto3


class ECSManager:

    def __init__(self, ecs_client):
        self.ecs_client = ecs_client

    def get_running_task_images(self):
        images_in_use = set()

        try:
            clusters = self.ecs_client.list_clusters()["clusterArns"]

            for cluster in clusters:
                tasks = self.ecs_client.list_tasks(
                    cluster=cluster, desiredStatus="RUNNING"
                )["taskArns"]
                if tasks:
                    task_descriptions = self.ecs_client.describe_tasks(
                        cluster=cluster, tasks=tasks
                    )
                    for task in task_descriptions["tasks"]:
                        task_def_arn = task["taskDefinitionArn"]
                        task_def = self.ecs_client.describe_task_definition(
                            taskDefinition=task_def_arn
                        )
                        container_defs = task_def["taskDefinition"][
                            "containerDefinitions"
                        ]
                        for container in container_defs:
                            images_in_use.add(container["image"])

        except Exception as e:
            logging.error(f"Error fetching running ECS task images: {e}")

        return sorted(images_in_use)
