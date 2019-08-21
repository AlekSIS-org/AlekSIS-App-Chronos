# Generated by Django 2.2.4 on 2019-08-21 14:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_person_primary_group'),
        ('chronos', '0002_make_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonSubstitution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='chronos.Room')),
                ('subject', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lesson_substitutions', to='chronos.Subject')),
                ('teachers', models.ManyToManyField(related_name='lesson_substitutions', to='core.Person')),
            ],
        ),
        migrations.AddField(
            model_name='lessonperiod',
            name='substitution',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lesson_period', to='chronos.LessonSubstitution'),
        ),
    ]
