# -*- coding: utf-8 -*-

import csv

import config

from ecr_cleaner.cleaner import ECRCleaner


def cleaner_up():
    cleaner = ECRCleaner(aws_region=config.AWS_REGION, slack_token=config.SLACK_TOKEN)
    images_to_delete = cleaner.images_to_delete

    csv_data = []

    for ec_repo, delete_data in images_to_delete.items():
        for image in delete_data["delete"]:
            csv_data.append([f"{ec_repo}:{image}"])

    with open("delete_images.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)

    cleaner.run()
    return {"statusCode": 200, "body": "ECR cleanup completed."}


# Example usage
if __name__ == "__main__":
    cleaner_up()
