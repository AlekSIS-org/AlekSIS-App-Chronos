# Generated by Django 2.2 on 2019-04-11 10:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('timetable', '0003_auto_20190410_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='hint',
            name='teachers',
            field=models.BooleanField(default=False, verbose_name='Lehrer?'),
        ),
        migrations.AlterField(
            model_name='hint',
            name='classes',
            field=models.ManyToManyField(related_name='hints', to='timetable.HintClass', verbose_name='Klassen'),
        ),
    ]
