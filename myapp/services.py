from abc import ABC, abstractmethod
from django.utils import timezone
from .models import NotificationDelivery, UserAlertPreference

class NotificationChannel(ABC):
    @abstractmethod
    def deliver(self, alert, user, is_reminder=False):
        pass

class InAppNotificationChannel(NotificationChannel):
    def deliver(self, alert, user, is_reminder=False):
        # Create delivery record
        NotificationDelivery.objects.create(
            alert=alert,
            user=user,
            delivery_channel='in_app',
            is_reminder=is_reminder
        )
        
        # Update user preference
        pref, created = UserAlertPreference.objects.get_or_create(
            user=user, alert=alert
        )
        if is_reminder:
            pref.last_reminder = timezone.now()
            pref.save()
        
        return True

class EmailNotificationChannel(NotificationChannel):
    def deliver(self, alert, user, is_reminder=False):
        # Future implementation for email
        print(f"Email sent to {user.email}: {alert.title}")
        return True

class SMSNotificationChannel(NotificationChannel):
    def deliver(self, alert, user, is_reminder=False):
        # Future implementation for SMS
        print(f"SMS sent to {user.username}: {alert.title}")
        return True

class NotificationService:
    def __init__(self):
        self.channels = {
            'in_app': InAppNotificationChannel(),
            'email': EmailNotificationChannel(),
            'sms': SMSNotificationChannel(),
        }
    
    def deliver_alert(self, alert, is_reminder=False):
        target_users = alert.get_target_users()
        channel = self.channels.get(alert.delivery_type)
        
        if not channel:
            return False
        
        delivered_count = 0
        for user in target_users:
            if is_reminder:
                pref = UserAlertPreference.objects.filter(user=user, alert=alert).first()
                if pref and not pref.needs_reminder():
                    continue
            
            try:
                channel.deliver(alert, user, is_reminder)
                delivered_count += 1
            except Exception as e:
                print(f"Failed to deliver alert {alert.id} to user {user.id}: {e}")
        
        return delivered_count > 0
    
    def send_reminders(self):
        from .models import Alert
        active_alerts = Alert.objects.filter(
            is_active=True,
            reminders_enabled=True,
            start_time__lte=timezone.now(),
            expiry_time__gt=timezone.now()
        )
        
        for alert in active_alerts:
            self.deliver_alert(alert, is_reminder=True)