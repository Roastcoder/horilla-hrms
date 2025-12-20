#!/usr/bin/env python3
"""
Call Attendance System Test Script

This script tests the basic functionality of the call attendance system.
Run this after setting up the system to verify everything works correctly.
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.contrib.auth.models import User
from employee.models import Employee
from attendance.call_attendance_models import (
    CallLog, CallAttendanceConfig, CallAttendance
)
from attendance.call_attendance_services import CallAttendanceService, CallLogService


def test_call_attendance_system():
    """Test the call attendance system functionality"""
    
    print("🧪 Testing Call Attendance System")
    print("=" * 50)
    
    # Test 1: Create Configuration
    print("\n1. Testing Configuration Creation...")
    config, created = CallAttendanceConfig.objects.get_or_create(
        is_active=True,
        defaults={
            'full_day_minutes': 171,
            'half_day_minutes': 121,
            'absent_threshold_minutes': 120,
        }
    )
    print(f"✅ Configuration {'created' if created else 'exists'}: {config}")
    
    # Test 2: Get Active Employee
    print("\n2. Testing Employee Lookup...")
    try:
        employee = Employee.objects.filter(is_active=True).first()
        if not employee:
            print("❌ No active employees found. Please create an employee first.")
            return False
        print(f"✅ Found employee: {employee.get_full_name()}")
    except Exception as e:
        print(f"❌ Error finding employee: {e}")
        return False
    
    # Test 3: Create Call Log
    print("\n3. Testing Call Log Creation...")
    try:
        test_date = date.today() - timedelta(days=1)  # Yesterday
        call_log = CallLogService.create_call_log(
            employee=employee,
            call_date=test_date,
            call_duration_minutes=180,  # 3 hours - should be PRESENT
            call_count=25,
            source="TEST"
        )
        print(f"✅ Call log created: {call_log}")
    except Exception as e:
        print(f"❌ Error creating call log: {e}")
        return False
    
    # Test 4: Calculate Attendance
    print("\n4. Testing Attendance Calculation...")
    try:
        result = CallAttendanceService.calculate_daily_attendance(test_date)
        print(f"✅ Attendance calculated: {result}")
    except Exception as e:
        print(f"❌ Error calculating attendance: {e}")
        return False
    
    # Test 5: Verify Attendance Record
    print("\n5. Testing Attendance Record...")
    try:
        attendance = CallAttendance.objects.get(
            employee_id=employee,
            attendance_date=test_date
        )
        print(f"✅ Attendance record: {attendance.attendance_status} ({attendance.call_duration_minutes} min)")
        
        # Verify status is correct
        expected_status = 'PRESENT'  # 180 minutes should be PRESENT
        if attendance.attendance_status == expected_status:
            print(f"✅ Status calculation correct: {expected_status}")
        else:
            print(f"❌ Status calculation wrong: expected {expected_status}, got {attendance.attendance_status}")
            
    except CallAttendance.DoesNotExist:
        print("❌ Attendance record not found")
        return False
    except Exception as e:
        print(f"❌ Error verifying attendance: {e}")
        return False
    
    # Test 6: Test Permission Check
    print("\n6. Testing Permission System...")
    try:
        # Get a user (admin)
        user = User.objects.filter(is_superuser=True).first()
        if user:
            can_update = CallAttendanceService.can_update_attendance(user)
            print(f"✅ Permission check for admin: {can_update}")
        else:
            print("⚠️  No admin user found to test permissions")
    except Exception as e:
        print(f"❌ Error testing permissions: {e}")
    
    # Test 7: Test Summary
    print("\n7. Testing Employee Summary...")
    try:
        summary = CallAttendanceService.get_employee_attendance_summary(
            employee=employee,
            start_date=test_date,
            end_date=test_date
        )
        print(f"✅ Employee summary: {summary}")
    except Exception as e:
        print(f"❌ Error getting summary: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Call Attendance System Test Completed!")
    print("\nNext Steps:")
    print("1. Access the dashboard: /attendance/call-attendance/call-attendance/")
    print("2. Configure thresholds: /attendance/call-attendance/config/")
    print("3. Setup automated scheduling (see README)")
    print("4. Train TL/Managers on manual updates")
    
    return True


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test call logs
    deleted_logs = CallLog.objects.filter(source="TEST").delete()[0]
    print(f"✅ Deleted {deleted_logs} test call logs")
    
    # Delete test attendance records
    test_date = date.today() - timedelta(days=1)
    deleted_attendance = CallAttendance.objects.filter(
        attendance_date=test_date,
        source='AUTO'
    ).delete()[0]
    print(f"✅ Deleted {deleted_attendance} test attendance records")


if __name__ == "__main__":
    try:
        success = test_call_attendance_system()
        
        # Ask if user wants to cleanup
        if success:
            cleanup_choice = input("\nDo you want to clean up test data? (y/N): ").lower()
            if cleanup_choice == 'y':
                cleanup_test_data()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)