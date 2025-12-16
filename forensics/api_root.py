from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.permissions import AllowAny


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    API Root - Browse available endpoints
    """
    return Response({
        'cases': reverse('case-list', request=request, format=format),
        'persons': reverse('person-list', request=request, format=format),
        'case-persons': reverse('caseperson-list', request=request, format=format),
        'evidence': reverse('evidence-list', request=request, format=format),
        'evidence-transfers': reverse('evidencetransfer-list', request=request, format=format),
        'evidence-images': reverse('evidenceimage-list', request=request, format=format),
        'documents': reverse('document-list', request=request, format=format),
        'tasks': reverse('task-list', request=request, format=format),
        'timeline-activities': reverse('timelineactivity-list', request=request, format=format),
        'notifications': reverse('notification-list', request=request, format=format),
        'user-profiles': reverse('userprofile-list', request=request, format=format),
        'access-requests': reverse('accessrequest-list', request=request, format=format),
    })
