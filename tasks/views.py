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

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

from .forms import TaskForm

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
    from django.shortcuts import get_object_or_404 # Добавь этот импорт наверх, он нам понадобится!

@login_required
def task_board(request):
    # 1. Базовый запрос (кто что видит)
    if request.user.is_superuser:
        user_tasks = Task.objects.all()
        users = User.objects.all() # Боссу нужен список всех юзеров для фильтра
    else:
        user_tasks = Task.objects.filter(assignee=request.user)
        users = None

    # 2. Ловим фильтры из поисковой строки браузера (GET-параметры)
    status_filter = request.GET.get('status')
    assignee_filter = request.GET.get('assignee')
    sort_by = request.GET.get('sort')

    # 3. Применяем фильтры, если они есть
    if status_filter:
        user_tasks = user_tasks.filter(status=status_filter)

    if assignee_filter and request.user.is_superuser:
        user_tasks = user_tasks.filter(assignee_id=assignee_filter)

    # 4. Применяем сортировку
    if sort_by == 'deadline_asc':
        user_tasks = user_tasks.order_by('deadline') # Сначала срочные
    elif sort_by == 'deadline_desc':
        user_tasks = user_tasks.order_by('-deadline')
    elif sort_by == 'priority_desc':
        user_tasks = user_tasks.order_by('-priority') # Сначала важные (5 -> 1)
    elif sort_by == 'priority_asc':
        user_tasks = user_tasks.order_by('priority')
    else:
        user_tasks = user_tasks.order_by('-created_at') # По умолчанию новые сверху

    # Упаковываем всё и отдаем в HTML
    context = {
        'tasks': user_tasks,
        'users': users,
        'current_status': status_filter,
        'current_assignee': assignee_filter,
        'current_sort': sort_by,
    }
    return render(request, 'index.html', context)


from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('task_board')
    else:
        form = UserCreationForm()
        
    return render(request, 'register.html', {'form': form})

@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False) # Говорим Джанго: "Подожди, пока не сохраняй!"
            task.author = request.user       # Автоматически ставим автором того, кто нажал кнопку
            task.save()                      # Вот теперь сохраняем в базу
            return redirect('task_board')    # Возвращаем на доску
    else:
        form = TaskForm()
    
    return render(request, 'create_task.html', {'form': form})  

@login_required
def analytics_board(request):
    if not request.user.is_superuser:
        return redirect('task_board')

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

    unassigned_total = Task.objects.filter(assignee__isnull=True).count()
    unassigned_completed = Task.objects.filter(assignee__isnull=True, status='completed').count()
    unassigned_overdue = Task.objects.filter(assignee__isnull=True, status='overdue').count()

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': completion_rate,
        'employee_stats': users_stats,
        
        'unassigned_total': unassigned_total,
        'unassigned_completed': unassigned_completed,
        'unassigned_overdue': unassigned_overdue,
    }
    return render(request, 'analytics.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.is_superuser:
        task = get_object_or_404(Task, id=task_id)
        task.delete()
    return redirect('task_board')

@login_required
def edit_task(request, task_id):
    if not request.user.is_superuser:
        return redirect('task_board')
        
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('task_board')
    else:
        form = TaskForm(instance=task)
        
    return render(request, 'create_task.html', {'form': form, 'edit_mode': True})


'''
вот это фронт моего сайта в данный момент и мне учительница сказала исправить типа 

улучшить вид сайта так как стиль сайта не устраивает и вот теперь 

для этого я собирался использовать  Agent Templates | 21st | 21st 

но у него оказалось платн подписка вроде того и теперь если я дам тебе промпты или сам компонент ты можешь мне создать такие красивые сайты 

и еще изначально в пример нам поставили TasksBoard | Desktop app for Google Tasks   этот сайт  

теперь я бы хотел улучшить саит до совершенства  

посмотрев наш примерный саит я осознал что мне надо улучшить не только стиль и сам бэкенды и тд 



вот в пример промптов которых я бы использовал 



и вот еще мне написать это все в режим code 




'''