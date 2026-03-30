# Generated manually for Phase 7.3 asset tag system.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0011_returnitem_project_allocation"),
        ("organizations", "0005_add_base_model_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TagGroup",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_deleted",
                    models.BooleanField(
                        db_comment="Soft delete flag, records are filtered out by default",
                        db_index=True,
                        default=False,
                        verbose_name="Is Deleted",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_comment="Timestamp when record was soft deleted",
                        null=True,
                        verbose_name="Deleted At",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_comment="Timestamp when record was created",
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_comment="Timestamp when record was last updated",
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "custom_fields",
                    models.JSONField(
                        blank=True,
                        db_comment="Dynamic fields for metadata-driven extensions",
                        default=dict,
                        verbose_name="Custom Fields",
                    ),
                ),
                ("name", models.CharField(help_text="Tag group name", max_length=100)),
                (
                    "code",
                    models.CharField(
                        db_index=True,
                        help_text="Unique tag group code within the organization",
                        max_length=50,
                    ),
                ),
                ("description", models.TextField(blank=True, help_text="Tag group description")),
                (
                    "color",
                    models.CharField(
                        default="#409EFF",
                        help_text="Default color for the tag group",
                        max_length=20,
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        blank=True,
                        help_text="Optional icon name for the tag group",
                        max_length=50,
                    ),
                ),
                (
                    "sort_order",
                    models.IntegerField(default=0, help_text="Display order for the tag group"),
                ),
                (
                    "is_system",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the tag group is system managed",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, help_text="Whether the tag group is active"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who created this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who soft deleted this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_deleted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted By",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        db_comment="Organization for multi-tenant data isolation",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_set",
                        to="organizations.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who last updated this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated By",
                    ),
                ),
            ],
            options={
                "verbose_name": "Asset Tag Group",
                "verbose_name_plural": "Asset Tag Groups",
                "db_table": "asset_tag_groups",
                "ordering": ["sort_order", "name", "id"],
                "indexes": [
                    models.Index(fields=["organization", "code"], name="asset_tag_group_org_code_idx"),
                    models.Index(fields=["organization", "is_active"], name="asset_tag_group_org_active_idx"),
                    models.Index(fields=["organization", "sort_order"], name="asset_tag_group_org_sort_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(is_deleted=False),
                        fields=("organization", "code"),
                        name="uniq_asset_tg_group_code_org",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AssetTag",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_deleted",
                    models.BooleanField(
                        db_comment="Soft delete flag, records are filtered out by default",
                        db_index=True,
                        default=False,
                        verbose_name="Is Deleted",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_comment="Timestamp when record was soft deleted",
                        null=True,
                        verbose_name="Deleted At",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_comment="Timestamp when record was created",
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_comment="Timestamp when record was last updated",
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "custom_fields",
                    models.JSONField(
                        blank=True,
                        db_comment="Dynamic fields for metadata-driven extensions",
                        default=dict,
                        verbose_name="Custom Fields",
                    ),
                ),
                ("name", models.CharField(help_text="Tag display name", max_length=50)),
                (
                    "code",
                    models.CharField(
                        db_index=True,
                        help_text="Unique tag code within the tag group",
                        max_length=50,
                    ),
                ),
                (
                    "color",
                    models.CharField(
                        blank=True,
                        help_text="Optional tag color override",
                        max_length=20,
                    ),
                ),
                (
                    "icon",
                    models.CharField(
                        blank=True,
                        help_text="Optional tag icon name",
                        max_length=50,
                    ),
                ),
                ("description", models.TextField(blank=True, help_text="Tag description")),
                (
                    "sort_order",
                    models.IntegerField(default=0, help_text="Display order inside the tag group"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, help_text="Whether the tag is active"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who created this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who soft deleted this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_deleted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted By",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        db_comment="Organization for multi-tenant data isolation",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_set",
                        to="organizations.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "tag_group",
                    models.ForeignKey(
                        help_text="Owning tag group",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="tags",
                        to="assets.taggroup",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who last updated this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated By",
                    ),
                ),
            ],
            options={
                "verbose_name": "Asset Tag",
                "verbose_name_plural": "Asset Tags",
                "db_table": "asset_tags",
                "ordering": ["tag_group__sort_order", "sort_order", "name", "id"],
                "indexes": [
                    models.Index(fields=["organization", "code"], name="asset_tag_org_code_idx"),
                    models.Index(fields=["organization", "tag_group"], name="asset_tag_org_group_idx"),
                    models.Index(fields=["organization", "is_active"], name="asset_tag_org_active_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(is_deleted=False),
                        fields=("organization", "tag_group", "code"),
                        name="uniq_asset_tag_code_group_org",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="AssetTagRelation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_deleted",
                    models.BooleanField(
                        db_comment="Soft delete flag, records are filtered out by default",
                        db_index=True,
                        default=False,
                        verbose_name="Is Deleted",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_comment="Timestamp when record was soft deleted",
                        null=True,
                        verbose_name="Deleted At",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_comment="Timestamp when record was created",
                        verbose_name="Created At",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        db_comment="Timestamp when record was last updated",
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "custom_fields",
                    models.JSONField(
                        blank=True,
                        db_comment="Dynamic fields for metadata-driven extensions",
                        default=dict,
                        verbose_name="Custom Fields",
                    ),
                ),
                (
                    "tagged_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when the tag was added",
                    ),
                ),
                (
                    "notes",
                    models.CharField(
                        blank=True,
                        help_text="Optional tagging notes",
                        max_length=200,
                    ),
                ),
                (
                    "asset",
                    models.ForeignKey(
                        help_text="Tagged asset",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="asset_tag_relations",
                        to="assets.asset",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who created this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Created By",
                    ),
                ),
                (
                    "deleted_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who soft deleted this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_deleted",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Deleted By",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        blank=True,
                        db_comment="Organization for multi-tenant data isolation",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_set",
                        to="organizations.organization",
                        verbose_name="Organization",
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        help_text="Assigned tag",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="asset_relations",
                        to="assets.assettag",
                    ),
                ),
                (
                    "tagged_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who added the tag",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="asset_tag_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        db_comment="User who last updated this record",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(app_label)s_%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Updated By",
                    ),
                ),
            ],
            options={
                "verbose_name": "Asset Tag Relation",
                "verbose_name_plural": "Asset Tag Relations",
                "db_table": "asset_tag_relations",
                "ordering": ["-tagged_at", "-created_at", "id"],
                "indexes": [
                    models.Index(fields=["organization", "asset"], name="asset_tag_rel_org_asset_idx"),
                    models.Index(fields=["organization", "tag"], name="asset_tag_rel_org_tag_idx"),
                    models.Index(fields=["organization", "tagged_at"], name="asset_tag_rel_org_tagged_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(is_deleted=False),
                        fields=("organization", "asset", "tag"),
                        name="uniq_asset_tag_rel_org_pair",
                    ),
                ],
            },
        ),
    ]
