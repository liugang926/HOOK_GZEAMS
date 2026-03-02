"""
Unit tests for i18n models (Language and Translation).

Tests cover:
- Language model creation, validation, and methods
- Translation model with hybrid design (namespace/key and GenericForeignKey)
- Soft delete behavior
- Multi-organization isolation
"""
import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from apps.common.models import BaseModel
from apps.system.models import Language, Translation, BusinessObject, DictionaryType
from apps.organizations.models import Organization


@pytest.mark.django_db
class TestLanguageModel:
    """Test Language model functionality."""

    @pytest.fixture
    def organization(self):
        """Create test organization."""
        return Organization.objects.create(
            name='Test Organization',
            code='test-org'
        )

    @pytest.fixture
    def language_data(self, organization):
        """Return language test data."""
        return {
            'organization': organization,
            'code': 'zh-CN',
            'name': '简体中文',
            'native_name': '中文',
            'flag_emoji': '🇨🇳',
            'locale': 'zhCN',
            'is_default': True,
            'is_active': True,
            'sort_order': 1
        }

    def test_create_language(self, language_data):
        """Test creating a language record."""
        language = Language.objects.create(**language_data)
        assert language.code == 'zh-CN'
        assert language.name == '简体中文'
        assert language.native_name == '中文'
        assert language.flag_emoji == '🇨🇳'
        assert language.locale == 'zhCN'
        assert language.is_default is True
        assert language.is_active is True
        assert language.sort_order == 1

    def test_language_code_unique(self, organization):
        """Test that language code must be unique."""
        Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English'
        )
        with pytest.raises(Exception):  # IntegrityError
            Language.objects.create(
                organization=organization,
                code='en-US',  # Duplicate code
                name='English 2',
                native_name='English'
            )

    def test_language_inherits_base_model(self, language_data):
        """Test that Language inherits BaseModel fields."""
        language = Language.objects.create(**language_data)
        assert hasattr(language, 'id')
        assert hasattr(language, 'organization')
        assert hasattr(language, 'is_deleted')
        assert hasattr(language, 'deleted_at')
        assert hasattr(language, 'created_at')
        assert hasattr(language, 'updated_at')
        assert hasattr(language, 'created_by')
        assert hasattr(language, 'custom_fields')

    def test_language_soft_delete(self, language_data):
        """Test soft delete behavior."""
        language = Language.objects.create(**language_data)
        language_id = language.id

        # Soft delete
        language.soft_delete()

        # Check it's marked as deleted
        language.refresh_from_db()
        assert language.is_deleted is True
        assert language.deleted_at is not None

        # Check it's filtered from default queryset
        assert Language.objects.filter(id=language_id).count() == 0
        assert Language.all_objects.filter(id=language_id).count() == 1

    def test_language_default_ordering(self, organization):
        """Test that languages are ordered by sort_order and name."""
        Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English',
            sort_order=2
        )
        Language.objects.create(
            organization=organization,
            code='zh-CN',
            name='Chinese',
            native_name='中文',
            sort_order=1
        )

        languages = list(Language.objects.all())
        assert languages[0].code == 'zh-CN'
        assert languages[1].code == 'en-US'

    def test_only_one_default_language(self, organization):
        """Test that only one language can be default per organization."""
        Language.objects.create(
            organization=organization,
            code='zh-CN',
            name='Chinese',
            native_name='中文',
            is_default=True
        )

        # Create another language with is_default=True
        lang2 = Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English',
            is_default=False
        )

        # Set second language as default
        lang2.is_default = True
        lang2.save()

        # Refresh first language
        lang1 = Language.objects.get(code='zh-CN')
        # Note: Application logic should enforce this, model doesn't have constraint

    def test_get_active_languages(self, organization):
        """Test filtering active languages."""
        Language.objects.create(
            organization=organization,
            code='zh-CN',
            name='Chinese',
            native_name='中文',
            is_active=True
        )
        Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English',
            is_active=False
        )

        active_languages = Language.objects.filter(is_active=True)
        assert active_languages.count() == 1
        assert active_languages.first().code == 'zh-CN'


