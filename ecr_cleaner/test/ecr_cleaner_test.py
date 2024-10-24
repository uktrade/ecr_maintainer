# -*- coding: utf-8 -*-
from unittest.mock import call

from ecr_cleaner import config


def test_property_images_to_delete(ecr_cleaner, ecr_data, mocker):
    total_images_to_delete = ecr_cleaner.images_to_delete

    for ec_repo, delete_detail in total_images_to_delete.items():
        total_images = ecr_data[ec_repo]["totalImages"]
        total_images_to_delete = delete_detail["totalDelete"]

        total_images_to_keep = total_images - total_images_to_delete

        """Let us ensure least 3 images or original number of images are kept if they were less than 3"""
        assert (
            total_images_to_keep == total_images
            or total_images_to_keep >= config.KEEP_MIN_IMAGE_COUNT
        )

        images_to_delete = delete_detail["delete"]
        "Let us check and ensure images to be deleted are all older than minimum keep time"
        for image in ecr_data[ec_repo]["images"]:
            if image["imageDigest"] in images_to_delete:
                assert image["daysSincePushed"] >= config.KEEP_IMAGES_NEWER_THAN_DAYS


def test_send_slack_notifier(ecr_cleaner, mocker):

    config.SLACK_ENABLED = True
    mock_send_message = mocker.patch.object(ecr_cleaner.slack_notifier, "send_message")

    mock_delete_images = mocker.patch.object(ecr_cleaner.ecr_manager, "delete_images")

    mock_delete_images.return_value = ecr_cleaner.images_to_delete

    ecr_cleaner.run()

    mock_send_message.assert_called_once()

    config.SLACK_ENABLED = False


def test_delete_old_images(ecr_cleaner, mocker):

    config.DELETE_ENABLED = True
    mock_delete_images = mocker.patch.object(ecr_cleaner.ecr_manager, "delete_images")

    ecr_cleaner.run()

    mock_delete_images.assert_called()

    config.DELETE_ENABLED = False


def test_run(ecr_cleaner, ecr_manager, mocker):

    config.DELETE_ENABLED = True
    config.SLACK_ENABLED = True

    mock_delete_images = mocker.patch.object(ecr_manager, "delete_images")
    mock_send_message = mocker.patch.object(ecr_cleaner.slack_notifier, "send_message")

    images_to_delete = ecr_cleaner.images_to_delete

    ecr_cleaner.run()

    actual_calls = mock_delete_images.mock_calls

    excepted_calls = [
        call(repository_name=repo, images_to_delete=data["delete"])
        for repo, data in images_to_delete.items()
    ]

    assert excepted_calls == actual_calls

    mock_delete_images.assert_called()
    mock_send_message.assert_called_once()

    config.DELETE_ENABLED = False
    config.SLACK_ENABLED = False


def test_delete_old_images_when_delete_is_not_enabled(ecr_cleaner, mocker):

    config.DELETE_ENABLED = False
    mock_delete_images = mocker.patch.object(ecr_cleaner.ecr_manager, "delete_images")

    ecr_cleaner.run()

    assert not mock_delete_images.mock_calls
