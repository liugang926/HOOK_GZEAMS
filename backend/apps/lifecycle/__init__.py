"""
Lifecycle Management App

Manages the complete asset lifecycle from procurement to disposal:
- Purchase Request: Asset procurement requests with approval workflow
- Asset Receipt: Goods receipt with quality inspection and asset card generation
- Maintenance: Repair requests, technician assignment, and maintenance plans/tasks
- Disposal: Asset disposal with technical appraisal and execution
"""
default_app_config = 'apps.lifecycle.apps.LifecycleConfig'
