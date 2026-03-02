# Management command to initialize Language data
from django.core.management.base import BaseCommand
from apps.system.models import Language


class Command(BaseCommand):
    help = 'Initialize Language data for the i18n system'

    def handle(self, *args, **options):
        self.stdout.write('Initializing Language data...')

        # Define supported languages
        languages = [
            {
                'code': 'zh-CN',
                'name': 'Chinese (Simplified)',
                'native_name': '简体中文',
                'flag_emoji': '🇨🇳',
                'locale': 'zhCN',
                'sort_order': 0,
                'is_default': True,
                'is_active': True
            },
            {
                'code': 'en-US',
                'name': 'English (US)',
                'native_name': 'English',
                'flag_emoji': '🇺🇸',
                'locale': 'enUS',
                'sort_order': 1,
                'is_default': False,
                'is_active': True
            },
            {
                'code': 'ja-JP',
                'name': 'Japanese',
                'native_name': '日本語',
                'flag_emoji': '🇯🇵',
                'locale': 'jaJP',
                'sort_order': 2,
                'is_default': False,
                'is_active': False  # Disabled by default until translations are ready
            }
        ]

        created_count = 0
        updated_count = 0

        for lang_data in languages:
            code = lang_data.pop('code')
            obj, created = Language.objects.update_or_create(
                code=code,
                defaults=lang_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  Created language: {code} - {lang_data["name"]}')
            else:
                updated_count += 1
                self.stdout.write(f'  Updated language: {code} - {lang_data["name"]}')

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Created {created_count} languages.'))
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} languages.'))

        if created_count == 0 and updated_count == 0:
            self.stdout.write(self.style.WARNING('No languages were created or updated.'))

        self.stdout.write(self.style.SUCCESS('Language initialization complete.'))
