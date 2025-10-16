from django_celery_beat.models import CrontabSchedule, PeriodicTask


PeriodicTask.objects.all().delete()
CrontabSchedule.objects.all().delete()

daily_night_one_schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="1"
)
daily_night_three_schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="3"
)
daily_morning_eight_schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="8"
)
weekly_schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="0", day_of_week="1"
)
every_three_hour_schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="*/3"
)
every_four_hour_schedule, _ = CrontabSchedule.objects.get_or_create(
    minute="0", hour="*/4"
)


# Добавляем задачи
PeriodicTask.objects.get_or_create(
    crontab=weekly_schedule,
    name="Weekly Task",
    task="celery_schedule.tasks.run_everyweek_script",
)
PeriodicTask.objects.get_or_create(
    crontab=daily_night_one_schedule,
    name="Daily Task",
    task="celery_schedule.tasks.run_everyday_script",
)
PeriodicTask.objects.get_or_create(
    crontab=daily_night_three_schedule,
    name="Tags importers activator",
    task="celery_schedule.tasks.run_tag_importers_activator_script",
)
PeriodicTask.objects.get_or_create(
    crontab=daily_morning_eight_schedule,
    name="Search Index",
    task="celery_schedule.tasks.run_search_index_script",
)
