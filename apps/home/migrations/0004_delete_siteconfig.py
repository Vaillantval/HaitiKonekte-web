from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_contactreponse'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SiteConfig',
        ),
    ]
