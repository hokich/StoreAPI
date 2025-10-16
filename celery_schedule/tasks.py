from celery import shared_task


@shared_task
def run_everyweek_script() -> None:
    """Executes the 'everyweek' management script."""
    from django.core.management import call_command

    call_command("runscript", "everyweek")


@shared_task
def run_everyday_script() -> None:
    """Executes the 'everyday' management script."""
    from django.core.management import call_command

    call_command("runscript", "everyday")


@shared_task
def run_tag_importers_activator_script() -> None:
    """Executes the 'tag_importers_activator' management script."""
    from django.core.management import call_command

    call_command("runscript", "tag_importers_activator")


@shared_task
def run_search_index_script() -> None:
    """Executes the 'search_index' management script."""
    from django.core.management import call_command

    call_command("runscript", "search_index")
