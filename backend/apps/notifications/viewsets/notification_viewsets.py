"""
Notification ViewSets

ViewSets for all notification models with proper inheritance from
BaseModelViewSet and custom actions for notification operations.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from apps.common.viewsets.base import BaseModelViewSet, BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.notifications.models import (
    NotificationTemplate,
    Notification,
    NotificationLog,
    NotificationConfig,
    NotificationChannel,
    NotificationMessage,
    InAppMessage,
)
from apps.notifications.serializers import (
    NotificationTemplateSerializer,
    NotificationTemplateDetailSerializer,
    NotificationSerializer,
    NotificationListSerializer,
    NotificationLogSerializer,
    NotificationConfigSerializer,
    NotificationConfigUpdateSerializer,
    SendNotificationSerializer,
    BatchSendNotificationSerializer,
    NotificationChannelSerializer,
    NotificationChannelUpdateSerializer,
    NotificationChannelTestSerializer,
    NotificationMessageSerializer,
    NotificationMessageListSerializer,
    NotificationMessageCreateSerializer,
    NotificationMessageSendSerializer,
    InAppMessageSerializer,
    InAppMessageListSerializer,
    InAppMessageCreateSerializer,
    InAppMessageActionSerializer,
)
from apps.notifications.filters import (
    NotificationTemplateFilter,
    NotificationFilter,
    NotificationLogFilter,
    NotificationConfigFilter,
)
from apps.notifications.services import notification_service, template_service


class NotificationTemplateViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for NotificationTemplate model.

    Provides:
    - Standard CRUD operations
    - Template preview
    - Version management
    - Batch operations
    """

    queryset = NotificationTemplate.objects.all()
    filterset_class = NotificationTemplateFilter
    search_fields = ['template_code', 'template_name', 'description']
    ordering_fields = ['template_code', 'template_type', 'channel', 'version', 'created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return NotificationTemplateDetailSerializer
        return NotificationTemplateSerializer

    def get_permissions(self):
        """Custom permissions for template management."""
        if self.action in ['destroy', 'partial_update', 'update']:
            # Only admin can modify/delete system templates
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        """Prevent deletion of system templates."""
        if instance.is_system:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Cannot delete system templates")
        super().perform_destroy(instance)

    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """
        Get template preview with example data.

        GET /api/notifications/templates/{id}/preview/
        """
        template = self.get_object()
        preview_data = template_service.preview_template(
            template_code=template.template_code,
            channel=template.channel,
            language=template.language,
        )

        if preview_data:
            return Response({
                'success': True,
                'data': preview_data,
            })
        return Response({
            'success': False,
            'error': {'message': 'Failed to generate preview'},
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def save_version(self, request, pk=None):
        """
        Save template as a new version.

        POST /api/notifications/templates/{id}/save_version/
        """
        template = self.get_object()

        # Create new version
        new_version = template.save_new_version()

        serializer = NotificationTemplateSerializer(new_version)
        return Response({
            'success': True,
            'message': f'Created version {new_version.version}',
            'data': serializer.data,
        })

    @action(detail=False, methods=['get'])
    def types(self, request):
        """
        Get list of notification types.

        GET /api/notifications/templates/types/
        """
        types = NotificationTemplate.objects.values_list(
            'template_type', flat=True
        ).distinct().order_by('template_type')

        return Response({
            'success': True,
            'data': list(types),
        })

    @action(detail=False, methods=['get'])
    def channels(self, request):
        """
        Get list of available channels.

        GET /api/notifications/templates/channels/
        """
        channels = [
            {'value': choice[0], 'label': choice[1]}
            for choice in NotificationTemplate.CHANNEL_TYPES
        ]

        return Response({
            'success': True,
            'data': channels,
        })


class NotificationViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Notification model.

    Provides:
    - Standard CRUD operations
    - Mark as read/unread actions
    - Bulk operations
    - User-specific filtering
    """

    queryset = Notification.objects.select_related(
        'recipient', 'template', 'sender'
    ).all()
    filterset_class = NotificationFilter
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'scheduled_at', 'sent_at', 'priority', 'read_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Non-admin users can only see their own notifications
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            queryset = queryset.filter(recipient=user)

        return queryset

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark notification as read.

        POST /api/notifications/{id}/mark_read/
        """
        notification = self.get_object()

        # Check permission
        if notification.recipient != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {'message': 'Permission denied'},
            }, status=status.HTTP_403_FORBIDDEN)

        notification.mark_as_read()

        return Response({
            'success': True,
            'message': 'Notification marked as read',
            'data': {'read_at': notification.read_at},
        })

    @action(detail=True, methods=['post'])
    def mark_unread(self, request, pk=None):
        """
        Mark notification as unread.

        POST /api/notifications/{id}/mark_unread/
        """
        notification = self.get_object()

        # Check permission
        if notification.recipient != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {'message': 'Permission denied'},
            }, status=status.HTTP_403_FORBIDDEN)

        notification.mark_as_unread()

        return Response({
            'success': True,
            'message': 'Notification marked as unread',
        })

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """
        Mark all user notifications as read.

        POST /api/notifications/mark_all_read/
        """
        count = notification_service.mark_all_as_read(request.user)

        return Response({
            'success': True,
            'message': f'Marked {count} notifications as read',
            'data': {'count': count},
        })

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """
        Get count of unread notifications.

        GET /api/notifications/unread_count/
        """
        count = notification_service.get_unread_count(request.user)

        return Response({
            'success': True,
            'data': {'count': count},
        })

    @action(detail=False, methods=['post'])
    def send(self, request):
        """
        Send a notification.

        POST /api/notifications/send/
        Body:
        {
            "recipient_id": "uuid",
            "notification_type": "workflow_approval",
            "variables": {"asset_name": "Laptop"},
            "channels": ["inbox", "email"],
            "priority": "normal"
        }
        """
        serializer = SendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            result = notification_service.send(
                recipient=serializer.validated_data['recipient_id'],
                notification_type=serializer.validated_data['notification_type'],
                variables=serializer.validated_data['variables'],
                channels=serializer.validated_data.get('channels'),
                priority=serializer.validated_data.get('priority', 'normal'),
                scheduled_at=serializer.validated_data.get('scheduled_at'),
                sender=request.user,
            )

            return Response(result)
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid request data',
                'details': serializer.errors,
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def send_batch(self, request):
        """
        Send notification to multiple recipients.

        POST /api/notifications/send_batch/
        Body:
        {
            "recipient_ids": ["uuid1", "uuid2"],
            "notification_type": "system_announcement",
            "variables": {"message": "Maintenance scheduled"},
            "channels": ["inbox"],
            "priority": "high"
        }
        """
        serializer = BatchSendNotificationSerializer(data=request.data)
        if serializer.is_valid():
            result = notification_service.send_batch(
                recipients=serializer.validated_data['recipient_ids'],
                notification_type=serializer.validated_data['notification_type'],
                variables=serializer.validated_data['variables'],
                channels=serializer.validated_data.get('channels'),
                priority=serializer.validated_data.get('priority', 'normal'),
                sender=request.user,
            )

            return Response(result)
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Invalid request data',
                'details': serializer.errors,
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get notification summary for current user.

        GET /api/notifications/summary/
        """
        queryset = self.get_queryset().filter(recipient=request.user)

        summary = queryset.aggregate(
            total=Count('id'),
            unread=Count('id', filter=Q(read_at__isnull=True)),
            urgent=Count('id', filter=Q(priority='urgent', read_at__isnull=True)),
            high=Count('id', filter=Q(priority='high', read_at__isnull=True)),
        )

        return Response({
            'success': True,
            'data': summary,
        })


class NotificationLogViewSet(BaseModelViewSet):
    """
    ViewSet for NotificationLog model.

    Provides read-only access to notification logs.
    Only admins can view logs for audit purposes.
    """

    queryset = NotificationLog.objects.select_related('notification').all()
    serializer_class = NotificationLogSerializer
    filterset_class = NotificationLogFilter
    search_fields = ['error_message', 'external_id']
    ordering_fields = ['created_at', 'duration', 'retry_count']

    def get_permissions(self):
        """Only admins can access logs."""
        return [IsAuthenticated(), IsAdminUser()]

    def perform_create(self, serializer):
        """Logs are created automatically, not via API."""
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Logs are created automatically")

    def perform_update(self, serializer):
        """Logs cannot be modified."""
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Logs cannot be modified")


class NotificationConfigViewSet(BaseModelViewSet):
    """
    ViewSet for NotificationConfig model.

    Provides:
    - User's own configuration management
    - Admin can view all configs
    """

    queryset = NotificationConfig.objects.select_related('user').all()
    filterset_class = NotificationConfigFilter
    ordering_fields = ['created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['update', 'partial_update']:
            return NotificationConfigUpdateSerializer
        return NotificationConfigSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Non-admin users can only see their own config
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            queryset = queryset.filter(user=user)

        return queryset

    def perform_create(self, serializer):
        """Set user to current user on create."""
        # Ensure user can only create their own config
        if serializer.validated_data.get('user') != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Can only create config for yourself")
        super().perform_create(serializer)

    @action(detail=False, methods=['get'])
    def my_config(self, request):
        """
        Get current user's notification config.

        GET /api/notifications/configs/my_config/
        """
        config, created = NotificationConfig.objects.get_or_create(
            user=request.user,
        )

        serializer = NotificationConfigSerializer(config)
        return Response({
            'success': True,
            'data': serializer.data,
        })


# Action classes for documentation purposes
class SendNotificationAction:
    """Documentation for send action."""
    pass


class BatchSendNotificationAction:
    """Documentation for batch send action."""
    pass


class MarkAsReadAction:
    """Documentation for mark read action."""
    pass


class MarkAllAsReadAction:
    """Documentation for mark all read action."""
    pass


class GetUnreadCountAction:
    """Documentation for unread count action."""
    pass


# =============================================================================
# NotificationChannel ViewSet
# =============================================================================

class NotificationChannelViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for NotificationChannel model.

    Provides:
    - Standard CRUD operations for channel configuration
    - Channel testing
    - Enable/disable channels
    """

    queryset = NotificationChannel.objects.all()
    serializer_class = NotificationChannelSerializer
    search_fields = ['channel_type', 'channel_name']
    ordering_fields = ['channel_type', 'priority', 'is_enabled', 'status']
    filterset_fields = ['channel_type', 'is_enabled', 'status']

    def get_permissions(self):
        """Only admins can manage channels."""
        from rest_framework.permissions import IsAdminUser
        return [IsAuthenticated(), IsAdminUser()]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['update', 'partial_update']:
            return NotificationChannelUpdateSerializer
        return NotificationChannelSerializer

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test channel connectivity.

        POST /api/notifications/channels/{id}/test/
        """
        channel = self.get_object()
        serializer = NotificationChannelTestSerializer(data=request.data)

        if serializer.is_valid():
            from apps.notifications.channels import get_channel

            try:
                from apps.notifications.channels import NotificationMessage as ChannelNotificationMessage
                adapter = get_channel(channel.channel_type)
                # Test with provided recipient and message
                result = adapter.send_with_validation(
                    ChannelNotificationMessage(
                        recipient=serializer.validated_data['recipient'],
                        subject='Test Message',
                        content=serializer.validated_data['message'],
                    )
                )

                if result.success:
                    channel.record_success()
                else:
                    channel.record_failure(result.error_message or 'Test failed')

                return Response({
                    'success': result.success,
                    'message': result.message,
                    'data': {
                        'channel': channel.channel_type,
                        'external_id': result.external_id,
                        'duration_ms': result.duration_ms,
                    }
                })

            except Exception as e:
                channel.record_failure(str(e))
                return Response({
                    'success': False,
                    'error': {'message': str(e)},
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': False,
            'error': {'details': serializer.errors},
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """
        Enable channel.

        POST /api/notifications/channels/{id}/enable/
        """
        channel = self.get_object()
        channel.is_enabled = True
        channel.status = 'active'
        channel.save(update_fields=['is_enabled', 'status'])

        return Response({
            'success': True,
            'message': f'Channel {channel.channel_type} enabled',
        })

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """
        Disable channel.

        POST /api/notifications/channels/{id}/disable/
        """
        channel = self.get_object()
        channel.is_enabled = False
        channel.save(update_fields=['is_enabled'])

        return Response({
            'success': True,
            'message': f'Channel {channel.channel_type} disabled',
        })

    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get list of available channel types.

        GET /api/notifications/channels/available/
        """
        from apps.notifications.channels import get_supported_channels

        channels = [
            {'value': ct, 'label': ct.capitalize()}
            for ct in get_supported_channels()
        ]

        return Response({
            'success': True,
            'data': channels,
        })


