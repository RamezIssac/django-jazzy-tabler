from django.db import migrations, models


def create_marker(apps, schema_editor):
    apps.get_model("live_demo", "DemoReset").objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DemoReset",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reset_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.RunPython(create_marker, migrations.RunPython.noop),
    ]
