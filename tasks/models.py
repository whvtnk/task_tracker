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