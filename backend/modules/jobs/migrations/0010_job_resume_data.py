from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0009_alter_job_created_at_alter_job_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='resume_data',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
