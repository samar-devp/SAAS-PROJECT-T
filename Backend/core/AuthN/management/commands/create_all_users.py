from django.core.management.base import BaseCommand
from django.db import transaction
from AuthN.models import (
    BaseUserModel, 
    SystemOwnerProfile, 
    OrganizationProfile, 
    AdminProfile, 
    UserProfile,
    OrganizationSettings
)
from ServiceShift.models import ServiceShift
from ServiceWeekOff.models import WeekOffPolicy
from TaskControl.models import TaskType
from Expenditure.models import ExpenseCategory
from LocationControl.models import Location


class Command(BaseCommand):
    help = 'Creates all four types of users: SystemOwner, Organization, Admin, and User'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing users and recreate them',
        )

    def handle(self, *args, **options):
        force = options['force']
        self.stdout.write(self.style.SUCCESS('Starting user registration...'))
        
        try:
            with transaction.atomic():
                # 1. Create System Owner
                self.stdout.write('Creating System Owner...')
                system_owner_data = {
                    "user": {
                        "email": "sysowner@gmail.com",
                        "username": "systemowner",
                        "password": "testpassword",
                        "role": "system_owner"
                    },
                    "company_name": "Tech Corp"
                }
                
                # Check if user exists
                existing_system_owner = BaseUserModel.objects.filter(
                    email=system_owner_data["user"]["email"]
                ).first()
                
                if existing_system_owner:
                    if force:
                        self.stdout.write(self.style.WARNING(f'Deleting existing System Owner: {existing_system_owner.email}'))
                        SystemOwnerProfile.objects.filter(user=existing_system_owner).delete()
                        existing_system_owner.delete()
                    else:
                        self.stdout.write(self.style.WARNING(f'System Owner already exists: {existing_system_owner.email}. Use --force to recreate.'))
                        system_owner_user = existing_system_owner
                        system_owner_profile = SystemOwnerProfile.objects.get(user=system_owner_user)
                
                if not existing_system_owner or force:
                    system_owner_user = BaseUserModel.objects.create_user(
                        email=system_owner_data["user"]["email"],
                        username=system_owner_data["user"]["username"],
                        password=system_owner_data["user"]["password"],
                        role="system_owner"
                    )
                    system_owner_profile = SystemOwnerProfile.objects.create(
                        user=system_owner_user,
                        company_name=system_owner_data["company_name"]
                    )
                    self.stdout.write(self.style.SUCCESS(f'[OK] System Owner created: {system_owner_user.email}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'[OK] Using existing System Owner: {system_owner_user.email}'))
                
                # 2. Create Organization
                self.stdout.write('Creating Organization...')
                organization_data = {
                    "user": {
                        "email": "organizati1on1a1a@gmail.com",
                        "username": "systemorganization",
                        "password": "testpassword",
                        "role": "organization"
                    },
                    "organization_name": "Tech Corp"
                }
                
                existing_organization = BaseUserModel.objects.filter(
                    email=organization_data["user"]["email"]
                ).first()
                
                if existing_organization:
                    if force:
                        self.stdout.write(self.style.WARNING(f'Deleting existing Organization: {existing_organization.email}'))
                        OrganizationProfile.objects.filter(user=existing_organization).delete()
                        OrganizationSettings.objects.filter(organization=existing_organization).delete()
                        existing_organization.delete()
                    else:
                        self.stdout.write(self.style.WARNING(f'Organization already exists: {existing_organization.email}. Use --force to recreate.'))
                        organization_user = existing_organization
                        organization_profile = OrganizationProfile.objects.get(user=organization_user)
                
                if not existing_organization or force:
                    organization_user = BaseUserModel.objects.create_user(
                        email=organization_data["user"]["email"],
                        username=organization_data["user"]["username"],
                        password=organization_data["user"]["password"],
                        role="organization"
                    )
                    organization_profile = OrganizationProfile.objects.create(
                        user=organization_user,
                        organization_name=organization_data["organization_name"],
                        system_owner=system_owner_user
                    )
                    # Create OrganizationSettings
                    OrganizationSettings.objects.create(organization=organization_user)
                    self.stdout.write(self.style.SUCCESS(f'[OK] Organization created: {organization_user.email}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'[OK] Using existing Organization: {organization_user.email}'))
                
                # 3. Create Admin
                self.stdout.write('Creating Admin...')
                admin_data = {
                    "user": {
                        "email": "aadminq11a11aq@gmail.com",
                        "username": "systemadmin",
                        "password": "testpassword",
                        "role": "admin"
                    },
                    "admin_name": "Tech Corp Admin"
                }
                
                existing_admin = BaseUserModel.objects.filter(
                    email=admin_data["user"]["email"]
                ).first()
                
                if existing_admin:
                    if force:
                        self.stdout.write(self.style.WARNING(f'Deleting existing Admin: {existing_admin.email}'))
                        AdminProfile.objects.filter(user=existing_admin).delete()
                        ServiceShift.objects.filter(admin=existing_admin).delete()
                        WeekOffPolicy.objects.filter(admin=existing_admin).delete()
                        TaskType.objects.filter(admin=existing_admin).delete()
                        ExpenseCategory.objects.filter(admin=existing_admin).delete()
                        existing_admin.delete()
                    else:
                        self.stdout.write(self.style.WARNING(f'Admin already exists: {existing_admin.email}. Use --force to recreate.'))
                        admin_user = existing_admin
                        admin_profile = AdminProfile.objects.get(user=admin_user)
                
                if not existing_admin or force:
                    admin_user = BaseUserModel.objects.create_user(
                        email=admin_data["user"]["email"],
                        username=admin_data["user"]["username"],
                        password=admin_data["user"]["password"],
                        role="admin"
                    )
                    admin_profile = AdminProfile.objects.create(
                        user=admin_user,
                        admin_name=admin_data["admin_name"],
                        organization=organization_user
                    )
                    # Create default ServiceShift, WeekOffPolicy, TaskType, ExpenseCategory
                    ServiceShift.objects.create(admin=admin_user, organization=organization_user)
                    WeekOffPolicy.objects.create(admin=admin_user, organization=organization_user)
                    WeekOffPolicy.objects.create(admin=admin_user, organization=organization_user)
                    TaskType.objects.create(admin=admin_user, organization=organization_user)
                    ExpenseCategory.objects.create(admin=admin_user, organization=organization_user)
                    self.stdout.write(self.style.SUCCESS(f'[OK] Admin created: {admin_user.email}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'[OK] Using existing Admin: {admin_user.email}'))
                
                # 4. Create User
                self.stdout.write('Creating User...')
                user_data = {
                    "user": {
                        "email": "user111q1aa131@gmail.com",
                        "username": "systemuser",
                        "password": "testpassword",
                        "role": "user"
                    },
                    "user_name": "Tech Corp user"
                }
                
                existing_user = BaseUserModel.objects.filter(
                    email=user_data["user"]["email"]
                ).first()
                
                if existing_user:
                    if force:
                        self.stdout.write(self.style.WARNING(f'Deleting existing User: {existing_user.email}'))
                        UserProfile.objects.filter(user=existing_user).delete()
                        existing_user.delete()
                    else:
                        self.stdout.write(self.style.WARNING(f'User already exists: {existing_user.email}. Use --force to recreate.'))
                        user_user = existing_user
                        user_profile = UserProfile.objects.get(user=user_user)
                
                if not existing_user or force:
                    user_user = BaseUserModel.objects.create_user(
                        email=user_data["user"]["email"],
                        username=user_data["user"]["username"],
                        password=user_data["user"]["password"],
                        role="user"
                    )
                    user_profile = UserProfile.objects.create(
                        user=user_user,
                        user_name=user_data["user_name"],
                        admin=admin_user,
                        organization=organization_user
                    )
                    # Assign defaults (M2M fields)
                    shift_ids = ServiceShift.objects.filter(admin=admin_user, is_active=True).values_list('id', flat=True)[:1]
                    week_off_ids = WeekOffPolicy.objects.filter(admin=admin_user).values_list('id', flat=True)[:1]
                    location_ids = Location.objects.filter(admin=admin_user, is_active=True).values_list('id', flat=True)[:1]
                    
                    if shift_ids:
                        user_profile.shifts.set(shift_ids)
                    if week_off_ids:
                        user_profile.week_offs.set(week_off_ids)
                    if location_ids:
                        user_profile.locations.set(location_ids)
                    
                    self.stdout.write(self.style.SUCCESS(f'[OK] User created: {user_user.email}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'[OK] Using existing User: {user_user.email}'))
                
                self.stdout.write(self.style.SUCCESS('\n' + '='*50))
                self.stdout.write(self.style.SUCCESS('All users created successfully!'))
                self.stdout.write(self.style.SUCCESS('='*50))
                self.stdout.write(self.style.SUCCESS(f'\nSystem Owner: {system_owner_user.email}'))
                self.stdout.write(self.style.SUCCESS(f'Organization: {organization_user.email}'))
                self.stdout.write(self.style.SUCCESS(f'Admin: {admin_user.email}'))
                self.stdout.write(self.style.SUCCESS(f'User: {user_user.email}'))
                self.stdout.write(self.style.SUCCESS('\nAll users password: testpassword'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating users: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

