# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime, timedelta, timezone

import boto3

from ecr_cleaner import config
from ecr_cleaner.manager import ECRManager, ECSManager
from ecr_cleaner.notifier import SlackNotifier


class ECRCleaner:

    def __init__(self, aws_region, slack_token):
        self.ecr_client = None
        self.ecs_client = None
        self.slack_token = slack_token
        self.aws_region = aws_region

        try:
            self.aws_client()
        except Exception as e:
            logging.error(f"Error: Failed to Get Credentials")
            raise e
        self.ecr_manager = ECRManager(self.ecr_client)
        self.ecs_manager = ECSManager(self.ecs_client)

        self.slack_notifier = SlackNotifier(slack_token=self.slack_token)

        self.now = datetime.now(timezone.utc)
        self.keep_images_newer_than_days = self.now - timedelta(
            days=config.KEEP_IMAGES_NEWER_THAN_DAYS
        )

    def aws_client(self):

        if os.getenv("LAMBDA_TASK_ROOT") or os.getenv("RUN_TEST"):
            self.ecr_client = boto3.client("ecr", region_name=self.aws_region)
            self.ecs_client = boto3.client("ecs", region_name=self.aws_region)
        else:
            session = boto3.session.Session(
                profile_name=os.getenv("AWS_PROFILE"), region_name=self.aws_region
            )
            self.ecr_client = session.client("ecr", region_name=self.aws_region)
            self.ecs_client = session.client("ecs", region_name=self.aws_region)

    @property
    def images_to_delete(self):

        running_task_images = self.ecs_manager.get_running_task_images()

        ecr_images_to_delete = {}

        for ec_repo in self.ecr_manager.get_all_repositories():

            images_to_keep = set()
            all_images = set()

            # get repo URI to be used with comparing image being used by running task
            repoUri = ec_repo["uri"]

            repository_images = self.ecr_manager.fetch_repository_images(
                repository_name=ec_repo["name"]
            )

            for image in repository_images:
                image_digest = image["imageDigest"]

                image_tag = None

                if "imageTag" in image.keys():
                    image_tag = image["imageTag"]

                image_tags = None

                if "imageTags" in image.keys():
                    image_tags = image["imageTags"]
                image_pushed_at = image["imagePushedAt"]

                all_images.add(image_digest)

                """ images to keep by age and count """
                if (
                    len(images_to_keep) < config.KEEP_MIN_IMAGE_COUNT
                    or image_pushed_at >= self.keep_images_newer_than_days
                ):
                    images_to_keep.add(image_digest)

                # check images by one or more tags
                if image_tags:
                    for tag in image_tags:
                        full_image = f"{repoUri}:{tag}"
                        if full_image in running_task_images:
                            images_to_keep.add(image_digest)

                # check image with single tag
                if image_tag:
                    full_image = f"{repoUri}:{image_tag}"
                    if full_image in running_task_images:
                        images_to_keep.add(image_digest)

                # this is for checking images which are added in task with digest instead of tags
                # it may or may not have tags but, it still can be added with digest and we need to check for else
                # we may miss an image
                if True:
                    full_image = f"{repoUri}@{image_digest}"
                    if full_image in running_task_images:
                        images_to_keep.add(image_digest)

            images_to_delete = all_images - images_to_keep

            if images_to_delete:
                ecr_images_to_delete[ec_repo["name"]] = dict(
                    totalDelete=len(images_to_delete), delete=images_to_delete
                )

        return ecr_images_to_delete

    def send_slack_notice(self, images_to_delete):

        message = ""
        totalDeleteImagesInAccount = 0

        for ec_repo, delete_data in images_to_delete.items():

            ec_repo_total_delete = delete_data["totalDelete"]

            totalDeleteImagesInAccount += ec_repo_total_delete

            message += f" - {ec_repo}: {ec_repo_total_delete}\n"

        message = f"*Total*: {totalDeleteImagesInAccount}\n" + message

        self.slack_notifier.send_message(message=message)

    def delete_old_images(self, images_to_delete):

        for ec_repo, ec_repo_data in images_to_delete.items():
            self.ecr_manager.delete_images(
                repository_name=ec_repo, images_to_delete=ec_repo_data["delete"]
            )

    def run(self):
        images_to_delete = self.images_to_delete

        if images_to_delete:
            if config.SLACK_ENABLED:
                self.send_slack_notice(images_to_delete=images_to_delete)
            if config.DELETE_ENABLED:
                self.delete_old_images(images_to_delete=images_to_delete)
