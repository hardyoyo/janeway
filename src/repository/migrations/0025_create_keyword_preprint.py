# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-09-29 11:27
from __future__ import unicode_literals

import core.model_utils
from django.db import migrations, models
import django.db.models.deletion


def migrate_keywords(apps, schema_editor):
    Preprint = apps.get_model('repository', 'Preprint')
    KeywordPreprint = apps.get_model('repository', 'KeywordPreprint')

    for preprint in Preprint.objects.all():
        for i, kw in enumerate(preprint.keywords.all()):
            kw_article, _ = KeywordPreprint.objects.get_or_create(
                keyword=kw,
                preprint=preprint,
                defaults={
                    'order': i,
                }
            )


def demigrate_keywords(apps, schema_editor):
    KeywordPreprint = apps.get_model('submission', 'KeywordArticle')

    for kw_preprint in KeywordPreprint.objects.all():
        kw_preprint.article.keywords.add(kw_preprint.keyword)


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0058_auto_20210812_1254'),
        ('repository', '0024_auto_20210812_1304'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeywordPreprint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=1)),
                ('keyword', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submission.Keyword')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
        migrations.AddField(
            model_name='keywordpreprint',
            name='preprint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repository.Preprint'),
        ),

        # Migrate keywords onto KeywordPreprint before we change Preprint.keywords
        migrations.RunPython(migrate_keywords, reverse_code=demigrate_keywords),

        migrations.RemoveField(
            model_name='preprint',
            name='keywords',
        ),
        migrations.AddField(
            model_name='preprint',
            name='keywords',
            field=models.ManyToManyField(blank=True, null=True, through='repository.KeywordPreprint',
                                         to='submission.Keyword'),
        ),
        migrations.AlterUniqueTogether(
            name='keywordpreprint',
            unique_together=set([('keyword', 'preprint')]),
        ),
    ]
