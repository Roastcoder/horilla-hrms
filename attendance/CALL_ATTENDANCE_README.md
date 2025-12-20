# Call-Based Auto Attendance System

## Overview

This is a **vendor-independent** call-based automatic attendance system for Horilla HRMS. It calculates employee attendance based on call duration without dependency on external platforms like Neodove.

## Key Features

✅ **Platform Independent** - No dependency on external calling platforms  
✅ **Automatic Calculation** - Daily attendance auto-calculated from call logs  
✅ **Manual Override** - TL/Manager can manually update attendance  
✅ **Full Audit Trail** - Complete history of all manual changes  
✅ **Configurable Thresholds** - Admin-controlled attendance rules  
✅ **Payroll Safe** - Manual updates never overwritten by system  
✅ **Role-Based Access** - Proper permission controls  

---

## Architecture

### Models

1. **CallLog** - Stores call data (duration, count, date)
2. **CallAttendanceConfig** - Configurable attendance thresholds
3. **CallAttendance** - Calculated attendance records
4. **CallAttendanceAudit** - Audit trail for manual updates

### Services

- **CallAttendanceService** - Business logic for attendance calculation
- **CallLogService** - Call log management

### Scheduler

- Automated daily attendance calculation
- Supports Django-Q, Celery, or cron jobs

---

## Installation & Setup

### 1. Database Migration

```bash
python manage.py makemigrations attendance
python manage.py migrate attendance
```

### 2. Configure Attendance Thresholds

Navigate to: **Call Attendance → Configuration**

Set the following thresholds:
- **Full Day**: 171+ minutes (default)
- **Half Day**: 121-170 minutes (default)
- **Absent**: ≤120 minutes (default)

### 3. Setup Automated Calculation

#### Option A: Django-Q (Recommended)

```python
# In your Django shell
from attendance.call_attendance_scheduler import setup_daily_attendance_schedule
setup_daily_attendance_schedule()
```

#### Option B: Cron Job

Add to crontab:
```bash
0 23 * * * cd /path/to/horilla && python manage.py calculate_call_attendance
```

#### Option C: Manual Execution

```bash
# Calculate for today
python manage.py calculate_call_attendance

# Calculate for specific date
python manage.py calculate_call_attendance --date 2024-01-15

# Calculate for last 7 days
python manage.py calculate_call_attendance --days-back 7
```

---

## Usage Workflows

### For Admins

1. **Configure Thresholds**
   - Go to Call Attendance → Configuration
   - Set full day, half day, and absent thresholds
   - Save configuration

2. **Monitor System**
   - View dashboard for daily statistics
   - Check audit trail for manual updates
   - Generate reports

3. **Manage Permissions**
   - Assign "Can manually update call attendance" permission to TL/Managers
   - Regular employees have read-only access

### For Team Leaders / Managers

1. **Manual Attendance Update**
   - Navigate to Call Attendance → Manual Update
   - Select employee and date
   - Enter call duration and count
   - **Provide mandatory reason**
   - Submit

2. **View Audit Trail**
   - Access audit trail to see all manual updates
   - Filter by employee, date range
   - Export for review

### For Employees

1. **View Own Attendance**
   - Navigate to My Attendance
   - See daily call time, calls done, status
   - View source (AUTO/MANUAL)
   - Read reason for manual updates

---

## Data Flow

### Call Log Entry

```
Call Data → CallLog Table
  ↓
Daily Scheduler (11:59 PM)
  ↓
Calculate Attendance Status
  ↓
CallAttendance Table (source=AUTO)
```

### Manual Update

```
TL/Manager Update Request
  ↓
Permission Check
  ↓
Update CallAttendance (source=MANUAL)
  ↓
Create CallAttendanceAudit Record
```

---

## API Integration (Future-Ready)

### Bulk Call Log Upload

```python
from attendance.call_attendance_services import CallLogService

call_data = [
    {
        'employee_id': 1,
        'call_date': date(2024, 1, 15),
        'call_duration_minutes': 180,
        'call_count': 25,
        'source': 'API'
    },
    # ... more records
]

created, updated = CallLogService.bulk_create_call_logs(call_data)
```

### CSV Bulk Upload

Navigate to: **Call Logs → Bulk Upload**

CSV Format:
```csv
employee_id,call_date,call_duration_minutes,call_count
1,2024-01-15,180,25
2,2024-01-15,150,20
```

---

## Permission Matrix

| Role | View Attendance | Manual Update | View Audit | Configure |
|------|----------------|---------------|------------|-----------|
| **Employee** | Own only | ❌ | ❌ | ❌ |
| **Team Leader** | Team | ✅ | ✅ | ❌ |
| **Manager** | Department | ✅ | ✅ | ❌ |
| **Admin** | All | ❌* | ✅ | ✅ |

*Admin manages rules, not individual attendance

---

## Business Rules

### Automatic Calculation

1. Runs daily at 11:59 PM (configurable)
2. Only processes working days (Mon-Sat)
3. Skips Sundays and company holidays
4. **Never overwrites manual entries**

### Manual Updates

1. Requires TL/Manager permission
2. Mandatory reason (min 10 characters)
3. Creates audit record
4. Changes source from AUTO → MANUAL
5. Protected from auto-recalculation

### Attendance Status Logic

```python
if call_minutes >= full_day_minutes:
    status = 'PRESENT'
elif call_minutes >= half_day_minutes:
    status = 'HALF_DAY'
else:
    status = 'ABSENT'
```

---

## Monitoring & Maintenance

### Check System Status

```python
from attendance.call_attendance_scheduler import get_attendance_calculation_status

status = get_attendance_calculation_status()
print(status)
# {
#     'today_records': 50,
#     'yesterday_records': 48,
#     'last_auto_calculation': datetime(...),
#     'status': 'up_to_date'
# }
```

### Cleanup Old Audit Logs

```python
from attendance.call_attendance_scheduler import cleanup_old_audit_logs

# Keep last 90 days
deleted_count = cleanup_old_audit_logs(days_to_keep=90)
```

---

## Troubleshooting

### Attendance Not Calculating

1. Check if configuration is active
2. Verify call logs exist for the date
3. Confirm it's a working day
4. Check scheduler is running
5. Review logs for errors

### Manual Update Fails

1. Verify user has permission
2. Check if reason is provided
3. Ensure date is not in future
4. Confirm employee exists

### Audit Trail Missing

1. Verify manual updates are being made
2. Check database for CallAttendanceAudit records
3. Ensure audit creation is not failing

---

## Security Considerations

1. **Permission-Based Access** - Role-based controls
2. **Audit Trail** - Complete change history
3. **Immutable Audits** - Cannot be modified
4. **Reason Mandatory** - All manual changes documented
5. **No PII in Logs** - Only employee IDs stored

---

## Integration Points

### With Existing Horilla Attendance

- Call attendance is **separate** from machine-based attendance
- Can coexist with biometric/face detection systems
- Independent configuration and workflows

### With Payroll

- Attendance data available for payroll calculation
- Manual updates properly tracked
- Audit trail for compliance

---

## Future Enhancements

- [ ] Mobile app integration
- [ ] Real-time call tracking
- [ ] Advanced analytics dashboard
- [ ] Multi-company support
- [ ] Custom attendance rules per department
- [ ] Integration with VoIP systems
- [ ] Automated notifications

---

## Support

For issues or questions:
1. Check this documentation
2. Review audit logs
3. Contact system administrator
4. Raise ticket in Horilla helpdesk

---

## License

Part of Horilla HRMS - LGPL License

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Compatibility**: Horilla HRMS 1.0+