# ECR Maintainer

This repository holds a module [ecr_cleaner](ecr_cleaner) which is used by both:

- [lambda_function.py](lambda_function.py)
- [run_cleaner.py](run_cleaner.py)

## Overview

The ECR Maintainer is a script designed to help manage Amazon Elastic Container Registry (ECR) repositories by cleaning up unused container images. This helps reduce storage costs and maintain a clean repository without affecting currently running ECS tasks. The script ensures that a minimum number of images are retained and prevents the deletion of recently pushed images.

By default, it looks for **images to keep** based on the following criteria:

- Images currently in use by running tasks in ECS.
- Images that have been pushed in the last 7 days.
- A minimum of 3 images are always kept in the repository.

## AWS Permissions

To run the ECR Cleaner, ensure that the executing role has the following permissions:

- `ecr:ListImages`
- `ecr:DescribeImages`
- `ecr:BatchDeleteImage`
- `ecs:DescribeTasks`
- `ecs:ListTasks`

These permissions are necessary to identify and delete unused images and to check for images in running ECS tasks.

## Environment Variables

These variables and their default values can be found in [config.py](ecr_cleaner/config.py):

| Variable                    | DEFAULT VALUE |
| --------------------------- | ------------- |
| AWS_REGION                  | eu-west-2     |
| SLACK_TOKEN                 | MY_TOKEN      |
| SLACK_CHANNEL               | MY_CHANNEL    |
| KEEP_MIN_IMAGE_COUNT        | 3             |
| KEEP_IMAGES_NEWER_THAN_DAYS | 7             |
| SLACK_MAX_MESSAGE_LENGTH    | 4000          |
| DELETE_ENABLED              | "false"       |
| SLACK_ENABLED               | "false"       |

### Enable Slack Notification

We need to set the following environment variables to enable Slack notifications:

```bash
SLACK_ENABLED=true
SLACK_TOKEN=<Your Slack Token>
SLACK_CHANNEL=<SLACK_CHANNEL_ID>

```

### Enable image deletion

We need to set the following environment variable to enable image deletion:

```bash
DELETE_ENABLED=true
```

#### Example Configuration

```bash
export AWS_REGION=eu-west-2
export SLACK_TOKEN=your-slack-token
export SLACK_CHANNEL=your-slack-channel
export DELETE_ENABLED=true
export SLACK_ENABLED=true

```

## Running Script locally

You can manually comment the line below and script ill only create csv file `to_delete.csv` with list of images it would delete along with repository name.

```python
  # cleaner.run()
```

```bash
$aws sso login
$export AWS_PROFILE=<AWS_PROFILE_NAME>
$python run_cleaner.py
```

OR

```bash
$aws sso login
$AWS_PROFILE=<AWS_PROFILE_NAME> python run_cleaner.py
```

## Lambda Handler

lambda handler

```shell
lambda_function.run_cleaner
```

## Run Test

```bash
$pytest
```

## Troubleshooting

### Common Issues

- _Permission Errors:_ Ensure that the role or profile you're using has the correct permissions for ECR, ECS, and Slack.
- _Slack Notifications Not Working:_ Double-check that your SLACK_TOKEN and SLACK_CHANNEL values are correct. You can test this using the Slack API directly.
- _Image Deletion Not Occurring:_ Make sure that DELETE_ENABLED is set to "true" and that images older than the retention policy (e.g., 7 days) exist in the repository.

## Todo

- add circleci testing
- enable dry run mode so we can collect images to be delete , images to be kept and, images used by running tasks in ecs
- lambda timeout
