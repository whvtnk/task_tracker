from django.db import models
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task
from .serializers import TaskSerializer 
from .permissions import IsAdminOrOwner


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer

    permission_classes = [IsAdminOrOwner]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'author', 'assignee']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'deadline', 'priority']

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Task.objects.all().order_by('-created_at')
        return Task.objects.filter(models.Q(author=user) | models.Q(assignee=user)).order_by('-created_at')
    
