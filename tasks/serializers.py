from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Task, Organization, UserProfile, InviteLink

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'organization']

class OrganizationSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ['id', 'name', 'owner', 'member_count', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count()

class InviteLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = InviteLink
        fields = ['id', 'token', 'is_active', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    author_info = UserSerializer(source='author', read_only=True)
    assignee_info = UserSerializer(source='assignee', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'