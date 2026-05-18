# Generated for ACM Training OJ MVP.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Problem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("description", models.TextField()),
                ("input_description", models.TextField()),
                ("output_description", models.TextField()),
                ("samples", models.JSONField(default=list, help_text="[{input: str, output: str}]")),
                ("time_limit_ms", models.PositiveIntegerField(default=1000)),
                ("memory_limit_mb", models.PositiveIntegerField(default=256)),
                ("is_public", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="TestCase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField()),
                ("input_file", models.CharField(max_length=512)),
                ("output_file", models.CharField(max_length=512)),
                ("score", models.PositiveIntegerField(default=0)),
                ("is_sample", models.BooleanField(default=False)),
                ("problem", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="test_cases", to="problems.problem")),
            ],
            options={
                "ordering": ["problem_id", "order"],
                "unique_together": {("problem", "order")},
            },
        ),
    ]
