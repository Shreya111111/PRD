from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    
class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    
    DELIVERY_CHOICES = [
        ('in_app', 'In-App'),
        ('email', 'Email'),
        ('sms', 'SMS'),
    ]
    
    VISIBILITY_CHOICES = [
        ('organization', 'Organization'),
        ('team', 'Team'),
        ('user', 'User'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='info')
    delivery_type = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='in_app')
    visibility_type = models.CharField(max_length=15, choices=VISIBILITY_CHOICES)
    
    # Visibility targets
    target_teams = models.ManyToManyField(Team, blank=True)
    target_users = models.ManyToManyField(User, blank=True)
    
    # Timing
    start_time = models.DateTimeField(default=timezone.now)
    expiry_time = models.DateTimeField()
    reminder_frequency = models.IntegerField(default=2)  # hours
    reminders_enabled = models.BooleanField(default=True)
    
    # Meta
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_alerts')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def is_expired(self):
        return timezone.now() > self.expiry_time
    
    def get_target_users(self):
        if self.visibility_type == 'organization':
            return User.objects.filter(is_active=True)
        elif self.visibility_type == 'team':
            return User.objects.filter(team__in=self.target_teams.all(), is_active=True)
        else:
            return self.target_users.filter(is_active=True)
    
    def __str__(self):
        return f"{self.title} ({self.severity})"

class NotificationDelivery(models.Model):
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivered_at = models.DateTimeField(auto_now_add=True)
    delivery_channel = models.CharField(max_length=10)
    is_reminder = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['alert', 'user', 'delivered_at']

class UserAlertPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    is_snoozed = models.BooleanField(default=False)
    snoozed_until = models.DateTimeField(null=True, blank=True)
    last_reminder = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'alert']
    
    def snooze_for_day(self):
        tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self.is_snoozed = True
        self.snoozed_until = tomorrow
        self.save()
    
    def is_snooze_active(self):
        if not self.is_snoozed or not self.snoozed_until:
            return False
        return timezone.now() < self.snoozed_until
    
    def needs_reminder(self):
        if self.is_snooze_active() or not self.alert.reminders_enabled:
            return False
        if not self.last_reminder:
            return True
        return timezone.now() >= self.last_reminder + timedelta(hours=self.alert.reminder_frequency)