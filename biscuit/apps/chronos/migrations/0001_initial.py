# Generated by Django 2.2.3 on 2019-07-16 22:12

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0008_school_person_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_start', models.DateField(null=True, verbose_name='Effective start date of lesson')),
                ('date_end', models.DateField(null=True, verbose_name='Effective end date of lesson')),
                ('groups', models.ManyToManyField(related_name='lessons', to='core.Group')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abbrev', models.CharField(max_length=10, verbose_name='Abbreviation of subject in timetable')),
                ('name', models.CharField(max_length=30, verbose_name='Long name of subject')),
                ('colour_fg', models.CharField(blank=True, max_length=7, validators=[django.core.validators.RegexValidator('#[0-9A-F]{6}')], verbose_name='Foreground colour in timetable')),
                ('colour_bg', models.CharField(blank=True, max_length=7, validators=[django.core.validators.RegexValidator('#[0-9A-F]{6}')], verbose_name='Background colour in timetable')),
            ],
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=10, unique=True, verbose_name='Short name, e.g. room number')),
                ('name', models.CharField(max_length=30, unique=True, verbose_name='Long name')),
            ],
        ),
        migrations.CreateModel(
            name='TimePeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekday', models.PositiveSmallIntegerField(choices=[(0, 'Sunday'), (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday')], verbose_name='Week day')),
                ('period', models.PositiveSmallIntegerField(verbose_name='Number of period')),
                ('time_start', models.TimeField(verbose_name='Time the period starts')),
                ('time_end', models.TimeField(verbose_name='Time the period ends')),
            ],
        ),
        migrations.CreateModel(
            name='LessonPeriod',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chronos.Lesson')),
                ('period', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chronos.TimePeriod')),
                ('room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='chronos.Room')),
            ],
        ),
        migrations.AddField(
            model_name='lesson',
            name='periods',
            field=models.ManyToManyField(related_name='lessons', through='chronos.LessonPeriod', to='chronos.TimePeriod'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='chronos.Subject'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='teachers',
            field=models.ManyToManyField(related_name='lessons', to='core.Person'),
        ),
    ]
