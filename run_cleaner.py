# -*- coding: utf-8 -*-

import csv

from ecr_cleaner import config
from ecr_cleaner.cleaner import ECRCleaner


def write_csv(headers, file_name, data):
    with open(file_name, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)


def cleaner_up():
    cleaner = ECRCleaner(aws_region=config.AWS_REGION, slack_token=config.SLACK_TOKEN)

    images_to_delete = cleaner.images_to_delete

    to_delete = []

    for ec_repo, delete_data in images_to_delete.items():
        for image in delete_data["delete"]:
            to_delete.append([f"{ec_repo}:{image}"])

    write_csv(["ImagesToDelete"], "to_delete.csv", to_delete)

    cleaner.run()
    return {"statusCode": 200, "body": "ECR cleanup completed."}


# Example usage
if __name__ == "__main__":
    cleaner_up()
