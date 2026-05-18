# Generated for ACM Training OJ MVP.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("problems", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Contest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("rule", models.CharField(choices=[("ACM", "ACM"), ("IOI", "IOI")], default="ACM", max_length=8)),
                ("start_at", models.DateTimeField()),
                ("end_at", models.DateTimeField()),
                ("is_public", models.BooleanField(default=False)),
                ("freeze_rank_minutes", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ("participants", models.ManyToManyField(blank=True, related_name="contests", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-start_at"]},
        ),
        migrations.CreateModel(
            name="ContestRankSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("frozen", models.BooleanField(default=False)),
                ("payload", models.JSONField(default=dict)),
                ("contest", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="rank_snapshots", to="contests.contest")),
            ],
        ),
        migrations.CreateModel(
            name="ContestProblem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("alias", models.CharField(help_text="A/B/C...", max_length=8)),
                ("score", models.PositiveIntegerField(default=100)),
                ("order", models.PositiveIntegerField()),
                ("contest", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="contest_problems", to="contests.contest")),
                ("problem", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="problems.problem")),
            ],
            options={
                "ordering": ["contest_id", "order"],
                "unique_together": {("contest", "problem"), ("contest", "alias")},
            },
        ),
    ]
