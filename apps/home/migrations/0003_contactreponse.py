from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_slider_image'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContactReponse',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu',    models.TextField(verbose_name='Contenu de la réponse')),
                ('envoye_le',  models.DateTimeField(auto_now_add=True)),
                ('message',    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reponses', to='home.contactmessage')),
                ('envoye_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reponses_contact', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name':        'Réponse contact',
                'verbose_name_plural': 'Réponses contact',
                'ordering':            ['envoye_le'],
            },
        ),
    ]
