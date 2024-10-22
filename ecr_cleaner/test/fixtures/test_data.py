# -*- coding: utf-8 -*-
import hashlib
import random
import string
from datetime import datetime, timedelta, timezone

import pytest


class MockDataGenerator:
    def __init__(self):
        self._ecr_data = self.generate_ecr_data(repo_count=5)
        self._ecs_data = self.generate_ecs_data(ecr_repositories=self._ecr_data)

    def generate_mock_sha256(self):
        """
        Generates a mock but valid SHA-256 digest.
        :return: A valid SHA-256 digest (64 hexadecimal characters).
        """
        # Generate a random string to simulate unique input data for the hash
        random_string = "".join(
            random.choices(string.ascii_letters + string.digits, k=64)
        )

        # Create a SHA-256 digest of the random string
        sha256_hash = hashlib.sha256(random_string.encode("utf-8")).hexdigest()

        return sha256_hash

    def generate_ecr_data(self, repo_count=3, images_per_repo=15, time_range=(1, 20)):
        """
        Generates mock ECR data, including the total number of images and the number of days since they were pushed.
        :param repo_count: Number of repositories to generate.
        :param images_per_repo: Number of images per repository.
        :param time_range: Tuple of (min_days, max_days) for image `pushedAt` time.
        :return: Dictionary containing ECR repository names, image details, total image count, and days since push.
        """
        repositories = {}
        now = datetime.now(timezone.utc)

        for repo_index in range(1, repo_count + 1):
            random_images_per_repo = random.randint(3, images_per_repo)
            repository_name = f"mock-ecr-repo-{repo_index}"
            repositories[repository_name] = {
                "totalImages": random_images_per_repo,
                "images": [],
            }

            for image_index in range(1, random_images_per_repo + 1):
                image_digest = f"sha256:{self.generate_mock_sha256()}"

                bool(random.getrandbits(1))

                # Generate random images without tag can be done this way, however boto3 does not like it and data fails to validate
                # if/when boto3 fix this issue, just un comment following 2 lines to enable test for images without 'imageTag' and 'imageTags'
                # why is it needed ? because it is possible to create image with just digest without any tag
                # image_tag = ""
                # if random_boolean:
                image_tag = f"v{image_index}"

                # Randomly generate image pushedAt times between 1 hour and `time_range` days ago
                time_offset_days = random.randint(time_range[0], time_range[1])
                time_offset_hours = random.randint(0, 23)
                image_pushed_at = now - timedelta(
                    days=time_offset_days, hours=time_offset_hours
                )

                # Calculate the number of days since the image was pushed
                days_since_pushed = (now - image_pushed_at).days
                image_tags = [image_tag]

                for i in range(random.randrange(0, 3)):
                    image_tags.append("".join(string.ascii_lowercase for _ in range(6)))

                # Add image details
                repositories[repository_name]["images"].append(
                    {
                        "imageDigest": image_digest,
                        "imageTag": image_tag,
                        "imageTags": sorted(image_tags),
                        "imagePushedAt": image_pushed_at,
                        "imageManifest": f'{{"schemaVersion": 2, "config": {{"digest": "sha256:{image_digest}-{image_index}"}},"mediaType": "application/vnd.docker.distribution.manifest.v2+json"}}',
                        "daysSincePushed": days_since_pushed,  # Number of days since the image was pushed
                    }
                )

        return repositories

    def generate_ecs_data(
        self,
        ecr_repositories,
        cluster_count=3,
        tasks_per_cluster=3,
        containers_per_task=3,
    ):
        """
        Generates mock ECS data, using images from the provided ECR repositories.
        Some tasks will be randomly marked as RUNNING.
        :param ecr_repositories: List of ECR repositories to use for container images.
        :param cluster_count: Number of ECS clusters to generate.
        :param tasks_per_cluster: Number of tasks per cluster.
        :param containers_per_task: Number of containers per task definition.
        :return: Dictionary containing ECS cluster names, task details, and running status indicators.
        """
        clusters = {}

        for cluster_index in range(1, cluster_count + 1):
            cluster_name = f"mock-ecs-cluster-{cluster_index}"
            clusters[cluster_name] = []

            # Create tasks and assign container definitions
            for task_index in range(1, tasks_per_cluster + 1):
                task_id = f"mock-task-{task_index}"

                # Select a random ECR repository and image for the container
                selected_repo = random.choice(list(ecr_repositories.keys()))
                selected_image = random.choice(
                    ecr_repositories[selected_repo]["images"]
                )
                random_container_per_task = random.randint(1, containers_per_task)
                container_definitions = [
                    {
                        "name": f"mock-container-{i+1}",
                        "image": f"{selected_repo}:{selected_image['imageTag']}",
                        "cpu": 128,
                        "memory": 128,
                    }
                    for i in range(random_container_per_task)
                ]

                # Randomly decide if the task should be marked as RUNNING
                is_running = random.choice([True, False])

                # Add task details with running indicator
                clusters[cluster_name].append(
                    {
                        "taskId": task_id,
                        "totalContainers": random_container_per_task,
                        "containerDefinitions": container_definitions,
                        "isRunning": is_running,  # Indicator for whether this task should be marked as RUNNING
                    }
                )

        return clusters

    @property
    def ecr_data(self):
        return self._ecr_data

    @property
    def ecs_data(self):
        return self._ecs_data
