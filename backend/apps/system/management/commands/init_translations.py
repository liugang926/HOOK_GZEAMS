# Management command to initialize core translation data
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from apps.system.models import Translation, BusinessObject, DictionaryType, DictionaryItem, ModelFieldDefinition


class Command(BaseCommand):
    help = 'Initialize core translation data for the i18n system'

    def handle(self, *args, **options):
        self.stdout.write('Initializing core translation data...')

        # Get content types
        business_object_ct = ContentType.objects.get_for_model(BusinessObject, for_concrete_model=False)
        dict_type_ct = ContentType.objects.get_for_model(DictionaryType, for_concrete_model=False)
        dict_item_ct = ContentType.objects.get_for_model(DictionaryItem, for_concrete_model=False)
        field_def_ct = ContentType.objects.get_for_model(ModelFieldDefinition, for_concrete_model=False)

        translations_to_create = []
        count = 0

        # 1. Static translations (namespace/key pattern)
        # Common translations
        common_translations = {
            # Actions
            'button.save': {'zh-CN': '保存', 'en-US': 'Save'},
            'button.cancel': {'zh-CN': '取消', 'en-US': 'Cancel'},
            'button.confirm': {'zh-CN': '确定', 'en-US': 'Confirm'},
            'button.add': {'zh-CN': '添加', 'en-US': 'Add'},
            'button.edit': {'zh-CN': '编辑', 'en-US': 'Edit'},
            'button.delete': {'zh-CN': '删除', 'en-US': 'Delete'},
            'button.export': {'zh-CN': '导出', 'en-US': 'Export'},
            'button.import': {'zh-CN': '导入', 'en-US': 'Import'},
            'button.search': {'zh-CN': '查询', 'en-US': 'Search'},
            'button.reset': {'zh-CN': '重置', 'en-US': 'Reset'},
            # Status
            'status.active': {'zh-CN': '启用', 'en-US': 'Active'},
            'status.inactive': {'zh-CN': '停用', 'en-US': 'Inactive'},
            'status.idle': {'zh-CN': '空闲', 'en-US': 'Idle'},
            'status.in_use': {'zh-CN': '使用中', 'en-US': 'In Use'},
            'status.maintenance': {'zh-CN': '维护中', 'en-US': 'Maintenance'},
            # Common labels
            'label.yes': {'zh-CN': '是', 'en-US': 'Yes'},
            'label.no': {'zh-CN': '否', 'en-US': 'No'},
            'label.all': {'zh-CN': '全部', 'en-US': 'All'},
            'label.name': {'zh-CN': '名称', 'en-US': 'Name'},
            'label.code': {'zh-CN': '编码', 'en-US': 'Code'},
            'label.description': {'zh-CN': '描述', 'en-US': 'Description'},
            'label.created_at': {'zh-CN': '创建时间', 'en-US': 'Created At'},
            'label.updated_at': {'zh-CN': '更新时间', 'en-US': 'Updated At'},
            'label.actions': {'zh-CN': '操作', 'en-US': 'Actions'},
        }

        for key, texts in common_translations.items():
            namespace, key = key.split('.', 1)
            for lang_code, text in texts.items():
                translations_to_create.append(
                    Translation(
                        namespace=namespace,
                        key=key,
                        language_code=lang_code,
                        text=text,
                        type='label',
                        is_system=True
                    )
                )

        # 2. Asset status enum translations
        asset_status_translations = {
            'asset.status.idle': {'zh-CN': '空闲', 'en-US': 'Idle'},
            'asset.status.in_use': {'zh-CN': '使用中', 'en-US': 'In Use'},
            'asset.status.maintenance': {'zh-CN': '维护中', 'en-US': 'Maintenance'},
            'asset.status.repair': {'zh-CN': '维修中', 'en-US': 'Under Repair'},
            'asset.status.retired': {'zh-CN': '已退役', 'en-US': 'Retired'},
            'asset.status.lost': {'zh-CN': '已丢失', 'en-US': 'Lost'},
            'asset.status.scrapped': {'zh-CN': '已报废', 'en-US': 'Scrapped'},
        }

        for key, texts in asset_status_translations.items():
            namespace, key = key.split('.', 1)
            for lang_code, text in texts.items():
                translations_to_create.append(
                    Translation(
                        namespace=namespace,
                        key=key,
                        language_code=lang_code,
                        text=text,
                        type='enum',
                        is_system=True
                    )
                )

        # 3. BusinessObject translations (migrate from name_en)
        for obj in BusinessObject.objects.filter(is_deleted=False):
            if obj.name_en:
                # English translation
                if not Translation.objects.filter(
                    content_type=business_object_ct,
                    object_id=obj.pk,
                    field_name='name',
                    language_code='en-US',
                    is_deleted=False
                ).exists():
                    translations_to_create.append(
                        Translation(
                            content_type=business_object_ct,
                            object_id=obj.pk,
                            field_name='name',
                            language_code='en-US',
                            text=obj.name_en,
                            type='object_field',
                            is_system=True
                        )
                    )

        # 4. DictionaryType translations (migrate from name_en)
        for obj in DictionaryType.objects.filter(is_deleted=False):
            if obj.name_en:
                if not Translation.objects.filter(
                    content_type=dict_type_ct,
                    object_id=obj.pk,
                    field_name='name',
                    language_code='en-US',
                    is_deleted=False
                ).exists():
                    translations_to_create.append(
                        Translation(
                            content_type=dict_type_ct,
                            object_id=obj.pk,
                            field_name='name',
                            language_code='en-US',
                            text=obj.name_en,
                            type='object_field',
                            is_system=True
                        )
                    )

        # 5. DictionaryItem translations (migrate from name_en)
        for obj in DictionaryItem.objects.filter(is_deleted=False):
            if obj.name_en:
                if not Translation.objects.filter(
                    content_type=dict_item_ct,
                    object_id=obj.pk,
                    field_name='name',
                    language_code='en-US',
                    is_deleted=False
                ).exists():
                    translations_to_create.append(
                        Translation(
                            content_type=dict_item_ct,
                            object_id=obj.pk,
                            field_name='name',
                            language_code='en-US',
                            text=obj.name_en,
                            type='object_field',
                            is_system=True
                        )
                    )

        # Bulk create
        if translations_to_create:
            Translation.objects.bulk_create(translations_to_create, batch_size=500)
            count = len(translations_to_create)
            self.stdout.write(self.style.SUCCESS(f'Created {count} translations.'))
        else:
            self.stdout.write(self.style.WARNING('No new translations to create.'))

        self.stdout.write(self.style.SUCCESS('Translation initialization complete.'))
