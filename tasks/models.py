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
        (1, 'Low (1)'),
        (2, 'Medium-Low (2)'),
        (3, 'Medium (3)'),
        (4, 'Medium-High (4)'),
        (5, 'High (5)'),    
    ]

    estimated_hours = models.IntegerField(verbose_name="Предполагаемые часы", default=0)

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    
    # Пока сделаем проект просто текстовым полем. 
    # (В будущем можно создать отдельную таблицу Project, если захочешь)
    project = models.CharField(max_length=100, verbose_name="Проект")

    # Связи с пользователями
    # on_delete=models.CASCADE означает: если удалят пользователя, удалятся и его задачи
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks', verbose_name="Автор")
    
    # null=True, blank=True означает, что исполнителя может пока не быть
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', verbose_name="Исполнитель")

    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1, verbose_name="Приоритет")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    
    deadline = models.DateTimeField(verbose_name="Дедлайн")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")


    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"