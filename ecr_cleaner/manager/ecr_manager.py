# -*- coding: utf-8 -*-
import logging

import boto3


class ECRManager:
    def __init__(self, ecr_client):
        self.ecr_client = ecr_client

    def get_all_repositories(self):
        try:
            paginator = self.ecr_client.get_paginator("describe_repositories")
            for repo_page in paginator.paginate():
                for repo in repo_page["repositories"]:
                    yield {"name": repo["repositoryName"], "uri": repo["repositoryUri"]}
        except Exception as e:
            logging.error(f"Error fetching ECR repositories: {e}")

    def fetch_repository_images(self, repository_name):
        try:
            images = []
            paginator = self.ecr_client.get_paginator("describe_images")
            for page in paginator.paginate(repositoryName=repository_name):
                images.extend(page["imageDetails"])
            return images
        except Exception as e:
            logging.error(f"Error fetching ECR images for {repository_name}: {e}")
            return []

    def delete_images(self, repository_name, images_to_delete):
        try:
            image_ids = [
                {"imageDigest": image_digest} for image_digest in images_to_delete
            ]
            logging.info(f"Deleting images: {repository_name} @ {image_ids}")
            self.ecr_client.batch_delete_image(
                repositoryName=repository_name,
                imageIds=image_ids,
            )
        except Exception as e:
            logging.error(f"Error deleting images from {repository_name}: {e}")
