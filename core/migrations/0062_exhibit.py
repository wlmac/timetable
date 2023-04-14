# Generated by Django 4.0.10 on 2023-04-14 06:21

import core.models.post
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0061_expo_notif_tokens_support_multiple'),
    ]

    operations = [
        migrations.CreateModel(
            name='Exhibit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('last_modified_date', models.DateTimeField(auto_now=True)),
                ('show_after', models.DateTimeField(help_text='Show this announcement after this time.', verbose_name='Automatically post on')),
                ('title', models.CharField(max_length=64)),
                ('body', models.TextField()),
                ('slug', models.SlugField(unique=True)),
                ('content', models.ImageField(default='featured_image/default.png', upload_to=core.models.post.featured_image_file_path_generator)),
                ('content_description', models.CharField(help_text='Alt text for the featured image e.g. what screen readers tell users', max_length=140)),
                ('is_published', models.BooleanField(default=False)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)ss_authored', to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(blank=True, related_name='%(class)ss', related_query_name='%(class)s', to='core.tag')),
            ],
            options={
                'ordering': ['-created_date'],
            },
        ),
    ]