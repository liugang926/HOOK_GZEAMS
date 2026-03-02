from rest_framework import serializers
from apps.system.models import ActivityLog
from apps.accounts.serializers import UserBasicSerializer

class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for ActivityLog."""
    
    actor = UserBasicSerializer(read_only=True)
    userName = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(source='created_at', format='%Y-%m-%d %H:%M:%S', read_only=True)
    actionLabel = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 
            'action', 
            'actionLabel',
            'actor', 
            'userName',
            'changes', 
            'description', 
            'timestamp'
        ]
        
    def get_userName(self, obj):
        if obj.actor:
            return obj.actor.get_full_name() or obj.actor.username
        return 'System'
