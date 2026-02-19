from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count

from rest_framework import viewsets, filters
from .models import Task

from .serializers import TaskSerializer 
from .permissions import IsAdminOrOwner, IsSuperUser


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
    

class AnalyticsView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='completed').count()
        overdue_tasks = Task.objects.filter(status='overdue').count()


        completion_rate = 0
        if total_tasks > 0:
            completion_rate = round((completed_tasks / total_tasks) * 100, 2)


        users_stats = User.objects.annotate(
            total_assigned=Count('assigned_tasks'),
            completed=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed')),
            overdue=Count('assigned_tasks', filter=Q(assigned_tasks__status='overdue'))
        ).values('username', 'total_assigned', 'completed', 'overdue')

        return Response({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'completion_rate_percent': completion_rate,
            'employee_stats': list(users_stats)
        })
    