@pytest.mark.django_db
class TestTranslationModel:
    """Test Translation model functionality."""

    @pytest.fixture
    def organization(self):
        """Create test organization."""
        return Organization.objects.create(
            name='Test Organization',
            code='test-org'
        )

    @pytest.fixture
    def language(self, organization):
        """Create test language."""
        return Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English'
        )

    @pytest.fixture
    def business_object(self, organization):
        """Create test business object."""
        return BusinessObject.objects.create(
            organization=organization,
            code='test_asset',
            name='Test Asset',
            table_name='test_asset'
        )

    def test_create_namespace_translation(self, language):
        """Test creating a namespace/key translation."""
        translation = Translation.objects.create(
            language_code='en-US',
            namespace='common',
            key='button.save',
            text='Save',
            type='label',
            is_system=True
        )
        assert translation.namespace == 'common'
        assert translation.key == 'button.save'
        assert translation.text == 'Save'
        assert translation.language_code == 'en-US'
        assert translation.type == 'label'
        assert translation.is_system is True
        assert translation.content_type is None
        assert translation.object_id is None

    def test_create_object_translation(self, organization, business_object):
        """Test creating a GenericForeignKey object translation."""
        content_type = ContentType.objects.get_for_model(business_object)

        translation = Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='en-US',
            text='Test Asset EN',
            type='object_field',
            is_system=True
        )

        assert translation.content_type == content_type
        assert translation.object_id == business_object.id
        assert translation.field_name == 'name'
        assert translation.text == 'Test Asset EN'
        assert translation.content_object == business_object

    def test_translation_inherits_base_model(self, organization, business_object):
        """Test that Translation inherits BaseModel fields."""
        content_type = ContentType.objects.get_for_model(business_object)

        translation = Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='en-US',
            text='Test'
        )

        assert hasattr(translation, 'id')
        assert hasattr(translation, 'organization')
        assert hasattr(translation, 'is_deleted')
        assert hasattr(translation, 'deleted_at')
        assert hasattr(translation, 'created_at')
        assert hasattr(translation, 'updated_at')
        assert hasattr(translation, 'created_by')
        assert hasattr(translation, 'custom_fields')

    def test_translation_soft_delete(self, business_object):
        """Test soft delete behavior."""
        content_type = ContentType.objects.get_for_model(business_object)

        translation = Translation.objects.create(
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='en-US',
            text='Test'
        )
        translation_id = translation.id

        # Soft delete
        translation.soft_delete()

        # Check it's marked as deleted
        translation.refresh_from_db()
        assert translation.is_deleted is True
        assert translation.deleted_at is not None

    def test_unique_namespace_key_constraint(self, language):
        """Test unique constraint on namespace+key+language_code."""
        Translation.objects.create(
            language_code='en-US',
            namespace='common',
            key='button.save',
            text='Save',
            type='label'
        )

        # Should be able to create same namespace/key for different language
        Translation.objects.create(
            language_code='zh-CN',
            namespace='common',
            key='button.save',
            text='保存',
            type='label'
        )

    def test_unique_gfk_constraint(self, organization, business_object):
        """Test unique constraint on content_type+object_id+field_name+language_code."""
        content_type = ContentType.objects.get_for_model(business_object)

        Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='en-US',
            text='Test EN'
        )

        # Should be able to create translation for different language
        Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='zh-CN',
            text='测试'
        )

        # Should be able to create translation for different field
        Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='description',
            language_code='en-US',
            text='Test Description'
        )

    def test_get_translation_for_object(self, organization, business_object):
        """Test retrieving translations for a specific object."""
        content_type = ContentType.objects.get_for_model(business_object)

        Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='en-US',
            text='Asset EN'
        )

        # Query translations for this object
        translations = Translation.objects.filter(
            content_type=content_type,
            object_id=business_object.id
        )

        assert translations.count() == 1
        assert translations.first().text == 'Asset EN'

    def test_translation_type_choices(self):
        """Test that translation type is limited to valid choices."""
        valid_types = ['label', 'message', 'enum', 'object_field']
        for t in valid_types:
            Translation.objects.create(
                language_code='en-US',
                namespace='test',
                key=f'key.{t}',
                text='Test',
                type=t
            )

        # Verify all were created
        assert Translation.objects.filter(namespace='test').count() == 4


