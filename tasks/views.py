import uuid
from django.db import models
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Task, Organization, UserProfile, InviteLink
from .serializers import TaskSerializer, OrganizationSerializer, InviteLinkSerializer
from .permissions import IsAdminOrOwner, IsSuperUser, IsManager
from .forms import TaskForm, PersonalTaskForm, RegisterForm, OrganizationForm


# ─── API ViewSets ────────────────────────────────────────────

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
        return Task.objects.filter(
            Q(author=user) | Q(assignee=user)
        ).order_by('-created_at')


class AnalyticsView(APIView):
    permission_classes = [IsSuperUser]

    def get(self, request):
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='completed').count()
        overdue_tasks = Task.objects.filter(status='overdue').count()
        completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

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


# ─── Утилита: получить или создать профиль ───────────────────

def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'user'}
    )
    return profile


# ─── Auth Views ──────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            org_name = form.cleaned_data.get('organization_name', '')

            if role == 'manager':
                org = Organization.objects.create(name=org_name, owner=user)
                UserProfile.objects.create(user=user, role='manager', organization=org)
            else:
                UserProfile.objects.create(user=user, role='user')

            login(request, user)
            return redirect('task_board')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')


# ─── Инвайт система ──────────────────────────────────────────

@login_required
def generate_invite(request):
    """Менеджер генерирует новую инвайт-ссылку"""
    profile = get_or_create_profile(request.user)
    if profile.role != 'manager':
        return redirect('task_board')

    invite = InviteLink.objects.create(
        organization=profile.organization,
        created_by=request.user
    )
    invite_url = request.build_absolute_uri(f'/invite/{invite.token}/')
    return JsonResponse({'invite_url': invite_url, 'token': str(invite.token)})


@login_required
def accept_invite(request, token):
    """Юзер принимает инвайт и вступает в организацию"""
    invite = get_object_or_404(InviteLink, token=token, is_active=True)
    profile = get_or_create_profile(request.user)

    if profile.role == 'manager':
        return render(request, 'invite_error.html', {
            'error': 'Менеджеры не могут вступать в организации через инвайт.'
        })

    if profile.organization is not None:
        return render(request, 'invite_error.html', {
            'error': 'Вы уже состоите в организации.'
        })

    # Вступаем в организацию
    profile.organization = invite.organization
    profile.save()

    # Деактивируем ссылку
    invite.is_active = False
    invite.save()

    return redirect('assigned_tasks')


@login_required
def leave_organization(request):
    """Юзер покидает организацию (только если менеджер удалил орг)"""
    profile = get_or_create_profile(request.user)
    if profile.organization and not profile.organization.pk:
        profile.organization = None
        profile.save()
    return redirect('task_board')


# ─── Доска задач ─────────────────────────────────────────────

@login_required
def task_board(request):
    """Главная доска — личные задачи пользователя"""
    profile = get_or_create_profile(request.user)

    # Личные задачи — только свои
    personal_tasks = Task.objects.filter(
        author=request.user,
        task_type='personal'
    ).order_by('-created_at')

    # Фильтры
    status_filter = request.GET.get('status')
    sort_by = request.GET.get('sort')
    search_q = request.GET.get('q', '')

    if status_filter:
        personal_tasks = personal_tasks.filter(status=status_filter)
    if search_q:
        personal_tasks = personal_tasks.filter(
            Q(title__icontains=search_q) | Q(description__icontains=search_q)
        )
    if sort_by == 'deadline_asc':
        personal_tasks = personal_tasks.order_by('deadline')
    elif sort_by == 'priority_desc':
        personal_tasks = personal_tasks.order_by('-priority')

    context = {
        'tasks': personal_tasks,
        'profile': profile,
        'current_status': status_filter,
        'current_sort': sort_by,
        'search_q': search_q,
        'page': 'board',
    }
    return render(request, 'index.html', context)


@login_required
def assigned_tasks(request):
    """Назначено мне — задачи от менеджера"""
    profile = get_or_create_profile(request.user)

    tasks = Task.objects.filter(
        assignee=request.user,
        task_type='assigned'
    ).order_by('-created_at')

    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    context = {
        'tasks': tasks,
        'profile': profile,
        'current_status': status_filter,
        'page': 'assigned',
    }
    return render(request, 'assigned.html', context)


