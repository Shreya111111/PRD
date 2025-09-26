from django.core.management.base import BaseCommand
from myapp.models import User

class Command(BaseCommand):
    help = 'Create admin user'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_user(
                username='admin',
                password='admin123',
                is_admin=True,
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write('Admin user created: username=admin, password=admin123')
        else:
            self.stdout.write('Admin user already exists')