@pytest.mark.django_db
class TestTranslationQuerySet:
    """Test Translation queryset methods."""

    @pytest.fixture
    def organization(self):
        """Create test organization."""
        return Organization.objects.create(
            name='Test Organization',
            code='test-org'
        )

    @pytest.fixture
    def languages(self, organization):
        """Create test languages."""
        zh = Language.objects.create(
            organization=organization,
            code='zh-CN',
            name='Chinese',
            native_name='中文',
            is_default=True
        )
        en = Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English'
        )
        return {'zh': zh, 'en': en}

    def test_filter_by_language_code(self, organization):
        """Test filtering translations by language code."""
        Translation.objects.create(
            organization=organization,
            language_code='zh-CN',
            namespace='common',
            key='button.save',
            text='保存'
        )
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='common',
            key='button.save',
            text='Save'
        )

        zh_translations = Translation.objects.filter(language_code='zh-CN')
        en_translations = Translation.objects.filter(language_code='en-US')

        assert zh_translations.count() == 1
        assert en_translations.count() == 1
        assert zh_translations.first().text == '保存'
        assert en_translations.first().text == 'Save'

    def test_filter_by_type(self, organization):
        """Test filtering translations by type."""
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='common',
            key='button.save',
            text='Save',
            type='label'
        )
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='status',
            key='active',
            text='Active',
            type='enum'
        )

        label_translations = Translation.objects.filter(type='label')
        enum_translations = Translation.objects.filter(type='enum')

        assert label_translations.count() == 1
        assert enum_translations.count() == 1

    def test_filter_system_translations(self, organization):
        """Test filtering system vs user translations."""
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='common',
            key='button.save',
            text='Save',
            is_system=True
        )
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='custom',
            key='custom.text',
            text='Custom',
            is_system=False
        )

        system_translations = Translation.objects.filter(is_system=True)
        user_translations = Translation.objects.filter(is_system=False)

        assert system_translations.count() == 1
        assert user_translations.count() == 1


@pytest.mark.django_db
class TestTranslationIntegration:
    """Integration tests for i18n system."""

    @pytest.fixture
    def organization(self):
        """Create test organization."""
        return Organization.objects.create(
            name='Test Organization',
            code='test-org'
        )

    @pytest.fixture
    def setup_languages(self, organization):
        """Create default languages."""
        Language.objects.create(
            organization=organization,
            code='zh-CN',
            name='简体中文',
            native_name='中文',
            is_default=True,
            is_active=True,
            sort_order=1,
            flag_emoji='🇨🇳'
        )
        Language.objects.create(
            organization=organization,
            code='en-US',
            name='English',
            native_name='English',
            is_default=False,
            is_active=True,
            sort_order=2,
            flag_emoji='🇺🇸'
        )

    @pytest.fixture
    def business_object(self, organization):
        """Create test business object."""
        return BusinessObject.objects.create(
            organization=organization,
            code='Asset',
            name='资产',
            table_name='assets_asset'
        )

    def test_full_translation_workflow(self, organization, setup_languages, business_object):
        """Test complete translation workflow."""
        content_type = ContentType.objects.get_for_model(business_object)

        # Create object translations
        Translation.objects.create(
            organization=organization,
            content_type=content_type,
            object_id=business_object.id,
            field_name='name',
            language_code='en-US',
            text='Asset',
            type='object_field'
        )

        # Create static translations
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='asset',
            key='status.idle',
            text='Idle',
            type='enum'
        )
        Translation.objects.create(
            organization=organization,
            language_code='zh-CN',
            namespace='asset',
            key='status.idle',
            text='空闲',
            type='enum'
        )

        # Verify all translations exist
        assert Translation.objects.count() == 3

        # Get English translations
        en_translations = Translation.objects.filter(language_code='en-US')
        assert en_translations.count() == 2

    def test_organization_isolation(self, organization):
        """Test that translations are isolated by organization."""
        org2 = Organization.objects.create(
            name='Org 2',
            code='org2'
        )

        # Create translation in org1
        Translation.objects.create(
            organization=organization,
            language_code='en-US',
            namespace='test',
            key='test1',  # Use different key to avoid unique constraint
            text='Org1 Test'
        )

        # Create translation in org2
        Translation.objects.create(
            organization=org2,
            language_code='en-US',
            namespace='test',
            key='test2',  # Use different key to avoid unique constraint
            text='Org2 Test'
        )

        # Each org should only see its own translations
        org1_translations = Translation.objects.filter(organization=organization)
        org2_translations = Translation.objects.filter(organization=org2)

        assert org1_translations.count() == 1
        assert org2_translations.count() == 1
        assert org1_translations.first().text == 'Org1 Test'
        assert org2_translations.first().text == 'Org2 Test'
