"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tasks.views import TaskViewSet, AnalyticsView
from django.contrib.auth import views as auth_views

from django.views.generic import RedirectView

from tasks import views

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='task_board'), name='home'),
    
    path('admin/', admin.site.urls),
    
    path('api/analytics/', AnalyticsView.as_view(), name='analytics'),

    path('api/', include(router.urls)),

    path('api-auth/', include('rest_framework.urls')),

    path('api/token/' , TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('api/token/refresh/' , TokenRefreshView.as_view(), name='token_refresh'),
    
    path('logout/', views.custom_logout, name='logout'),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    path('register/', views.register, name='register'),
    
    path('board/', views.task_board, name='task_board'),

    path('create-task/', views.create_task, name='create_task'),

    path('analytics-board/', views.analytics_board, name='analytics'),

    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
]
