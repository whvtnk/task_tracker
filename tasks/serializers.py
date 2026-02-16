from rest_framework import serializers 
from django.contrib.auth.models import User 
from .models import Task 

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class TaskSerializer(serializers.ModelSerializer):
    author_info = UserSerializer(source = 'author', read_only=True)
    assignee_info = UserSerializer(source = 'assignee', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        