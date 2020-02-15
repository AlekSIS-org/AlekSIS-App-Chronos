# Generated by Django 3.0.2 on 2020-02-02 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chronos', '0006_extended_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeperiod',
            name='weekday',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], verbose_name='Week day'),
        ),
    ]
