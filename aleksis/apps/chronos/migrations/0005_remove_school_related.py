# Generated by Django 3.0.2 on 2020-01-10 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_create_admin_user'),
        ('chronos', '0004_room_name_not_unique'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lesson',
            name='school',
        ),
        migrations.RemoveField(
            model_name='lessonperiod',
            name='school',
        ),
        migrations.AlterField(
            model_name='lesson',
            name='teachers',
            field=models.ManyToManyField(related_name='lessons_as_teacher', to='core.Person'),
        ),
        migrations.AlterField(
            model_name='room',
            name='short_name',
            field=models.CharField(max_length=10, unique=True, verbose_name='Short name, e.g. room number'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='abbrev',
            field=models.CharField(max_length=10, unique=True, verbose_name='Abbreviation of subject in timetable'),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.CharField(max_length=30, unique=True, verbose_name='Long name of subject'),
        ),
        migrations.AlterUniqueTogether(
            name='lessonsubstitution',
            unique_together={('lesson_period', 'week')},
        ),
        migrations.AlterUniqueTogether(
            name='room',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='subject',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='timeperiod',
            unique_together={('weekday', 'period')},
        ),
        migrations.RemoveField(
            model_name='lessonsubstitution',
            name='school',
        ),
        migrations.RemoveField(
            model_name='room',
            name='school',
        ),
        migrations.RemoveField(
            model_name='subject',
            name='school',
        ),
        migrations.RemoveField(
            model_name='timeperiod',
            name='school',
        ),
    ]