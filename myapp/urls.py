from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'alerts', views.AlertViewSet)

urlpatterns = [
    # Template views
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.user_login_view, name='login'),
    path('user/login/', views.user_login_view, name='user_login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/user-alerts/', views.user_alerts, name='user-alerts'),
    path('api/dashboard-stats/', views.dashboard_stats, name='dashboard-stats'),
    path('api/analytics/', views.analytics, name='analytics'),
    path('api/trigger-reminders/', views.trigger_reminders, name='trigger-reminders'),
    path('api/teams/', views.teams_list, name='teams-list'),
    path('api/users/', views.users_list, name='users-list'),
]