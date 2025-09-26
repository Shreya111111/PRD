from rest_framework import serializers
from .models import Alert, Team, User, UserAlertPreference

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    team = TeamSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'team', 'is_admin']

class AlertSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    target_teams = TeamSerializer(many=True, read_only=True)
    target_users = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'

class AlertCreateSerializer(serializers.ModelSerializer):
    target_team_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    target_user_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    
    class Meta:
        model = Alert
        exclude = ['created_by', 'target_teams', 'target_users']
    
    def create(self, validated_data):
        target_team_ids = validated_data.pop('target_team_ids', [])
        target_user_ids = validated_data.pop('target_user_ids', [])
        
        alert = Alert.objects.create(**validated_data)
        
        if target_team_ids:
            alert.target_teams.set(target_team_ids)
        if target_user_ids:
            alert.target_users.set(target_user_ids)
        
        return alert

class UserAlertPreferenceSerializer(serializers.ModelSerializer):
    alert = AlertSerializer(read_only=True)
    
    class Meta:
        model = UserAlertPreference
        fields = ['alert', 'is_read', 'is_snoozed', 'snoozed_until']