# Generated by Django 5.0.2 on 2024-05-18 09:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdminRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_id', models.IntegerField(unique=True)),
                ('role', models.CharField(max_length=255, unique=True)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=128)),
                ('contact_number', models.CharField(max_length=15, unique=True)),
                ('address', models.CharField(max_length=255, unique=True)),
                ('company_name', models.CharField(max_length=255, unique=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='company_logo/')),
                ('status', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_name', models.CharField(max_length=255)),
                ('venue', models.CharField(max_length=255)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('unique_code', models.CharField(default='368afd', editable=False, max_length=6, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('max_admins', models.IntegerField(default=1)),
                ('max_users', models.IntegerField(default=10)),
                ('max_events', models.IntegerField(default=10)),
                ('max_storage', models.CharField(help_text='max_storage in MB', max_length=100)),
                ('validity_period', models.CharField(help_text='Validity period in months', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField()),
                ('subscription_date', models.DateTimeField()),
                ('plan_expired_date', models.DateTimeField()),
                ('admin', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organizations_admin', to='photosharing_app.adminregistration')),
                ('company_name', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='organization_company_name', to='photosharing_app.adminregistration')),
                ('plan_id', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='organizations_plan', to='photosharing_app.adminregistration')),
            ],
        ),
        migrations.CreateModel(
            name='EventImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='event_images/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='photosharing_app.event')),
                ('admin', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='photosharing_app.organization')),
            ],
        ),
        migrations.AddField(
            model_name='event',
            name='created_by',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='photosharing_app.organization'),
        ),
        migrations.AddField(
            model_name='adminregistration',
            name='organization',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='admin_registrations', to='photosharing_app.organization'),
        ),
    ]