# -*- coding: utf-8 -*-
def test_get_running_task_images(ecs_data, ecs_manager):

    images_in_use = ecs_manager.get_running_task_images()

    for cluster_name, tasks in ecs_data.items():
        for task in tasks:
            if task["isRunning"]:
                for container in task["containerDefinitions"]:
                    assert container["image"] in images_in_use

            """
                We can not test, if image is not in the STOPPED task.
                Stopped task may still have the same image in container definition as running task
            """
