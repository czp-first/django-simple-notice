# Generated by Django 4.0.3 on 2022-04-29 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notice', '0006_backlog_creator_backlog_title_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='privatenotice',
            name='content',
        ),
        migrations.RemoveField(
            model_name='privatenotice',
            name='redirect_url',
        ),
        migrations.AddField(
            model_name='privatenotice',
            name='business_type',
            field=models.CharField(default='', max_length=64, verbose_name='business type'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='privatenotice',
            name='data',
            field=models.JSONField(null=True, verbose_name='data'),
        ),
        migrations.AddField(
            model_name='privatenotice',
            name='is_node_done',
            field=models.BooleanField(default=False, verbose_name='completed status'),
        ),
        migrations.AddField(
            model_name='privatenotice',
            name='node',
            field=models.CharField(default='', max_length=64, verbose_name='node'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='privatenotice',
            name='obj_key',
            field=models.CharField(default='', max_length=64, verbose_name='obj key'),
            preserve_default=False,
        ),
    ]