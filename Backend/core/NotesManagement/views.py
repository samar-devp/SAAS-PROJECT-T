"""
Notes Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import traceback

from .models import NoteCategory, Note, NoteComment, NoteVersion, NoteTemplate
from .serializers import (
    NoteCategorySerializer, NoteSerializer, NoteCommentSerializer,
    NoteVersionSerializer, NoteTemplateSerializer
)
from AuthN.models import BaseUserModel
from utils.pagination_utils import CustomPagination


class NoteCategoryAPIView(APIView):
    """Note Category CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        """Get categories"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                category = get_object_or_404(NoteCategory, id=pk, organization=organization)
                serializer = NoteCategorySerializer(category)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Category fetched successfully",
                    "data": serializer.data
                })
            else:
                categories = NoteCategory.objects.filter(organization=organization, is_active=True)
                serializer = NoteCategorySerializer(categories, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Categories fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Create category"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin = get_object_or_404(BaseUserModel, id=request.data.get('admin_id'), role='admin')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['admin'] = str(admin.id)
            
            serializer = NoteCategorySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Category created successfully",
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


class NoteAPIView(APIView):
    """Note CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, user_id, pk=None):
        """Get notes"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            
            if pk:
                note = get_object_or_404(Note, id=pk)
                # Check access
                if note.created_by != user and user not in note.shared_with.all():
                    return Response({
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "Access denied"
                    }, status=status.HTTP_403_FORBIDDEN)
                
                serializer = NoteSerializer(note)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Note fetched successfully",
                    "data": serializer.data
                })
            else:
                # Get user's notes and shared notes
                queryset = Note.objects.filter(
                    Q(created_by=user) | Q(shared_with=user),
                    deleted_at__isnull=True
                ).distinct()
                
                # Filters
                is_archived = request.query_params.get('is_archived')
                if is_archived == 'true':
                    queryset = queryset.filter(is_archived=True)
                elif is_archived == 'false':
                    queryset = queryset.filter(is_archived=False)
                
                is_pinned = request.query_params.get('is_pinned')
                if is_pinned == 'true':
                    queryset = queryset.filter(is_pinned=True)
                
                category_id = request.query_params.get('category_id')
                if category_id:
                    queryset = queryset.filter(category_id=category_id)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = NoteSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Notes fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, user_id):
        """Create note"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            user_profile = user.own_user_profile
            
            data = request.data.copy()
            data['created_by'] = str(user.id)
            data['admin'] = str(user_profile.admin.id)
            data['organization'] = str(user_profile.organization.id)
            
            # Calculate word count and reading time
            content = data.get('content', '')
            word_count = len(content.split())
            reading_time = max(1, word_count // 200)  # Assuming 200 words per minute
            data['word_count'] = word_count
            data['reading_time_minutes'] = reading_time
            
            serializer = NoteSerializer(data=data)
            if serializer.is_valid():
                note = serializer.save()
                
                # Add shared users if provided
                shared_user_ids = request.data.get('shared_user_ids', [])
                if shared_user_ids:
                    shared_users = BaseUserModel.objects.filter(id__in=shared_user_ids)
                    note.shared_with.set(shared_users)
                
                # Add editable users if provided
                editable_user_ids = request.data.get('editable_user_ids', [])
                if editable_user_ids:
                    editable_users = BaseUserModel.objects.filter(id__in=editable_user_ids)
                    note.can_edit.set(editable_users)
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Note created successfully",
                    "data": NoteSerializer(note).data
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
    
    @transaction.atomic
    def put(self, request, user_id, pk):
        """Update note"""
        try:
            note = get_object_or_404(Note, id=pk)
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            
            # Check edit permission
            if note.created_by != user and user not in note.can_edit.all():
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to edit this note"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Create version before update
            NoteVersion.objects.create(
                note=note,
                version_number=note.version,
                title=note.title,
                content=note.content,
                changed_by=user
            )
            
            # Update note
            data = request.data.copy()
            if 'content' in data:
                content = data.get('content', '')
                word_count = len(content.split())
                reading_time = max(1, word_count // 200)
                data['word_count'] = word_count
                data['reading_time_minutes'] = reading_time
                data['version'] = note.version + 1
            
            serializer = NoteSerializer(note, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Note updated successfully",
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
    
    @transaction.atomic
    def delete(self, request, user_id, pk):
        """Soft delete note"""
        try:
            note = get_object_or_404(Note, id=pk)
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            
            # Check permission
            if note.created_by != user:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to delete this note"
                }, status=status.HTTP_403_FORBIDDEN)
            
            note.deleted_at = timezone.now()
            note.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Note deleted successfully"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NoteCommentAPIView(APIView):
    """Note Comments"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, note_id):
        """Get comments"""
        try:
            note = get_object_or_404(Note, id=note_id)
            comments = NoteComment.objects.filter(note=note)
            serializer = NoteCommentSerializer(comments, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Comments fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, note_id):
        """Create comment"""
        try:
            note = get_object_or_404(Note, id=note_id)
            data = request.data.copy()
            data['note'] = str(note.id)
            data['user'] = str(request.user.id)
            
            serializer = NoteCommentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Comment added successfully",
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

