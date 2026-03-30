# Generated manually for Phase 7.3 asset tag assignments.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("organizations", "0005_add_base_model_fields"),
        ("system", "0052_closedloopdashboardsnapshot"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="TagAssignment",
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
                    "object_id",
                    models.UUIDField(
                        db_comment="Target record ID",
                        db_index=True,
                    ),
                ),
                (
                    "biz_type",
                    models.CharField(
                        db_comment="Target business object code",
                        db_index=True,
                        max_length=50,
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        db_comment="Target model content type",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="system_tag_assignments",
                        to="contenttypes.contenttype",
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
                        db_comment="Assigned tag",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assignments",
                        to="system.tag",
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
                "verbose_name": "Tag Assignment",
                "verbose_name_plural": "Tag Assignments",
                "db_table": "tag_assignments",
                "unique_together": {("organization", "tag", "content_type", "object_id")},
                "indexes": [
                    models.Index(
                        fields=["organization", "tag"],
                        name="tag_assignme_organiz_28e2da_idx",
                    ),
                    models.Index(
                        fields=["organization", "biz_type"],
                        name="tag_assignme_organiz_1df73a_idx",
                    ),
                    models.Index(
                        fields=["organization", "content_type", "object_id"],
                        name="tag_assignme_organiz_c92a07_idx",
                    ),
                ],
            },
        ),
    ]
