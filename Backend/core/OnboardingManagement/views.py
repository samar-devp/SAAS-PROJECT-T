"""
Onboarding Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date, timedelta

from .models import (
    OnboardingTemplate, OnboardingChecklist, OnboardingProcess,
    OnboardingTask, DocumentType, EmployeeDocument
)
from .serializers import (
    OnboardingTemplateSerializer, OnboardingChecklistSerializer,
    OnboardingProcessSerializer, OnboardingTaskSerializer,
    DocumentTypeSerializer, EmployeeDocumentSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class OnboardingTemplateAPIView(APIView):
    """Onboarding Template CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                template = get_object_or_404(OnboardingTemplate, id=pk, organization=organization)
                serializer = OnboardingTemplateSerializer(template)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Template fetched successfully",
                    "data": serializer.data
                })
            else:
                templates = OnboardingTemplate.objects.filter(organization=organization, is_active=True)
                serializer = OnboardingTemplateSerializer(templates, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Templates fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin_id = request.data.get('admin_id')
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin') if admin_id else None
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if admin:
                data['admin'] = str(admin.id)
            
            serializer = OnboardingTemplateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Template created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardingChecklistAPIView(APIView):
    """Onboarding Checklist CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, template_id):
        try:
            template = get_object_or_404(OnboardingTemplate, id=template_id)
            items = OnboardingChecklist.objects.filter(template=template, is_active=True).order_by('order')
            serializer = OnboardingChecklistSerializer(items, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Checklist items fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, template_id):
        try:
            template = get_object_or_404(OnboardingTemplate, id=template_id)
            
            data = request.data.copy()
            data['template'] = str(template.id)
            
            serializer = OnboardingChecklistSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Checklist item created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardingProcessAPIView(APIView):
    """Onboarding Process CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                process = get_object_or_404(OnboardingProcess, id=pk, organization=organization)
                serializer = OnboardingProcessSerializer(process)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Process fetched successfully",
                    "data": serializer.data
                })
            else:
                processes = OnboardingProcess.objects.filter(organization=organization)
                
                status_filter = request.query_params.get('status')
                if status_filter:
                    processes = processes.filter(status=status_filter)
                
                serializer = OnboardingProcessSerializer(processes.order_by('-created_at'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Processes fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            template_id = request.data.get('template_id')
            template = get_object_or_404(OnboardingTemplate, id=template_id) if template_id else None
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if template:
                data['template'] = str(template.id)
            
            # Set started_at if status is in_progress
            if data.get('status') == 'in_progress' and 'started_at' not in data:
                data['started_at'] = timezone.now()
            
            serializer = OnboardingProcessSerializer(data=data)
            if serializer.is_valid():
                process = serializer.save()
                
                # Auto-create tasks from template checklist if template provided
                if template and template.auto_create_profile:
                    checklist_items = OnboardingChecklist.objects.filter(template=template, is_active=True)
                    for item in checklist_items:
                        due_date = process.joining_date + timedelta(days=item.due_days)
                        OnboardingTask.objects.create(
                            onboarding_process=process,
                            checklist_item=item,
                            title=item.title,
                            description=item.description,
                            task_type=item.task_type,
                            assigned_to_id=request.data.get('assigned_to_id'),
                            due_date=due_date
                        )
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Onboarding process created successfully",
                    "data": OnboardingProcessSerializer(process).data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class OnboardingTaskAPIView(APIView):
    """Onboarding Task CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, process_id, pk=None):
        try:
            process = get_object_or_404(OnboardingProcess, id=process_id)
            
            if pk:
                task = get_object_or_404(OnboardingTask, id=pk, onboarding_process=process)
                serializer = OnboardingTaskSerializer(task)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Task fetched successfully",
                    "data": serializer.data
                })
            else:
                tasks = OnboardingTask.objects.filter(onboarding_process=process)
                
                status_filter = request.query_params.get('status')
                if status_filter:
                    tasks = tasks.filter(status=status_filter)
                
                serializer = OnboardingTaskSerializer(tasks.order_by('due_date'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Tasks fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, process_id, pk):
        try:
            process = get_object_or_404(OnboardingProcess, id=process_id)
            task = get_object_or_404(OnboardingTask, id=pk, onboarding_process=process)
            
            data = request.data.copy()
            
            # If marking as completed
            if data.get('status') == 'completed' and task.status != 'completed':
                data['completed_at'] = timezone.now()
                data['completed_by'] = str(request.user.id)
            
            serializer = OnboardingTaskSerializer(task, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                # Update process progress
                total_tasks = OnboardingTask.objects.filter(onboarding_process=process).count()
                completed_tasks = OnboardingTask.objects.filter(
                    onboarding_process=process,
                    status='completed'
                ).count()
                
                if total_tasks > 0:
                    progress = (completed_tasks / total_tasks) * 100
                    process.progress_percentage = progress
                    
                    if completed_tasks == total_tasks:
                        process.status = 'completed'
                        process.completed_at = timezone.now()
                    
                    process.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Task updated successfully",
                    "data": serializer.data
                })
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentTypeAPIView(APIView):
    """Document Type CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                doc_type = get_object_or_404(DocumentType, id=pk, organization=organization)
                serializer = DocumentTypeSerializer(doc_type)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Document type fetched successfully",
                    "data": serializer.data
                })
            else:
                doc_types = DocumentType.objects.filter(organization=organization, is_active=True)
                serializer = DocumentTypeSerializer(doc_types, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Document types fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            
            serializer = DocumentTypeSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Document type created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeDocumentAPIView(APIView):
    """Employee Document CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, employee_id, pk=None):
        try:
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            if pk:
                doc = get_object_or_404(EmployeeDocument, id=pk, employee=employee)
                serializer = EmployeeDocumentSerializer(doc)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Document fetched successfully",
                    "data": serializer.data
                })
            else:
                docs = EmployeeDocument.objects.filter(employee=employee)
                
                status_filter = request.query_params.get('status')
                if status_filter:
                    docs = docs.filter(status=status_filter)
                
                serializer = EmployeeDocumentSerializer(docs.order_by('-uploaded_at'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Documents fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, employee_id):
        try:
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            doc_type = get_object_or_404(DocumentType, id=request.data.get('document_type_id'))
            
            data = request.data.copy()
            data['employee'] = str(employee.id)
            data['document_type'] = str(doc_type.id)
            data['status'] = 'uploaded'
            
            serializer = EmployeeDocumentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Document uploaded successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

