"""
Bulk Registration Views
CSV/Excel import for Employees and Admins
"""

import csv
import openpyxl
from io import StringIO, BytesIO
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from datetime import datetime, date
import uuid

from .models import BaseUserModel, UserProfile, AdminProfile, OrganizationProfile
from .serializers import UserProfileSerializer, AdminProfileSerializer
from ServiceShift.models import ServiceShift
from ServiceWeekOff.models import WeekOffPolicy
from LocationControl.models import Location


class BulkEmployeeRegistrationAPIView(APIView):
    """Bulk Employee Registration via CSV/Excel"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, admin_id):
        """Upload and process CSV/Excel file for bulk employee registration"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            admin_profile = get_object_or_404(AdminProfile, user=admin)
            organization = admin_profile.organization
            
            if 'file' not in request.FILES:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "No file uploaded"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            file_extension = file.name.split('.')[-1].lower()
            
            processed = 0
            errors = []
            created_employees = []
            
            if file_extension == 'csv':
                data = self._parse_csv(file)
            elif file_extension in ['xlsx', 'xls']:
                data = self._parse_excel(file)
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Unsupported file format. Please upload CSV or Excel file."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                for row_num, row_data in enumerate(data, start=2):  # Start from 2 (skip header)
                    try:
                        # Required fields
                        email = row_data.get('email', '').strip()
                        username = row_data.get('username', '').strip() or email.split('@')[0]
                        user_name = row_data.get('user_name', '').strip()
                        custom_employee_id = row_data.get('custom_employee_id', '').strip()
                        password = row_data.get('password', '').strip() or str(uuid.uuid4())[:8]
                        
                        if not email or not user_name or not custom_employee_id:
                            errors.append(f"Row {row_num}: Missing required fields (email, user_name, custom_employee_id)")
                            continue
                        
                        # Check if employee already exists
                        if BaseUserModel.objects.filter(email=email).exists():
                            errors.append(f"Row {row_num}: Employee with email {email} already exists")
                            continue
                        
                        if UserProfile.objects.filter(custom_employee_id=custom_employee_id).exists():
                            errors.append(f"Row {row_num}: Employee ID {custom_employee_id} already exists")
                            continue
                        
                        # Create user
                        user = BaseUserModel.objects.create_user(
                            email=email,
                            username=username,
                            password=password,
                            role='user',
                            phone_number=row_data.get('phone_number', '').strip() or None
                        )
                        
                        # Parse dates
                        date_of_birth = self._parse_date(row_data.get('date_of_birth', ''))
                        date_of_joining = self._parse_date(row_data.get('date_of_joining', '')) or date.today()
                        
                        # Create user profile
                        profile_data = {
                            'user': user.id,
                            'user_name': user_name,
                            'admin': admin.id,
                            'organization': organization.id,
                            'custom_employee_id': custom_employee_id,
                            'date_of_birth': date_of_birth,
                            'date_of_joining': date_of_joining,
                            'gender': row_data.get('gender', '').strip() or None,
                            'marital_status': row_data.get('marital_status', '').strip() or None,
                            'blood_group': row_data.get('blood_group', '').strip() or None,
                            'job_title': row_data.get('job_title', '').strip() or None,
                            'designation': row_data.get('designation', '').strip() or None,
                            'aadhaar_number': row_data.get('aadhaar_number', '').strip() or None,
                            'pan_number': row_data.get('pan_number', '').strip() or None,
                            'bank_account_no': row_data.get('bank_account_no', '').strip() or None,
                            'bank_ifsc_code': row_data.get('bank_ifsc_code', '').strip() or None,
                            'bank_name': row_data.get('bank_name', '').strip() or None,
                            'pf_number': row_data.get('pf_number', '').strip() or None,
                            'esic_number': row_data.get('esic_number', '').strip() or None,
                            'emergency_contact_no': row_data.get('emergency_contact_no', '').strip() or None,
                        }
                        
                        serializer = UserProfileSerializer(data=profile_data)
                        if serializer.is_valid():
                            profile = serializer.save()
                            
                            # Assign default shift, week off, location
                            shift_name = row_data.get('shift_name', '').strip()
                            if shift_name:
                                shift = ServiceShift.objects.filter(
                                    admin=admin,
                                    shift_name=shift_name,
                                    is_active=True
                                ).first()
                                if shift:
                                    profile.shifts.add(shift)
                            
                            # Add default shift if none assigned
                            if not profile.shifts.exists():
                                default_shift = ServiceShift.objects.filter(
                                    admin=admin,
                                    is_active=True
                                ).first()
                                if default_shift:
                                    profile.shifts.add(default_shift)
                            
                            # Add default week off
                            default_week_off = WeekOffPolicy.objects.filter(admin=admin).first()
                            if default_week_off:
                                profile.week_offs.add(default_week_off)
                            
                            # Add default location
                            location_name = row_data.get('location_name', '').strip()
                            if location_name:
                                location = Location.objects.filter(
                                    admin=admin,
                                    location_name=location_name,
                                    is_active=True
                                ).first()
                                if location:
                                    profile.locations.add(location)
                            
                            created_employees.append({
                                'email': email,
                                'user_name': user_name,
                                'custom_employee_id': custom_employee_id
                            })
                            processed += 1
                        else:
                            errors.append(f"Row {row_num}: {serializer.errors}")
                            user.delete()  # Clean up
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Successfully created {processed} employees",
                "processed": processed,
                "created_employees": created_employees,
                "errors": errors if errors else None
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _parse_csv(self, file):
        """Parse CSV file"""
        decoded_file = file.read().decode('utf-8')
        io_string = StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        return list(reader)
    
    def _parse_excel(self, file):
        """Parse Excel file"""
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        
        # Get headers from first row
        headers = [cell.value for cell in ws[1]]
        
        data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            row_dict = {}
            for idx, value in enumerate(row):
                if idx < len(headers):
                    row_dict[headers[idx].lower().replace(' ', '_') if headers[idx] else f'col_{idx}'] = str(value) if value else ''
            data.append(row_dict)
        
        return data
    
    def _parse_date(self, date_str):
        """Parse date string to date object"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        if not date_str or date_str.lower() == 'none':
            return None
        
        # Try different date formats
        formats = ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue
        
        return None


class BulkAdminRegistrationAPIView(APIView):
    """Bulk Admin Registration via CSV/Excel"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Upload and process CSV/Excel file for bulk admin registration"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if 'file' not in request.FILES:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "No file uploaded"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            file = request.FILES['file']
            file_extension = file.name.split('.')[-1].lower()
            
            processed = 0
            errors = []
            created_admins = []
            
            if file_extension == 'csv':
                data = self._parse_csv(file)
            elif file_extension in ['xlsx', 'xls']:
                data = self._parse_excel(file)
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Unsupported file format. Please upload CSV or Excel file."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                for row_num, row_data in enumerate(data, start=2):
                    try:
                        email = row_data.get('email', '').strip()
                        username = row_data.get('username', '').strip() or email.split('@')[0]
                        admin_name = row_data.get('admin_name', '').strip()
                        password = row_data.get('password', '').strip() or str(uuid.uuid4())[:8]
                        
                        if not email or not admin_name:
                            errors.append(f"Row {row_num}: Missing required fields (email, admin_name)")
                            continue
                        
                        if BaseUserModel.objects.filter(email=email).exists():
                            errors.append(f"Row {row_num}: Admin with email {email} already exists")
                            continue
                        
                        # Create admin user
                        user = BaseUserModel.objects.create_user(
                            email=email,
                            username=username,
                            password=password,
                            role='admin',
                            phone_number=row_data.get('phone_number', '').strip() or None
                        )
                        
                        # Create admin profile
                        profile_data = {
                            'user': user.id,
                            'admin_name': admin_name,
                            'organization': organization.id
                        }
                        
                        serializer = AdminProfileSerializer(data=profile_data)
                        if serializer.is_valid():
                            serializer.save()
                            created_admins.append({
                                'email': email,
                                'admin_name': admin_name
                            })
                            processed += 1
                        else:
                            errors.append(f"Row {row_num}: {serializer.errors}")
                            user.delete()
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        continue
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Successfully created {processed} admins",
                "processed": processed,
                "created_admins": created_admins,
                "errors": errors if errors else None
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _parse_csv(self, file):
        """Parse CSV file"""
        decoded_file = file.read().decode('utf-8')
        io_string = StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        return list(reader)
    
    def _parse_excel(self, file):
        """Parse Excel file"""
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        
        headers = [cell.value for cell in ws[1]]
        
        data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            row_dict = {}
            for idx, value in enumerate(row):
                if idx < len(headers):
                    row_dict[headers[idx].lower().replace(' ', '_') if headers[idx] else f'col_{idx}'] = str(value) if value else ''
            data.append(row_dict)
        
        return data


