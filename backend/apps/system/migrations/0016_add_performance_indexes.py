"""
Migration to add performance indexes for JSONB fields and common queries.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0015_add_config_package_models'),
    ]

    operations = [
        # GIN index for dynamic_fields JSONB on DynamicData (if using PostgreSQL)
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                -- Create GIN index on dynamic_fields for JSONB containment queries
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_dynamic_data_fields_gin'
                ) THEN
                    CREATE INDEX idx_dynamic_data_fields_gin 
                    ON dynamic_data USING GIN (dynamic_fields);
                END IF;
                
                -- Create index on status field within dynamic_fields
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_dynamic_data_status'
                ) THEN
                    CREATE INDEX idx_dynamic_data_status 
                    ON dynamic_data USING BTREE ((dynamic_fields->>'status'));
                END IF;
                
                -- Create index for common ordering by created_at
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_dynamic_data_created_desc'
                ) THEN
                    CREATE INDEX idx_dynamic_data_created_desc 
                    ON dynamic_data (created_at DESC);
                END IF;
                
                -- Create composite index for business_object + created_at
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_dynamic_data_bo_created'
                ) THEN
                    CREATE INDEX idx_dynamic_data_bo_created 
                    ON dynamic_data (business_object_id, created_at DESC);
                END IF;
                
            END $$;
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS idx_dynamic_data_fields_gin;
            DROP INDEX IF EXISTS idx_dynamic_data_status;
            DROP INDEX IF EXISTS idx_dynamic_data_created_desc;
            DROP INDEX IF EXISTS idx_dynamic_data_bo_created;
            """
        ),

        # GIN index for layout_config JSONB on PageLayout
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_page_layout_config_gin'
                ) THEN
                    CREATE INDEX idx_page_layout_config_gin 
                    ON page_layouts USING GIN (layout_config);
                END IF;
            END $$;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_page_layout_config_gin;"
        ),

        # GIN index for condition JSONB on BusinessRule
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_business_rule_condition_gin'
                ) THEN
                    CREATE INDEX idx_business_rule_condition_gin 
                    ON business_rules USING GIN (condition);
                END IF;
            END $$;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_business_rule_condition_gin;"
        ),

        # Index for FieldDefinition lookups
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_field_def_bo_order'
                ) THEN
                    CREATE INDEX idx_field_def_bo_order 
                    ON field_definitions (business_object_id, sort_order);
                END IF;
            END $$;
            """,
            reverse_sql="DROP INDEX IF EXISTS idx_field_def_bo_order;"
        ),
    ]
