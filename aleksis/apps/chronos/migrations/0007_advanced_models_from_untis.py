# Generated by Django 3.0.3 on 2020-03-08 20:16

import colorfield.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chronos', '0006_extended_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='Absence',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False)),
                ('date_start', models.DateField(null=True, verbose_name='Effective start date of absence')),
                ('date_end', models.DateField(null=True, verbose_name='Effective end date of absence')),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Absence',
                'ordering': ['date_start'],
            },
        ),
        migrations.CreateModel(
            name='AbsenceReason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False)),
                ('title', models.CharField(max_length=50, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Absence reason',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False)),
                ('title', models.CharField(max_length=50, verbose_name='Title')),
                ('date_start', models.DateField(null=True, verbose_name='Effective start date of event')),
                ('date_end', models.DateField(null=True, verbose_name='Effective end date of event')),
                ('timefrom', models.DateTimeField(null=True, verbose_name='Effective start time of event')),
                ('timeto', models.DateTimeField(null=True, verbose_name='Effective end time of event')),
            ],
            options={
                'verbose_name': 'Events',
                'ordering': ['date_start'],
            },
        ),
        migrations.CreateModel(
            name='Exam',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False)),
                ('date', models.DateField(null=True, verbose_name='Date of exam')),
                ('title', models.CharField(max_length=50, verbose_name='Title')),
                ('comment', models.TextField(verbose_name='Comment', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Exam',
                'ordering': ['date'],
            },
        ),
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False)),
                ('title', models.CharField(max_length=50, verbose_name='Title of the holidays')),
                ('date_start', models.DateField(null=True, verbose_name='Effective start date of holidays')),
                ('date_end', models.DateField(null=True, verbose_name='Effective end date of holidays')),
                ('comments', models.TextField(verbose_name='Comments', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Holiday',
                'ordering': ['date_start'],
            },
        ),
        migrations.CreateModel(
            name='SupervisionArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('extended_data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, editable=False)),
                ('short_name', models.CharField(max_length=10, verbose_name='Short name')),
                ('name', models.CharField(max_length=50, verbose_name='Long name')),
                ('colour_fg', colorfield.fields.ColorField(default='#000000', max_length=18)),
                ('colour_bg', colorfield.fields.ColorField(default='#FFFFFF', max_length=18)),
            ],
            options={
                'verbose_name': 'Supervision areas',
                'ordering': ['name'],
            },
        ),
        migrations.AddIndex(
            model_name='holiday',
            index=models.Index(fields=['date_start', 'date_end'], name='chronos_hol_date_st_a47004_idx'),
        ),
        migrations.AddField(
            model_name='exam',
            name='lesson',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exams', to='chronos.Lesson'),
        ),
        migrations.AddField(
            model_name='exam',
            name='periodfrom',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='chronos.TimePeriod', verbose_name='Effective start period of exam'),
        ),
        migrations.AddField(
            model_name='exam',
            name='periodto',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='chronos.TimePeriod', verbose_name='Effective end period of exam'),
        ),
        migrations.AddField(
            model_name='event',
            name='absence_reason',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='absence_reason', to='chronos.AbsenceReason', verbose_name='Absence reason'),
        ),
        migrations.AddField(
            model_name='event',
            name='teachers',
            field=models.ManyToManyField(related_name='events', to='core.Person', verbose_name='Teachers'),
        )
        migrations.AddField(
            model_name='event',
            name='groups',
            field=models.ManyToManyField(related_name='group', to='core.Group', verbose_name='Groups'),
        ),
        migrations.AddField(
            model_name='event',
            name='periodfrom',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='chronos.TimePeriod', verbose_name='Effective start period of event'),
        ),
        migrations.AddField(
            model_name='event',
            name='periodto',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='chronos.TimePeriod', verbose_name='Effective end period of event'),
        ),
        migrations.AddField(
            model_name='event',
            name='rooms',
            field=models.ManyToManyField(related_name='events', to='chronos.Room', verbose_name='Rooms'),
        ),
        migrations.AddField(
            model_name='absence',
            name='periodfrom',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='chronos.TimePeriod', verbose_name='Effective start period of absence'),
        ),
        migrations.AddField(
            model_name='absence',
            name='periodto',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='chronos.TimePeriod', verbose_name='Effective end period of absence'),
        ),
        migrations.AddField(
            model_name='absence',
            name='person',
            field=models.ManyToManyField(related_name='absences', to='core.Person'),
        ),
        migrations.AddField(
            model_name='absence',
            name='reason',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='absences', to='chronos.AbsenceReason'),
        ),
        migrations.AddIndex(
            model_name='exam',
            index=models.Index(fields=['date'], name='chronos_exa_date_5ba442_idx'),
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['periodfrom', 'periodto', 'date_start', 'date_end'], name='chronos_eve_periodf_56eb18_idx'),
        ),
        migrations.AddIndex(
            model_name='absence',
            index=models.Index(fields=['date_start', 'date_end'], name='chronos_abs_date_st_337ff5_idx'),
        ),
    ]
