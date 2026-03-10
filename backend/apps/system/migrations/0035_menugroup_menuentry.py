from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('system', '0034_restore_activitylog'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(db_comment='Soft delete flag, records are filtered out by default', db_index=True, default=False, verbose_name='Is Deleted')),
                ('deleted_at', models.DateTimeField(blank=True, db_comment='Timestamp when record was soft deleted', null=True, verbose_name='Deleted At')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_comment='Timestamp when record was created', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, db_comment='Timestamp when record was last updated', verbose_name='Updated At')),
                ('custom_fields', models.JSONField(blank=True, db_comment='Dynamic fields for metadata-driven extensions', default=dict, verbose_name='Custom Fields')),
                ('code', models.CharField(db_comment='Stable menu group code', db_index=True, max_length=100, unique=True)),
                ('name', models.CharField(db_comment='Display name or fallback translation label', max_length=100)),
                ('translation_key', models.CharField(blank=True, db_comment='Optional i18n key for group label', max_length=200)),
                ('icon', models.CharField(db_comment='Element Plus icon', default='Menu', max_length=100)),
                ('sort_order', models.PositiveIntegerField(db_comment='Display order', default=999)),
                ('is_visible', models.BooleanField(db_comment='Whether this group is visible in the navigation', default=True)),
                ('is_locked', models.BooleanField(db_comment='Locked groups cannot be deleted', default=False)),
                ('is_system', models.BooleanField(db_comment='Default system group', default=False)),
                ('created_by', models.ForeignKey(blank=True, db_comment='User who created this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_menugroup_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('deleted_by', models.ForeignKey(blank=True, db_comment='User who soft deleted this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_menugroup_deleted', to=settings.AUTH_USER_MODEL, verbose_name='Deleted By')),
                ('organization', models.ForeignKey(blank=True, db_comment='Organization for multi-tenant data isolation', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='system_menugroup_set', to='organizations.organization', verbose_name='Organization')),
                ('updated_by', models.ForeignKey(blank=True, db_comment='User who last updated this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_menugroup_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'verbose_name': 'Menu Group',
                'verbose_name_plural': 'Menu Groups',
                'db_table': 'menu_groups',
                'ordering': ['sort_order', 'code'],
            },
        ),
        migrations.CreateModel(
            name='MenuEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(db_comment='Soft delete flag, records are filtered out by default', db_index=True, default=False, verbose_name='Is Deleted')),
                ('deleted_at', models.DateTimeField(blank=True, db_comment='Timestamp when record was soft deleted', null=True, verbose_name='Deleted At')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_comment='Timestamp when record was created', verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, db_comment='Timestamp when record was last updated', verbose_name='Updated At')),
                ('custom_fields', models.JSONField(blank=True, db_comment='Dynamic fields for metadata-driven extensions', default=dict, verbose_name='Custom Fields')),
                ('source_type', models.CharField(choices=[('business_object', 'Business Object'), ('static', 'Static Page')], db_comment='Entry source type', db_index=True, max_length=30)),
                ('source_code', models.CharField(db_comment='Stable source identifier', db_index=True, max_length=100)),
                ('code', models.CharField(db_comment='Menu entry code', db_index=True, max_length=100)),
                ('name', models.CharField(db_comment='Display name fallback', max_length=100)),
                ('name_en', models.CharField(blank=True, db_comment='English display name fallback', max_length=100)),
                ('translation_key', models.CharField(blank=True, db_comment='Optional i18n key for entry label', max_length=200)),
                ('route_path', models.CharField(db_comment='Frontend route path', max_length=255)),
                ('icon', models.CharField(db_comment='Element Plus icon', default='Document', max_length=100)),
                ('sort_order', models.PositiveIntegerField(db_comment='Display order within the group', default=999)),
                ('is_visible', models.BooleanField(db_comment='Whether this entry is visible in the navigation', default=True)),
                ('is_locked', models.BooleanField(db_comment='Locked entries cannot be deleted', default=False)),
                ('is_system', models.BooleanField(db_comment='Default system entry', default=False)),
                ('business_object', models.ForeignKey(blank=True, db_comment='Linked business object for dynamic entries', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='menu_entries', to='system.businessobject')),
                ('created_by', models.ForeignKey(blank=True, db_comment='User who created this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_menuentry_created', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('deleted_by', models.ForeignKey(blank=True, db_comment='User who soft deleted this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_menuentry_deleted', to=settings.AUTH_USER_MODEL, verbose_name='Deleted By')),
                ('menu_group', models.ForeignKey(db_comment='Owning menu group', on_delete=django.db.models.deletion.PROTECT, related_name='entries', to='system.menugroup')),
                ('organization', models.ForeignKey(blank=True, db_comment='Organization for multi-tenant data isolation', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='system_menuentry_set', to='organizations.organization', verbose_name='Organization')),
                ('updated_by', models.ForeignKey(blank=True, db_comment='User who last updated this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='system_menuentry_updated', to=settings.AUTH_USER_MODEL, verbose_name='Updated By')),
            ],
            options={
                'verbose_name': 'Menu Entry',
                'verbose_name_plural': 'Menu Entries',
                'db_table': 'menu_entries',
                'ordering': ['menu_group__sort_order', 'sort_order', 'code'],
            },
        ),
        migrations.AddIndex(
            model_name='menugroup',
            index=models.Index(fields=['-created_at'], name='menu_groups_created_at_b0fe26_idx'),
        ),
        migrations.AddIndex(
            model_name='menugroup',
            index=models.Index(fields=['is_deleted'], name='menu_groups_is_delet_b80cab_idx'),
        ),
        migrations.AddIndex(
            model_name='menugroup',
            index=models.Index(fields=['code'], name='menu_groups_code_b81254_idx'),
        ),
        migrations.AddIndex(
            model_name='menugroup',
            index=models.Index(fields=['sort_order'], name='menu_groups_sort_or_7b5ca8_idx'),
        ),
        migrations.AddIndex(
            model_name='menugroup',
            index=models.Index(fields=['is_visible'], name='menu_groups_is_visi_2da8d0_idx'),
        ),
        migrations.AddIndex(
            model_name='menuentry',
            index=models.Index(fields=['-created_at'], name='menu_entries_created_8d1592_idx'),
        ),
        migrations.AddIndex(
            model_name='menuentry',
            index=models.Index(fields=['is_deleted'], name='menu_entries_is_dele_56430b_idx'),
        ),
        migrations.AddIndex(
            model_name='menuentry',
            index=models.Index(fields=['source_type', 'source_code'], name='menu_entries_source__726de6_idx'),
        ),
        migrations.AddIndex(
            model_name='menuentry',
            index=models.Index(fields=['code'], name='menu_entries_code_4f4f4e_idx'),
        ),
        migrations.AddIndex(
            model_name='menuentry',
            index=models.Index(fields=['sort_order'], name='menu_entries_sort_o_a47a61_idx'),
        ),
        migrations.AddIndex(
            model_name='menuentry',
            index=models.Index(fields=['is_visible'], name='menu_entries_is_vis_857d1d_idx'),
        ),
        migrations.AddConstraint(
            model_name='menuentry',
            constraint=models.UniqueConstraint(fields=('source_type', 'source_code'), name='uniq_menu_entry_source'),
        ),
    ]
