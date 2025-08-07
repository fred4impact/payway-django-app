from .models import Notification


def notification_context(request):
    """Add notification context to all templates"""
    if request.user.is_authenticated:
        # Get unread notification count
        unread_count = Notification.objects.filter(
            user=request.user, 
            status='unread'
        ).count()
        
        # Get recent notifications (last 5)
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        return {
            'unread_notifications_count': unread_count,
            'recent_notifications': recent_notifications,
        }
    
    return {
        'unread_notifications_count': 0,
        'recent_notifications': [],
    }
