from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task

class Command(BaseCommand):
    help = 'Помечает просроченные задачи статусом "overdue"'

    def handle(self, *args, **kwargs):
        now = timezone.now() # Текущее время
        
        # Ищем задачи: дедлайн прошел, но они еще не завершены и не помечены просроченными
        overdue_tasks = Task.objects.filter(
            deadline__lt=now
        ).exclude(
            status__in=['completed', 'overdue']
        )

        count = overdue_tasks.count()
        
        if count > 0:
            overdue_tasks.update(status='overdue')
            # Выводим зеленое сообщение об успехе
            self.stdout.write(self.style.SUCCESS(f'✅ Обновлено просроченных задач: {count}'))
        else:
            self.stdout.write(self.style.SUCCESS('🎉 Нет новых просроченных задач!'))