class DownloadEmployeeSampleCSVAPIView(APIView):
    """Download sample CSV template for employee bulk registration"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generate and return sample CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="employee_bulk_upload_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'email', 'username', 'user_name', 'custom_employee_id', 'password',
            'phone_number', 'date_of_birth', 'date_of_joining', 'gender',
            'marital_status', 'blood_group', 'job_title', 'designation',
            'aadhaar_number', 'pan_number', 'bank_account_no', 'bank_ifsc_code',
            'bank_name', 'pf_number', 'esic_number', 'emergency_contact_no',
            'shift_name', 'location_name'
        ])
        
        # Add sample row
        writer.writerow([
            'employee@example.com', 'employee1', 'John Doe', 'EMP001', 'password123',
            '9876543210', '1990-01-15', '2024-01-01', 'Male',
            'Single', 'O+', 'Software Engineer', 'Engineer',
            '123456789012', 'ABCDE1234F', '1234567890', 'HDFC0001234',
            'HDFC Bank', 'PF123456', 'ESIC123456', '9876543210',
            'Morning Shift', 'Head Office'
        ])
        
        return response


class DownloadAdminSampleCSVAPIView(APIView):
    """Download sample CSV template for admin bulk registration"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Generate and return sample CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="admin_bulk_upload_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['email', 'username', 'admin_name', 'password', 'phone_number'])
        
        # Add sample row
        writer.writerow(['admin@example.com', 'admin1', 'Admin User', 'password123', '9876543210'])
        
        return response

