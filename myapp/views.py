from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from .models import Alert, Team, User, UserAlertPreference, NotificationDelivery
from .serializers import AlertSerializer, AlertCreateSerializer, UserAlertPreferenceSerializer
from .services import NotificationService

class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AlertCreateSerializer
        return AlertSerializer
    
    def perform_create(self, serializer):
        alert = serializer.save(created_by=self.request.user)
        # Deliver initial notification
        service = NotificationService()
        service.deliver_alert(alert)
    
    def get_queryset(self):
        queryset = Alert.objects.all()
        if not self.request.user.is_admin:
            # Users see only alerts targeted to them and created by admin users
            queryset = Alert.objects.filter(
                Q(visibility_type='organization') |
                Q(visibility_type='team', target_teams=self.request.user.team) |
                Q(visibility_type='user', target_users=self.request.user),
                created_by__is_admin=True  # Only show alerts created by admin users
            ).distinct()
        
        # Filters
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        status_filter = self.request.query_params.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True, expiry_time__gt=timezone.now())
        elif status_filter == 'expired':
            queryset = queryset.filter(Q(is_active=False) | Q(expiry_time__lte=timezone.now()))
        
        return queryset
    
    @action(detail=True, methods=['post', 'delete'])
    def snooze(self, request, pk=None):
        alert = self.get_object()
        pref, created = UserAlertPreference.objects.get_or_create(
            user=request.user, alert=alert
        )
        
        if request.method == 'POST':
            pref.snooze_for_day()
            return Response({'status': 'snoozed'})
        else:  # DELETE - unsnooze
            pref.is_snoozed = False
            pref.snoozed_until = None
            pref.save()
            return Response({'status': 'unsnoozed'})
    
    @action(detail=True, methods=['post', 'delete'])
    def mark_read(self, request, pk=None):
        alert = self.get_object()
        pref, created = UserAlertPreference.objects.get_or_create(
            user=request.user, alert=alert
        )
        
        if request.method == 'POST':
            pref.is_read = True
            pref.save()
            return Response({'status': 'marked_read'})
        else:  # DELETE - mark as unread
            pref.is_read = False
            pref.save()
            return Response({'status': 'marked_unread'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_alerts(request):
    user = request.user
    filter_type = request.GET.get('filter', '')
    
    # Get alerts based on visibility - only show alerts created by admin users
    alerts_query = Alert.objects.filter(
        Q(visibility_type='organization') |
        Q(visibility_type='team', target_teams=user.team) |
        Q(visibility_type='user', target_users=user),
        is_active=True,
        start_time__lte=timezone.now(),
        expiry_time__gt=timezone.now(),
        created_by__is_admin=True  # Only show alerts created by admin users
    ).distinct().order_by('-created_at')
    
    alert_data = []
    for alert in alerts_query:
        pref = UserAlertPreference.objects.filter(user=user, alert=alert).first()
        is_read = pref.is_read if pref else False
        is_snoozed = pref.is_snooze_active() if pref else False
        
        # Apply filters
        if filter_type == 'read' and not is_read:
            continue
        elif filter_type == 'unread' and is_read:
            continue
        elif filter_type == 'snoozed' and not is_snoozed:
            continue
            
        alert_info = AlertSerializer(alert).data
        alert_info['is_read'] = is_read
        alert_info['is_snoozed'] = is_snoozed
        alert_data.append(alert_info)
    
    return Response(alert_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    user = request.user
    
    user_alerts = Alert.objects.filter(
        Q(visibility_type='organization') |
        Q(visibility_type='team', target_teams=user.team) |
        Q(visibility_type='user', target_users=user),
        is_active=True,
        start_time__lte=timezone.now(),
        expiry_time__gt=timezone.now(),
        created_by__is_admin=True  # Only count alerts created by admin users
    ).distinct()
    
    total_count = user_alerts.count()
    read_count = UserAlertPreference.objects.filter(
        user=user, alert__in=user_alerts, is_read=True
    ).count()
    snoozed_count = UserAlertPreference.objects.filter(
        user=user, alert__in=user_alerts, is_snoozed=True, snoozed_until__gt=timezone.now()
    ).count()
    
    return Response({
        'total_alerts': total_count,
        'read_count': read_count,
        'snoozed_count': snoozed_count
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analytics(request):
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=403)
    
    total_alerts = Alert.objects.count()
    active_alerts = Alert.objects.filter(
        is_active=True,
        expiry_time__gt=timezone.now()
    ).count()
    
    delivered_count = NotificationDelivery.objects.count()
    read_count = UserAlertPreference.objects.filter(is_read=True).count()
    snoozed_count = UserAlertPreference.objects.filter(
        is_snoozed=True,
        snoozed_until__gt=timezone.now()
    ).count()
    
    severity_breakdown = Alert.objects.values('severity').annotate(
        count=Count('id')
    )
    
    return Response({
        'total_alerts': total_alerts,
        'active_alerts': active_alerts,
        'delivered_count': delivered_count,
        'read_count': read_count,
        'snoozed_count': snoozed_count,
        'severity_breakdown': list(severity_breakdown)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_reminders(request):
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=403)
    
    service = NotificationService()
    service.send_reminders()
    return Response({'status': 'reminders_sent'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teams_list(request):
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=403)
    
    teams = Team.objects.all().values('id', 'name')
    return Response(list(teams))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def users_list(request):
    if not request.user.is_admin:
        return Response({'error': 'Admin access required'}, status=403)
    
    users = User.objects.filter(is_active=True).values('id', 'username', 'first_name', 'last_name')
    return Response(list(users))

# Template Views
def user_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and not user.is_admin:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid user credentials')
    return render(request, 'myapp/user_login.html')

@csrf_protect
def admin_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user and user.is_admin:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid admin credentials')
    return render(request, 'myapp/admin_login.html')

@login_required
def dashboard_view(request):
    if request.user.is_admin:
        return render(request, 'myapp/admin_dashboard.html')
    return render(request, 'myapp/user_dashboard.html')

def logout_view(request):
    was_admin = request.user.is_authenticated and request.user.is_admin
    logout(request)
    return redirect('admin_login' if was_admin else 'login')