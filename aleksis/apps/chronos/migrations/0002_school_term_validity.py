# Generated by Django 3.0.7 on 2020-06-27 14:00

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, models


def migrate_lesson(apps, schema_editor):
    Lesson = apps.get_model("chronos", "Lesson")
    ValidityRange = apps.get_model("chronos", "ValidityRange")
    SchoolTerm = apps.get_model("core", "SchoolTerm")

    db_alias = schema_editor.connection.alias

    for lesson in Lesson.objects.using(db_alias).all():
        date_start = lesson.date_start
        date_end = lesson.date_end

        try:
            school_term = SchoolTerm.objects.using(db_alias).get(
                date_start__lte=date_end, date_end__gte=date_start
            )
        except SchoolTerm.DoesNotExist:
            school_term = SchoolTerm.objects.using(db_alias).create(
                date_start=date_start, date_end=date_end
            )

        try:
            validity_range = ValidityRange.objects.using(db_alias).get(
                school_term=school_term,
                date_start__lte=date_end,
                date_end__gte=date_start,
            )
        except ValidityRange.DoesNotExist:
            validity_range = ValidityRange.objects.using(db_alias).create(
                date_start=date_start, date_end=date_end, school_term=school_term
            )

        lesson.validity = validity_range
        lesson.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_auto_20200627_1600"),
        ("sites", "0002_alter_domain_unique"),
        ("chronos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ValidityRange",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "extended_data",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        default=dict, editable=False
                    ),
                ),
                (
                    "name",
                    models.CharField(blank=True, max_length=255, verbose_name="Name"),
                ),
                ("date_start", models.DateField(verbose_name="Start date")),
                ("date_end", models.DateField(verbose_name="End date")),
            ],
            options={
                "verbose_name": "Validity range",
                "verbose_name_plural": "Validity ranges",
            },
        ),
        migrations.AlterModelOptions(
            name="lesson",
            options={
                "ordering": ["validity__date_start", "subject"],
                "verbose_name": "Lesson",
                "verbose_name_plural": "Lessons",
            },
        ),
        migrations.AlterModelOptions(
            name="lessonperiod",
            options={
                "ordering": [
                    "lesson__validity__date_start",
                    "period__weekday",
                    "period__period",
                    "lesson__subject",
                ],
                "verbose_name": "Lesson period",
                "verbose_name_plural": "Lesson periods",
            },
        ),
        migrations.AlterModelOptions(
            name="lessonsubstitution",
            options={
                "ordering": [
                    "lesson_period__lesson__validity__date_start",
                    "week",
                    "lesson_period__period__weekday",
                    "lesson_period__period__period",
                ],
                "verbose_name": "Lesson substitution",
                "verbose_name_plural": "Lesson substitutions",
            },
        ),
        migrations.AlterModelManagers(name="break", managers=[],),
        migrations.AlterModelManagers(name="exam", managers=[],),
        migrations.AlterModelManagers(name="lesson", managers=[],),
        migrations.AlterModelManagers(name="timeperiod", managers=[],),
        migrations.AddField(
            model_name="absence",
            name="school_term",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="core.SchoolTerm",
                verbose_name="Linked school term",
            ),
        ),
        migrations.AddField(
            model_name="break",
            name="school_term",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="core.SchoolTerm",
                verbose_name="Linked school term",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="school_term",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="core.SchoolTerm",
                verbose_name="Linked school term",
            ),
        ),
        migrations.AddField(
            model_name="exam",
            name="school_term",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="core.SchoolTerm",
                verbose_name="Linked school term",
            ),
        ),
        migrations.AddField(
            model_name="extralesson",
            name="school_term",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="core.SchoolTerm",
                verbose_name="Linked school term",
            ),
        ),
        migrations.AddField(
            model_name="validityrange",
            name="school_term",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="validity_ranges",
                to="core.SchoolTerm",
                verbose_name="School term",
            ),
        ),
        migrations.AddField(
            model_name="validityrange",
            name="site",
            field=models.ForeignKey(
                default=1,
                editable=False,
                on_delete=django.db.models.deletion.CASCADE,
                to="sites.Site",
            ),
        ),
        migrations.AddField(
            model_name="lesson",
            name="validity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="chronos.ValidityRange",
                verbose_name="Linked validity range",
                null=True,
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="supervision",
            name="validity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="chronos.ValidityRange",
                verbose_name="Linked validity range",
                null=True,
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="timeperiod",
            name="validity",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to="chronos.ValidityRange",
                verbose_name="Linked validity range",
                null=True,
                blank=True,
            ),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name="validityrange", unique_together={("date_start", "date_end")},
        ),
        migrations.RunPython(migrate_lesson),
        migrations.RemoveIndex(
            model_name="lesson", name="chronos_les_date_st_5ecc62_idx",
        ),
        migrations.RemoveField(model_name="lesson", name="date_end",),
        migrations.RemoveField(model_name="lesson", name="date_start",),
    ]
