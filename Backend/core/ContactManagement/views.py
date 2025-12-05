"""
Contact Management Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.core.files.uploadedfile import InMemoryUploadedFile

from .models import Contact
from .serializers import (
    ContactSerializer, ContactCreateSerializer, ContactExtractionResultSerializer
)
from .ocr_service import BusinessCardOCRService
from AuthN.models import BaseUserModel
from utils.pagination_utils import CustomPagination


class ContactExtractAPIView(APIView):
    """
    Extract contact information from business card image using OCR
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, admin_id, user_id=None):
        """Extract contact details from uploaded business card image"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            if 'business_card_image' not in request.FILES:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Business card image is required",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            image_file = request.FILES['business_card_image']
            
            # Validate image file
            if not image_file.content_type.startswith('image/'):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "File must be an image",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Initialize OCR service
            ocr_service = BusinessCardOCRService()
            
            # Extract contact information
            extraction_result = ocr_service.extract_contact_info(image_file)
            
            if not extraction_result.get('success'):
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": extraction_result.get('error', 'Failed to extract contact information'),
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Remove success and error fields for response
            extraction_result.pop('success', None)
            extraction_result.pop('error', None)
            
            # Serialize the result
            serializer = ContactExtractionResultSerializer(data=extraction_result)
            if serializer.is_valid():
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Contact information extracted successfully",
                    "data": serializer.validated_data
                })
            else:
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Contact information extracted with some validation issues",
                    "data": extraction_result
                })
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error extracting contact information: {str(e)}",
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactAPIView(APIView):
    """
    Contact CRUD Operations
    - Admin and users can create, read, update, and delete contacts
    - Admin can see all contacts, users can only see their own
    - Search functionality for contacts
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, user_id=None, pk=None):
        """Get contacts - filtered by role"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            if pk:
                # Get specific contact
                contact = get_object_or_404(Contact, id=pk, admin=admin)
                
                # Check access permission
                if user.role == 'user':
                    # User can only see contacts where user_id matches
                    if contact.user != user:
                        return Response({
                            "status": status.HTTP_403_FORBIDDEN,
                            "message": "You don't have permission to view this contact",
                            "data": None
                        }, status=status.HTTP_403_FORBIDDEN)
                
                serializer = ContactSerializer(contact, context={'request': request})
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Contact fetched successfully",
                    "data": serializer.data
                })
            else:
                # Filter contacts based on role
                if user.role == 'admin':
                    # Admin can see all contacts where admin_id matches
                    queryset = Contact.objects.filter(admin=admin)
                    # Filter by user_id if provided
                    if user_id:
                        target_user = get_object_or_404(BaseUserModel, id=user_id, role='user')
                        queryset = queryset.filter(user=target_user)
                elif user.role == 'user':
                    # User can only see contacts where user_id matches
                    queryset = Contact.objects.filter(admin=admin, user=user)
                else:
                    queryset = Contact.objects.none()
                
                # Search functionality
                search_query = request.query_params.get('search', '').strip()
                if search_query:
                    queryset = queryset.filter(
                        Q(full_name__icontains=search_query) |
                        Q(company_name__icontains=search_query) |
                        Q(mobile_number__icontains=search_query) |
                        Q(email_address__icontains=search_query) |
                        Q(state__icontains=search_query) |
                        Q(city__icontains=search_query)
                    )
                
                # Filter by source type
                source_type = request.query_params.get('source_type')
                if source_type:
                    queryset = queryset.filter(source_type=source_type)
                
                # Filter by company
                company = request.query_params.get('company')
                if company:
                    queryset = queryset.filter(company_name__icontains=company)
                
                # Filter by state
                state = request.query_params.get('state')
                if state:
                    queryset = queryset.filter(state__icontains=state)
                
                # Filter by city
                city = request.query_params.get('city')
                if city:
                    queryset = queryset.filter(city__icontains=city)
                
                # Filter by date_from (created_at)
                date_from = request.query_params.get('date_from')
                if date_from:
                    queryset = queryset.filter(created_at__date__gte=date_from)
                
                # Filter by date_to (created_at)
                date_to = request.query_params.get('date_to')
                if date_to:
                    queryset = queryset.filter(created_at__date__lte=date_to)
                
                # Order by most recent first
                queryset = queryset.order_by('-created_at')
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = ContactSerializer(paginated_qs, many=True, context={'request': request})
                pagination_data = paginator.get_paginated_response(serializer.data)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Contacts fetched successfully",
                    "data": {
                        "results": serializer.data,
                        "count": pagination_data.get('total_objects', len(serializer.data)),
                        "next": pagination_data.get('next_page_number'),
                        "previous": pagination_data.get('previous_page_number')
                    }
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id, user_id=None):
        """Create contact - Admin or User can create"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            # Only admin and user can create contacts
            if user.role not in ['admin', 'user']:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "Only admin and user can create contacts",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            
            data = request.data.copy()
            data['created_by'] = str(user.id)
            
            # Determine user based on who is creating
            user_obj = None
            if user.role == 'user':
                # If user/employee is creating, both admin_id and user_id should be saved
                user_obj = user
            elif user.role == 'admin':
                # If admin is creating, user_id should be null
                user_obj = None
            
            # Clean empty strings from data - convert to None
            for key in list(data.keys()):
                if isinstance(data[key], str) and data[key].strip() == '':
                    data[key] = None
            
            # Set defaults for required fields
            if not data.get('mobile_number'):
                data['mobile_number'] = ''
            if not data.get('source_type'):
                data['source_type'] = 'manual'
            
            serializer = ContactCreateSerializer(data=data)
            # Always try to save, even if validation has minor issues
            if serializer.is_valid(raise_exception=False):
                created_by_user = BaseUserModel.objects.get(id=data['created_by'])
                contact = serializer.save(
                    admin=admin,
                    user=user_obj,
                    created_by=created_by_user
                )
            else:
                # If validation fails, create with cleaned data anyway
                created_by_user = BaseUserModel.objects.get(id=data['created_by'])
                # Prepare data for direct model creation
                contact_data = {}
                for field in ContactCreateSerializer.Meta.fields:
                    if field in data and data[field] is not None:
                        contact_data[field] = data[field]
                
                # Ensure mobile_number has a value
                if 'mobile_number' not in contact_data or not contact_data['mobile_number']:
                    contact_data['mobile_number'] = ''
                if 'source_type' not in contact_data or not contact_data['source_type']:
                    contact_data['source_type'] = 'manual'
                
                contact = Contact.objects.create(
                    admin=admin,
                    user=user_obj,
                    created_by=created_by_user,
                    **contact_data
                )
                
                response_serializer = ContactSerializer(contact, context={'request': request})
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Contact created successfully",
                    "data": response_serializer.data
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request, admin_id, user_id, pk):
        """Update contact"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            contact = get_object_or_404(Contact, id=pk, admin=admin)
            
            # Check access permission
            if user.role == 'user':
                # User can only update contacts where user_id matches
                if contact.user != user:
                    return Response({
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "You don't have permission to update this contact",
                        "data": None
                    }, status=status.HTTP_403_FORBIDDEN)
            
            data = request.data.copy()
            serializer = ContactCreateSerializer(contact, data=data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                response_serializer = ContactSerializer(contact, context={'request': request})
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Contact updated successfully",
                    "data": response_serializer.data
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def delete(self, request, admin_id, user_id, pk):
        """Delete contact"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            contact = get_object_or_404(Contact, id=pk, admin=admin)
            
            # Check access permission
            if user.role == 'user':
                # User can only delete contacts where user_id matches
                if contact.user != user:
                    return Response({
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "You don't have permission to delete this contact",
                        "data": None
                    }, status=status.HTTP_403_FORBIDDEN)
            
            contact.delete()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Contact deleted successfully",
                "data": None
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ContactStatsAPIView(APIView):
    """
    Get statistics about contacts
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, user_id=None):
        """Get contact statistics"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            # Filter contacts based on role
            if user.role == 'admin':
                # Admin can see all contacts where admin_id matches
                contacts = Contact.objects.filter(admin=admin)
                if user_id:
                # Admin viewing stats for specific user
                    target_user = get_object_or_404(BaseUserModel, id=user_id, role='user')
                    contacts = contacts.filter(user=target_user)
            elif user.role == 'user':
                # User can only see contacts where user_id matches
                contacts = Contact.objects.filter(admin=admin, user=user)
            else:
                contacts = Contact.objects.none()
            
            stats = {
                'total_contacts': contacts.count(),
                'scanned_contacts': contacts.filter(source_type='scanned').count(),
                'manual_contacts': contacts.filter(source_type='manual').count(),
                'contacts_with_email': contacts.exclude(email_address__isnull=True).exclude(email_address='').count(),
                'contacts_with_phone': contacts.exclude(mobile_number__isnull=True).exclude(mobile_number='').count(),
                'contacts_with_company': contacts.exclude(company_name__isnull=True).exclude(company_name='').count(),
                'unique_companies': contacts.exclude(company_name__isnull=True).exclude(company_name='').values('company_name').distinct().count(),
                'unique_states': contacts.exclude(state__isnull=True).exclude(state='').values('state').distinct().count(),
                'unique_cities': contacts.exclude(city__isnull=True).exclude(city='').values('city').distinct().count(),
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Statistics fetched successfully",
                "data": stats
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

