# Generated by Django 2.2.1 on 2019-05-22 14:07

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('timetable', '0011_debuglog'),
    ]

    operations = [
        migrations.AddField(
            model_name='debuglog',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2019, 5, 22, 16, 7, 24, 453531)),
        ),
        migrations.AlterField(
            model_name='debuglog',
            name='filename',
            field=models.FilePathField(match='.*.log', path='/home/wethjo/dev/school-apps/schoolapps/latex',
                                       verbose_name='Dateiname zur Logdatei'),
        ),
    ]
