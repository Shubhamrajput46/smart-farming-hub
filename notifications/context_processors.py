from .models import Notification


def notifications(request):
    farmer = getattr(request, 'farmer', None)
    if not farmer:
        return {}
    unread = Notification.objects.filter(farmer=farmer, is_read=False)
    return {
        'unread_count': unread.count(),
        'recent_notifications': Notification.objects.filter(farmer=farmer)[:5],
    }
