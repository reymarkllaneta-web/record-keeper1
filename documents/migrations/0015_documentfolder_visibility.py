from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0014_number_records_saved_with_zero'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentfolder',
            name='visibility',
            field=models.CharField(choices=[('PUBLIC', 'Public — everyone can see it'), ('CONFIDENTIAL', 'Confidential — super administrators and administrators only')], default='PUBLIC', max_length=12, verbose_name='Who can see it'),
        ),
    ]
