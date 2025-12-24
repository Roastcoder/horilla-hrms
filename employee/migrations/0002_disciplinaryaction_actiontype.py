# Generated migration for DisciplinaryAction and Actiontype models

from django.db import migrations, models
import django.db.models.deletion
from horilla.models import upload_path
from base.models import validate_time_format


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actiontype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=50)),
                ('action_type', models.CharField(choices=[('warning', 'Warning'), ('suspension', 'Suspension'), ('dismissal', 'Dismissal')], max_length=30)),
                ('block_option', models.BooleanField(default=False, help_text='If is enabled, employees log in will be blocked based on period of suspension or dismissal.', verbose_name='Enable login block :')),
            ],
            options={
                'verbose_name': 'Action Type',
                'verbose_name_plural': 'Action Types',
            },
        ),
        migrations.CreateModel(
            name='DisciplinaryAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField(max_length=255)),
                ('unit_in', models.CharField(choices=[('days', 'Days'), ('hours', 'Hours')], default='days', max_length=10)),
                ('days', models.IntegerField(default=1, null=True)),
                ('hours', models.CharField(default='00:00', max_length=6, null=True, validators=[validate_time_format])),
                ('start_date', models.DateField(null=True)),
                ('attachment', models.FileField(blank=True, null=True, upload_to=upload_path)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employee.actiontype')),
                ('employee_id', models.ManyToManyField(to='employee.employee', verbose_name='Employees')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]