@login_required
def manager_board(request):
    """Менеджер видит задачи своей команды"""
    profile = get_or_create_profile(request.user)
    if profile.role != 'manager':
        return redirect('task_board')

    org = profile.organization
    # Члены организации
    members = UserProfile.objects.filter(organization=org).select_related('user')

    # Задачи назначенные менеджером
    assigned = Task.objects.filter(
        author=request.user,
        task_type='assigned',
        organization=org
    ).order_by('-created_at')

    # Фильтры
    assignee_filter = request.GET.get('assignee')
    status_filter = request.GET.get('status')
    if assignee_filter:
        assigned = assigned.filter(assignee_id=assignee_filter)
    if status_filter:
        assigned = assigned.filter(status=status_filter)

    context = {
        'tasks': assigned,
        'members': members,
        'organization': org,
        'profile': profile,
        'current_assignee': assignee_filter,
        'current_status': status_filter,
        'page': 'manager',
    }
    return render(request, 'manager_board.html', context)


# ─── CRUD задач ──────────────────────────────────────────────

@login_required
def create_personal_task(request):
    """Создать личную задачу"""
    profile = get_or_create_profile(request.user)
    if request.method == 'POST':
        form = PersonalTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.task_type = 'personal'
            task.project = 'Личные'
            task.save()
            return redirect('task_board')
    else:
        form = PersonalTaskForm()
    return render(request, 'create_task.html', {'form': form, 'task_type': 'personal', 'profile': profile})


@login_required
def create_assigned_task(request):
    """Менеджер создаёт задачу для участника команды"""
    profile = get_or_create_profile(request.user)
    if profile.role != 'manager':
        return redirect('task_board')

    org = profile.organization
    members = UserProfile.objects.filter(organization=org).select_related('user')

    if request.method == 'POST':
        form = TaskForm(request.POST)
        # Ограничиваем assignee только членами организации
        form.fields['assignee'].queryset = User.objects.filter(
            profile__organization=org
        )
        if form.is_valid():
            task = form.save(commit=False)
            task.author = request.user
            task.task_type = 'assigned'
            task.organization = org
            task.save()
            return redirect('manager_board')
    else:
        form = TaskForm()
        form.fields['assignee'].queryset = User.objects.filter(
            profile__organization=org
        )

    return render(request, 'create_task.html', {
        'form': form,
        'task_type': 'assigned',
        'members': members, 
        'profile': profile
    })


@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    profile = get_or_create_profile(request.user)

    # Только автор может редактировать
    if task.author != request.user and not request.user.is_superuser:
        return redirect('task_board')

    if task.task_type == 'personal':
        FormClass = PersonalTaskForm
    else:
        FormClass = TaskForm

    if request.method == 'POST':
        form = FormClass(request.POST, instance=task)
        if form.is_valid():
            form.save()
            if task.task_type == 'assigned':
                return redirect('manager_board')
            return redirect('task_board')
    else:
        form = FormClass(instance=task)

    return render(request, 'create_task.html', {'form': form, 'edit_mode': True, 'profile': profile})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if task.author == request.user or request.user.is_superuser:
        task_type = task.task_type
        task.delete()
        if task_type == 'assigned':
            return redirect('manager_board')
    return redirect('task_board')


# ─── Аналитика ───────────────────────────────────────────────

@login_required
def analytics_board(request):
    if not request.user.is_superuser:
        return redirect('task_board')

    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    overdue_tasks = Task.objects.filter(status='overdue').count()
    completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0

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


# ─── Менеджмент организации ──────────────────────────────────

@login_required
def organization_settings(request):
    """Настройки организации для менеджера"""
    profile = get_or_create_profile(request.user)
    if profile.role != 'manager':
        return redirect('task_board')

    org = profile.organization
    members = UserProfile.objects.filter(organization=org).select_related('user')
    invites = InviteLink.objects.filter(organization=org, is_active=True)

    context = {
        'organization': org,
        'members': members,
        'invites': invites,
        'profile': profile,
    }
    return render(request, 'org_settings.html', context)


@login_required
def remove_member(request, user_id):
    """Менеджер удаляет участника из организации"""
    profile = get_or_create_profile(request.user)
    if profile.role != 'manager':
        return redirect('task_board')

    member_profile = get_object_or_404(UserProfile, user_id=user_id, organization=profile.organization)
    member_profile.organization = None
    member_profile.save()
    return redirect('org_settings')