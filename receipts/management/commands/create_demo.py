from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Создаёт демо-пользователя для входа в личный кабинет'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'elena'
        email = 'naneuser@email.com'
        password = 'demo12345'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Елена',
                'last_name': 'Иванова',
            },
        )
        user.email = email
        user.first_name = 'Елена'
        user.last_name = 'Иванова'
        user.set_password(password)
        user.save()
        action = 'создан' if created else 'обновлён'
        self.stdout.write(self.style.SUCCESS(
            f'Демо-пользователь {action}: {username} / {password}'
        ))
