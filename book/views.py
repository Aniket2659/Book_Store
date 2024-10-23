from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from django.core.exceptions import ObjectDoesNotExist
from .models import Book
from .serializers import BookSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication


class BookViewSet(viewsets.ModelViewSet):
    queryset=Book.objects.all()
    serializer_class=BookSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    # List: get a list of all books
    @swagger_auto_schema(
        operation_summary="Retrieve a list of all books",
        responses={200: openapi.Response('Success', BookSerializer(many=True))}
    )
    def list(self, request):
        print(f"User: {request.user}, Is authenticated: {request.user.is_authenticated}")
        if not request.user.is_authenticated:
            return Response({"error": "You are not authenticated."}, status=status.HTTP_403_FORBIDDEN)
        try:
            books = self.queryset
            serializer = self.get_serializer(books, many=True)
            return Response({"message": "List of books", "status": "Success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
            "error": f'Error retrieving books: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # retrieve: fet a specific book 
    @swagger_auto_schema(
        operation_summary="Retrieve a specific book",
        responses={
            200: openapi.Response('Success', BookSerializer),
            404: 'Book not found.'
        }
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            book=self.get_object()
            serializer=self.get_serializer(book)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except NotFound:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Error retrieving book: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Create a new book",
        request_body=BookSerializer,
        responses={
            201: openapi.Response('Book created successfully', BookSerializer),
            403: 'Permission denied.',
            400: 'Invalid data.'
        }
    )
    def create(self,request,*args, **kwargs):
        if not request.user.is_superuser:
            return Response({"error": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        try:
            serializer=self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response({"message": "Book created successfully", "status": "Success", "data": serializer.data}, status=status.HTTP_201_CREATED)
        
        except ValidationError as ve:
            return Response({'error': f'Invalid data: {ve.detail}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Error creating book: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_summary="Delete a book",
        responses={
            204: 'Book deleted successfully',
            403: 'Permission denied.',
            404: 'Book not found.'
        }
    )
    def update(self, request, pk=None, *args, **kwargs):
        if not request.user.is_superuser :
            return Response({"error": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            book = self.get_object()
            serializer = self.get_serializer(book, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Book updated successfully", "status": "Success", "data": serializer.data}, status=status.HTTP_200_OK)
        except NotFound:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            return Response({'error': f'Invalid data: {ve.detail}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Error updating book: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @swagger_auto_schema(
     operation_summary="Delete a book",
     responses={
         204: 'Book deleted successfully',
         403: 'Permission denied.',
         404: 'Book not found.'
     }
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        if not request.user.is_superuser :
            return Response({"error": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            book = self.get_object()
            self.perform_destroy(book)
            return Response({"message": "Book deleted successfully", "status": "Success"}, status=status.HTTP_204_NO_CONTENT)
        except NotFound:
            return Response({'error': 'Book not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Error deleting book: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)