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
        migrations.RunSQL(
            "CREATE TABLE IF NOT EXISTS employee_actiontype (id SERIAL PRIMARY KEY, title VARCHAR(50), action_type VARCHAR(30), block_option BOOLEAN DEFAULT FALSE, created_at TIMESTAMP, created_by_id INTEGER, updated_at TIMESTAMP, updated_by_id INTEGER);",
            reverse_sql="DROP TABLE IF EXISTS employee_actiontype;"
        ),
        migrations.RunSQL(
            "CREATE TABLE IF NOT EXISTS employee_disciplinaryaction (id SERIAL PRIMARY KEY, description TEXT, unit_in VARCHAR(10) DEFAULT 'days', days INTEGER DEFAULT 1, hours VARCHAR(6) DEFAULT '00:00', start_date DATE, attachment VARCHAR(100), action_id INTEGER, created_at TIMESTAMP, created_by_id INTEGER, updated_at TIMESTAMP, updated_by_id INTEGER);",
            reverse_sql="DROP TABLE IF EXISTS employee_disciplinaryaction;"
        ),
        migrations.RunSQL(
            "CREATE TABLE IF NOT EXISTS employee_disciplinaryaction_employee_id (id SERIAL PRIMARY KEY, disciplinaryaction_id INTEGER, employee_id INTEGER);",
            reverse_sql="DROP TABLE IF EXISTS employee_disciplinaryaction_employee_id;"
        ),
    ]