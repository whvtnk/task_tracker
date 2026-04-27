import uuid
from django.db import models
from django.contrib.auth.models import User
class Task(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium-Low'),
        (3, 'Medium'),
        (4, 'Medium-High'),
        (5, 'High'),    
    ]

    estimated_hours = models.IntegerField(verbose_name="Estimated hours", default=0)


   
    TASK_TYPE_CHOICES = [
        ('personal', 'Личная'),
        ('assigned', 'Назначенная'),
    ]

    task_type = models.CharField(
        max_length=20, choices=TASK_TYPE_CHOICES,
        default='personal', verbose_name="Тип задачи"
    )
    organization = models.ForeignKey(
        'Organization', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tasks',
        verbose_name="Организация"
    )




    title = models.CharField(max_length=200, verbose_name="Title")
    description = models.TextField(verbose_name="Description", blank=True)
    
    project = models.CharField(max_length=100, verbose_name="Project")

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks', verbose_name="Author")
    
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="Assignee")

    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1, verbose_name="Priority")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Status")
    
    deadline = models.DateTimeField(verbose_name="Deadline")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")


    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"


class Organization(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='owned_organizations',
        verbose_name="Менеджер"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Организация"
        verbose_name_plural = "Организации"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('user', 'User'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES,
        default='user', verbose_name="Роль"
    )
    organization = models.ForeignKey(
        Organization, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='members',
        verbose_name="Организация"
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"


class InviteLink(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE,
        related_name='invites',
        verbose_name="Организация"
    )
    token = models.UUIDField(
        default=uuid.uuid4, unique=True,
        verbose_name="Токен"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name="Создал"
    )
    is_active = models.BooleanField(
        default=True, verbose_name="Активна"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Инвайт для {self.organization.name}"

    class Meta:
        verbose_name = "Инвайт ссылка"
        verbose_name_plural = "Инвайт ссылки"