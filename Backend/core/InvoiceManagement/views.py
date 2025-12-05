"""
Invoice Management API Views
Admin only access
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, date
import traceback

from .models import Invoice
from .serializers import (
    InvoiceSerializer, InvoiceCreateSerializer, InvoiceUpdateSerializer,
    InvoiceListSerializer
)
from AuthN.models import BaseUserModel
from utils.pagination_utils import CustomPagination


class InvoiceAPIView(APIView):
    """Invoice CRUD - Admin Only"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, pk=None):
        """Get invoice(s)"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                # Get single invoice
                try:
                    invoice = Invoice.objects.get(id=pk, admin=admin)
                except Invoice.DoesNotExist:
                    return Response({
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Invoice not found",
                        "data": []
                    }, status=status.HTTP_404_NOT_FOUND)
                serializer = InvoiceSerializer(invoice, context={'request': request})
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Invoice fetched successfully",
                    "data": serializer.data
                })
            else:
                # Get list of invoices
                invoices = Invoice.objects.filter(admin=admin)
                
                # Filter by status if provided
                status_filter = request.query_params.get('status', None)
                if status_filter:
                    invoices = invoices.filter(status=status_filter)
                
                # Filter by date range if provided
                from_date = request.query_params.get('from_date', None)
                to_date = request.query_params.get('to_date', None)
                
                if from_date:
                    try:
                        from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
                        invoices = invoices.filter(invoice_date__gte=from_date_obj)
                    except ValueError:
                        pass  # Invalid date format, ignore
                
                if to_date:
                    try:
                        to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
                        invoices = invoices.filter(invoice_date__lte=to_date_obj)
                    except ValueError:
                        pass  # Invalid date format, ignore
                
                # Search by invoice number or client name
                search = request.query_params.get('search', None)
                if search:
                    invoices = invoices.filter(
                        Q(invoice_number__icontains=search) |
                        Q(client_name__icontains=search)
                    )
                
                # Pagination
                paginator = self.pagination_class()
                paginated_invoices = paginator.paginate_queryset(invoices, request)
                serializer = InvoiceListSerializer(paginated_invoices, many=True)
                
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Invoices fetched successfully",
                    "data": pagination_data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create invoice"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            
            # Parse items JSON string if it's a string or list containing string
            import json
            if 'items' in data:
                items_value = data['items']
                print(f"DEBUG VIEW: items type: {type(items_value)}, value: {items_value}")
                
                # Handle case where FormData sends it as a list with one string element
                if isinstance(items_value, list) and len(items_value) > 0:
                    if isinstance(items_value[0], str):
                        items_value = items_value[0]
                        print(f"DEBUG VIEW: Extracted string from list: {items_value[:200]}")
                
                if isinstance(items_value, str):
                    try:
                        parsed = json.loads(items_value)
                        print(f"DEBUG VIEW: Parsed successfully: {type(parsed)}, length: {len(parsed) if isinstance(parsed, list) else 'N/A'}, value: {parsed}")
                        data['items'] = parsed
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"DEBUG VIEW: JSON parse error: {e}")
                        data['items'] = []
                elif isinstance(items_value, list):
                    # Already a list, use as is
                    print(f"DEBUG VIEW: Already a list with {len(items_value)} items, using as is")
                    data['items'] = items_value
                else:
                    print(f"DEBUG VIEW: Unknown type {type(items_value)}, setting to empty list")
                    data['items'] = []
            else:
                print(f"DEBUG VIEW: 'items' key not found in data")
            
            # Final check before passing to serializer
            print(f"DEBUG VIEW FINAL: data['items'] before serializer: {data.get('items')}")
            print(f"DEBUG VIEW FINAL: data['items'] type: {type(data.get('items'))}")
            if 'items' in data and isinstance(data['items'], list):
                print(f"DEBUG VIEW FINAL: items list length: {len(data['items'])}")
            
            serializer = InvoiceCreateSerializer(data=data, context={'admin': admin})
            if serializer.is_valid():
                print(f"DEBUG VIEW: Serializer is valid, saving...")
                invoice = serializer.save()
                print(f"DEBUG VIEW: Invoice saved with items: {invoice.items}")
                response_serializer = InvoiceSerializer(invoice, context={'request': request})
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Invoice created successfully",
                    "data": response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                print(f"DEBUG VIEW: Serializer errors: {serializer.errors}")
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request, admin_id, pk):
        """Update invoice"""
        try:
            invoice = get_object_or_404(Invoice, id=pk, admin_id=admin_id)
            data = request.data.copy()
            
            # Parse items JSON string if it's a string or list containing string
            if 'items' in data:
                import json
                items_value = data['items']
                # Handle case where FormData sends it as a list with one string element
                if isinstance(items_value, list) and len(items_value) > 0:
                    items_value = items_value[0]
                if isinstance(items_value, str):
                    try:
                        data['items'] = json.loads(items_value)
                    except (json.JSONDecodeError, TypeError):
                        data['items'] = []
                elif not isinstance(items_value, list):
                    data['items'] = []
            
            serializer = InvoiceUpdateSerializer(invoice, data=data, partial=True)
            if serializer.is_valid():
                invoice = serializer.save()
                response_serializer = InvoiceSerializer(invoice, context={'request': request})
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Invoice updated successfully",
                    "data": response_serializer.data
                })
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, admin_id, pk):
        """Delete invoice"""
        try:
            invoice = get_object_or_404(Invoice, id=pk, admin_id=admin_id)
            invoice.delete()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Invoice deleted successfully",
                "data": []
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



