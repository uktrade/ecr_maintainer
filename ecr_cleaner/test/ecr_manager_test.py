# -*- coding: utf-8 -*-
import random

import pytest

from ecr_cleaner import config


def test_get_all_repositories(ecr_data, ecr_manager):

    ec_repositories = list(ecr_manager.get_all_repositories())
    ec_repositories_name = [repo["name"] for repo in ec_repositories]
    for ec_repo in ecr_data.keys():
        assert ec_repo in ec_repositories_name
        # Todo: add assert for ec_repo["uri"]


def test_fetch_repository_images(ecr_data, ecr_manager):

    ec_repositories = list(ecr_manager.get_all_repositories())

    for ec_repo in ec_repositories:
        image_data = ecr_manager.fetch_repository_images(
            repository_name=ec_repo["name"]
        )
        mock_image_data = ecr_data[ec_repo["name"]]["images"]

        assert len(image_data) == len(mock_image_data)

        for index in range(0, len(image_data)):
            assert (
                mock_image_data[index]["imagePushedAt"]
                == image_data[index]["imagePushedAt"]
            )
            assert mock_image_data[index]["imageTag"] == image_data[index]["imageTag"]
            assert mock_image_data[index]["imageTags"] == image_data[index]["imageTags"]
            assert (
                mock_image_data[index]["imageDigest"]
                == image_data[index]["imageDigest"]
            )


@pytest.mark.skip("this may be due to moto library but, needs further investigation")
def test_delete_images(ecr_data, ecr_manager):
    # Get all repositories from the ecr_manager
    config.DELETE_ENABLED = True
    ec_repositories = ecr_manager.get_all_repositories()

    for ec_repo in ec_repositories:
        images_to_delete = []

        for i in range(ecr_data[ec_repo]["totalImages"]):
            choice = random.choice([True, False])
            if choice:
                images_to_delete.append(ecr_data[ec_repo]["images"][i]["imageDigest"])

        ecr_manager.delete_images(
            repository_name=ec_repo, images_to_delete=images_to_delete
        )

        response = ecr_manager.ecr_client.describe_images(repositoryName=ec_repo)
        remaining_images = [image["imageDigest"] for image in response["imageDetails"]]

        assert set(images_to_delete).issubset(set(remaining_images)) is False
