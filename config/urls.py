from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import views as auth_views
from tasks.views import TaskViewSet, AnalyticsView
from tasks import views

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    # Редирект с главной
    path('', RedirectView.as_view(pattern_name='task_board'), name='home'),

    path('admin/', admin.site.urls),

    # API
    path('api/', include(router.urls)),
    path('api/analytics/', AnalyticsView.as_view(), name='api_analytics'),
    path('api-auth/', include('rest_framework.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),

    # Invite
    path('invite/<uuid:token>/', views.accept_invite, name='accept_invite'),
    path('invite/generate/', views.generate_invite, name='generate_invite'),

    # Страницы
    path('board/', views.task_board, name='task_board'),
    path('assigned/', views.assigned_tasks, name='assigned_tasks'),
    path('manager/', views.manager_board, name='manager_board'),
    path('analytics/', views.analytics_board, name='analytics'),

    # CRUD задач
    path('task/create/personal/', views.create_personal_task, name='create_personal_task'),
    path('task/create/assigned/', views.create_assigned_task, name='create_assigned_task'),
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    # Организация
    path('org/settings/', views.organization_settings, name='org_settings'),
    path('org/remove/<int:user_id>/', views.remove_member, name='remove_member'),
]