# =============================================================================
# NotificationMessage ViewSet
# =============================================================================

class NotificationMessageViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for NotificationMessage model.

    Provides:
    - Standard CRUD operations for message management
    - Message sending
    - Progress tracking
    """

    queryset = NotificationMessage.objects.select_related(
        'template', 'sender'
    ).all()
    serializer_class = NotificationMessageSerializer
    search_fields = ['message_code', 'title', 'notification_type']
    ordering_fields = ['created_at', 'scheduled_at', 'sent_at', 'priority', 'status']
    filterset_fields = ['notification_type', 'status', 'priority', 'channels']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return NotificationMessageListSerializer
        if self.action == 'create':
            return NotificationMessageCreateSerializer
        return NotificationMessageSerializer

    @action(detail=False, methods=['post'])
    def create_and_send(self, request):
        """
        Create and send a notification message.

        POST /api/notifications/messages/create_and_send/
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        serializer = NotificationMessageCreateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            # Create message
            message = NotificationMessage.objects.create(
                organization=request.user.organization,
                notification_type=data['notification_type'],
                title=data['title'],
                content=data['content'],
                subject=data.get('subject', ''),
                template_id=data.get('template_id'),
                target_type=data['target_type'],
                target_ids=data.get('target_ids', []),
                channels=data.get('channels', ['inbox']),
                primary_channel=data.get('primary_channel', ''),
                priority=data.get('priority', 'normal'),
                scheduled_at=data.get('scheduled_at'),
                data=data.get('data', {}),
                sender=request.user,
                status='pending',
            )

            # Generate message code
            message.generate_message_code()
            message.save(update_fields=['message_code'])

            # Get recipients
            recipient_ids = message.get_recipient_users()
            message.total_recipients = len(recipient_ids)

            # Send to recipients
            from apps.notifications.services import notification_service
            sent_count = 0
            failed_count = 0

            for recipient_id in recipient_ids:
                result = notification_service.send(
                    recipient=recipient_id,
                    notification_type=message.notification_type,
                    variables=message.data,
                    channels=message.channels,
                    priority=message.priority,
                    sender=message.sender,
                )
                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1

            message.update_progress(sent_count, failed_count)

            return Response({
                'success': True,
                'message': 'Message created and sent',
                'data': {
                    'message_id': str(message.id),
                    'message_code': message.message_code,
                    'total_recipients': message.total_recipients,
                    'sent_count': sent_count,
                    'failed_count': failed_count,
                },
            })

        return Response({
            'success': False,
            'error': {'details': serializer.errors},
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        Send a scheduled/draft message.

        POST /api/notifications/messages/{id}/send/
        """
        message = self.get_object()

        if message.status == 'sent':
            return Response({
                'success': False,
                'error': {'message': 'Message already sent'},
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get recipients
        recipient_ids = message.get_recipient_users()
        message.total_recipients = len(recipient_ids)

        # Send to recipients
        from apps.notifications.services import notification_service
        sent_count = 0
        failed_count = 0

        for recipient_id in recipient_ids:
            result = notification_service.send(
                recipient=recipient_id,
                notification_type=message.notification_type,
                variables=message.data,
                channels=message.channels,
                priority=message.priority,
                sender=message.sender,
            )
            if result['success']:
                sent_count += 1
            else:
                failed_count += 1

        message.update_progress(sent_count, failed_count)

        return Response({
            'success': True,
            'message': 'Message sent',
            'data': {
                'message_id': str(message.id),
                'total_recipients': message.total_recipients,
                'sent_count': sent_count,
                'failed_count': failed_count,
            },
        })

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """
        Get message sending progress.

        GET /api/notifications/messages/{id}/progress/
        """
        message = self.get_object()

        return Response({
            'success': True,
            'data': {
                'message_code': message.message_code,
                'status': message.status,
                'progress': message.progress,
                'total_recipients': message.total_recipients,
                'sent_count': message.sent_count,
                'failed_count': message.failed_count,
                'read_count': message.read_count,
            },
        })


# =============================================================================
# InAppMessage ViewSet
# =============================================================================

class InAppMessageViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for InAppMessage model.

    Provides:
    - Standard CRUD operations for in-app messages
    - Message publishing
    - User-specific message filtering
    """

    queryset = InAppMessage.objects.select_related('author').all()
    serializer_class = InAppMessageSerializer
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'publish_at', 'priority', 'status']
    filterset_fields = ['message_type', 'status', 'priority', 'show_popup']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InAppMessageListSerializer
        if self.action == 'create':
            return InAppMessageCreateSerializer
        return InAppMessageSerializer

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()

        # Non-admin users only see published messages or their own drafts
        user = self.request.user
        if not user.is_staff and not user.is_superuser:
            # Get messages targeted at this user
            user_ids = [str(user.id)]
            # Also get user's roles and departments
            from apps.accounts.models import Role
            user_roles = Role.objects.filter(users=user).values_list('id', flat=True)
            user_depts = [str(user.department_id)] if user.department_id else []

            # Filter: published messages for this user's targets
            queryset = queryset.filter(
                status='published',
            ).filter(
                target_type='all'
            ).union(
                queryset.filter(
                    status='published',
                    target_type='users',
                    target_ids__contains=str(user.id),
                )
            ).union(
                queryset.filter(
                    status='published',
                    target_type='roles',
                    target_ids__overlap=list(user_roles),
                )
            ).union(
                queryset.filter(
                    status='published',
                    target_type='departments',
                    target_ids__overlap=user_depts,
                )
            )

            # Also show user's own drafts
            queryset = queryset.union(
                InAppMessage.objects.filter(author=user)
            )

        return queryset

    @action(detail=False, methods=['post'])
    def create_and_publish(self, request):
        """
        Create and publish an in-app message.

        POST /api/notifications/inapp/create_and_publish/
        """
        serializer = InAppMessageCreateSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data

            message = InAppMessage.objects.create(
                organization=request.user.organization,
                message_type=data['message_type'],
                title=data['title'],
                content=data['content'],
                priority=data['priority'],
                target_type=data.get('target_type', 'all'),
                target_ids=data.get('target_ids', []),
                exclude_users=data.get('exclude_users', []),
                show_popup=data.get('show_popup', False),
                dismissible=data.get('dismissible', True),
                requires_acknowledgment=data.get('requires_acknowledgment', False),
                publish_at=data.get('publish_at'),
                expire_at=data.get('expire_at'),
                action_url=data.get('action_url', ''),
                action_label=data.get('action_label', ''),
                author=request.user,
                status='published' if not data.get('publish_at') else 'scheduled',
            )

            # Auto-publish if no scheduled time
            if not data.get('publish_at'):
                message.publish()

            return Response({
                'success': True,
                'message': 'In-app message created',
                'data': InAppMessageSerializer(message).data,
            })

        return Response({
            'success': False,
            'error': {'details': serializer.errors},
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """
        Publish an in-app message.

        POST /api/notifications/inapp/{id}/publish/
        """
        message = self.get_object()

        # Check permission
        if message.author != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {'message': 'Permission denied'},
            }, status=status.HTTP_403_FORBIDDEN)

        message.publish()

        return Response({
            'success': True,
            'message': 'Message published',
            'data': InAppMessageSerializer(message).data,
        })

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive an in-app message.

        POST /api/notifications/inapp/{id}/archive/
        """
        message = self.get_object()

        # Check permission
        if message.author != request.user and not request.user.is_staff:
            return Response({
                'success': False,
                'error': {'message': 'Permission denied'},
            }, status=status.HTTP_403_FORBIDDEN)

        message.archive()

        return Response({
            'success': True,
            'message': 'Message archived',
        })

    @action(detail=True, methods=['post'], url_path='action')
    def perform_action(self, request, pk=None):
        """
        Perform action on in-app message.

        POST /api/notifications/inapp/{id}/action/
        """
        message = self.get_object()
        serializer = InAppMessageActionSerializer(data=request.data)

        if serializer.is_valid():
            action_type = serializer.validated_data['action']

            if action_type == 'increment_view':
                message.increment_view()
            elif action_type == 'increment_acknowledge':
                message.increment_acknowledge()
            elif action_type == 'increment_dismiss':
                message.increment_dismiss()

            return Response({
                'success': True,
                'message': f'Action {action_type} completed',
                'data': {
                    'view_count': message.view_count,
                    'acknowledge_count': message.acknowledge_count,
                    'dismiss_count': message.dismiss_count,
                },
            })

        return Response({
            'success': False,
            'error': {'details': serializer.errors},
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active messages for current user.

        GET /api/notifications/inapp/active/
        """
        from django.utils import timezone

        now = timezone.now()

        messages = InAppMessage.objects.filter(
            status='published',
            publish_at__lte=now,
        ).filter(
            expire_at__isnull=True
        ).union(
            InAppMessage.objects.filter(
                status='published',
                expire_at__gt=now,
            )
        ).filter(
            target_type='all'
        )

        # Also check user-specific targeting
        user_ids = [str(request.user.id)]
        user_role_ids = list(
            request.user.roles.values_list('id', flat=True)
        ) if hasattr(request.user, 'roles') else []
        user_dept_id = str(request.user.department_id) if request.user.department_id else None

        if user_dept_id:
            messages = messages.union(
                InAppMessage.objects.filter(
                    status='published',
                    target_type='departments',
                    target_ids__contains=user_dept_id,
                )
            )

        # Filter out excluded users
        messages = [m for m in messages if str(request.user.id) not in m.exclude_users]

        serializer = InAppMessageListSerializer(messages, many=True)

        return Response({
            'success': True,
            'data': serializer.data,
        })

    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """
        Get user's in-app message statistics.

        GET /api/notifications/inapp/my_stats/
        """
        from django.utils import timezone

        now = timezone.now()

        # Get active messages for user
        all_messages = InAppMessage.objects.filter(
            status='published',
            publish_at__lte=now,
        ).filter(
            target_type='all'
        )

        total = all_messages.count()
        acknowledged = sum(1 for m in all_messages if str(request.user.id) in getattr(m, 'acknowledged_by', []))

        return Response({
            'success': True,
            'data': {
                'total_messages': total,
                'acknowledged': acknowledged,
                'pending': total - acknowledged,
            },
        })
