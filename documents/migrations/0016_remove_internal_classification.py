from django.db import migrations, models


def internal_to_confidential(apps, schema_editor):
    # "Internal" records were already hidden from staff, so Confidential keeps them hidden.
    Document = apps.get_model("documents", "Document")
    Document.objects.filter(classification="INTERNAL").update(classification="CONFIDENTIAL")


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0015_documentfolder_visibility'),
    ]

    operations = [
        migrations.RunPython(internal_to_confidential, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='document',
            name='classification',
            field=models.CharField(choices=[('PUBLIC', 'Public'), ('CONFIDENTIAL', 'Confidential')], default='CONFIDENTIAL', max_length=12),
        ),
    ]
