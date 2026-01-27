# Generated migration for hybrid architecture support

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0001_initial'),
    ]

    operations = [
        # Add is_hardcoded field to BusinessObject
        migrations.AddField(
            model_name='businessobject',
            name='is_hardcoded',
            field=models.BooleanField(
                default=False,
                db_comment='True for core Django models, False for metadata-driven objects'
            ),
        ),
        # Add django_model_path field to BusinessObject
        migrations.AddField(
            model_name='businessobject',
            name='django_model_path',
            field=models.CharField(
                blank=True,
                max_length=200,
                db_comment='Python path to Django model (e.g., apps.assets.models.Asset)'
            ),
        ),
        # Create ModelFieldDefinition model
        migrations.CreateModel(
            name='ModelFieldDefinition',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(db_comment='Soft delete flag', db_index=True, default=False)),
                ('deleted_at', models.DateTimeField(blank=True, db_comment='Timestamp when record was soft deleted', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_comment='Timestamp when record was created')),
                ('updated_at', models.DateTimeField(auto_now=True, db_comment='Timestamp when record was last updated')),
                ('custom_fields', models.JSONField(blank=True, default=dict)),
                ('field_name', models.CharField(max_length=100, db_comment='Actual Django field name')),
                ('display_name', models.CharField(max_length=100, db_comment='Field display name')),
                ('display_name_en', models.CharField(blank=True, max_length=100, db_comment='English display name')),
                ('field_type', models.CharField(max_length=50, db_comment='Mapped field type')),
                ('django_field_type', models.CharField(max_length=50, db_comment='Original Django field type')),
                ('is_required', models.BooleanField(default=False, db_comment='Is field required')),
                ('is_readonly', models.BooleanField(default=False, db_comment='Is field read-only')),
                ('is_editable', models.BooleanField(default=True, db_comment='Is field editable in forms')),
                ('is_unique', models.BooleanField(default=False, db_comment='Is field value unique')),
                ('show_in_list', models.BooleanField(default=True, db_comment='Show in list view')),
                ('show_in_detail', models.BooleanField(default=True, db_comment='Show in detail view')),
                ('show_in_form', models.BooleanField(default=True, db_comment='Show in create/edit forms')),
                ('sort_order', models.IntegerField(default=0, db_comment='Display order')),
                ('reference_model_path', models.CharField(blank=True, max_length=200, db_comment='Referenced model path for ForeignKey')),
                ('reference_display_field', models.CharField(blank=True, default='name', max_length=50, db_comment='Display field for referenced model')),
                ('decimal_places', models.IntegerField(blank=True, null=True, db_comment='Decimal places')),
                ('max_digits', models.IntegerField(blank=True, null=True, db_comment='Maximum digits')),
                ('max_length', models.IntegerField(blank=True, null=True, db_comment='Maximum length')),
                ('business_object', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='model_fields',
                    to='system.businessobject',
                    db_comment='Business object this field belongs to'
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_model_field_definitions',
                    to=settings.AUTH_USER_MODEL
                )),
                ('organization', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='system_model_field_definitions',
                    to='organizations.organization'
                )),
            ],
            options={
                'verbose_name': 'Model Field Definition',
                'verbose_name_plural': 'Model Field Definitions',
                'db_table': 'model_field_definitions',
            },
        ),
        # Add indexes for ModelFieldDefinition
        migrations.AddIndex(
            model_name='modelfielddefinition',
            index=models.Index(fields=['organization', 'business_object', 'field_name'], name='org_obj_field_idx'),
        ),
        migrations.AddIndex(
            model_name='modelfielddefinition',
            index=models.Index(fields=['organization', 'business_object', 'sort_order'], name='org_obj_sort_idx'),
        ),
        migrations.AddIndex(
            model_name='modelfielddefinition',
            index=models.Index(fields=['field_type'], name='field_type_idx'),
        ),
    ]
