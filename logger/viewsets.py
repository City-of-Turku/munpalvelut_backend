from rest_framework import viewsets, mixins, filters, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from logger.models import LogEntry
from logger.serializers import LogEntrySerializer, LogEntryFilterSet, BulkEraseSerializer

class LogEntryViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.ListModelMixin,
                      viewsets.GenericViewSet):
    """A general purpose logging service.

    Unauthenticated users may create new log entries, but cannot see them.
    Authenticated users can create and see their own entries.
    Users with the 'see_all' permission can see all log entries.
    Users with the delete permission may use the bulk delete command.
    """
    permission_classes = [AllowAny]
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = LogEntryFilterSet

    def get_queryset(self):
        if self.request.user.is_authenticated():
            if self.request.user.has_perm('logger.see_all'):
                return LogEntry.objects.all()
            return LogEntry.objects.filter(user=self.request.user)
        return LogEntry.objects.none()

    def get_serializer_class(self):
        if self.action == 'erase':
            return BulkEraseSerializer

        return LogEntrySerializer

    @list_route(methods=['post'])
    def erase(self, request):
        """Erase log entries in bulk.
        ---
        type:
            deleted:
                required: true
                type: string
        serializer: logger.serializers.BulkEraseSerializer
        omit_serializer: false
        """
        if not self.request.user.has_perm('logger.delete_logentry'):
            raise PermissionDenied()

        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            d = serializer.data
            total, models = LogEntry.objects.filter(
                created__lte=d['before'],
                severity__lte=d['max_severity']
                ).delete()
            
            # There should be no cascading deletes
            assert len(models) == 1
            
            return Response({
                'deleted': total
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
