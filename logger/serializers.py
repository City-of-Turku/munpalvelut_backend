from rest_framework import serializers, filters

from logger.models import LogEntry

import django_filters

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        read_only_fields = ('ip', 'user')
        fields = '__all__'

    def create(self, data):
        le = LogEntry(**data)
        le.ip = self.context['request'].META['REMOTE_ADDR']
        if self.context['request'].user.is_authenticated():
            le.user = self.context['request'].user
        
        le.save()
        return le


class LogEntryFilterSet(filters.FilterSet):
    message = django_filters.CharFilter(lookup_type='icontains')
    exception = django_filters.CharFilter(lookup_type='icontains')

    min_severity = django_filters.ChoiceFilter(
                                               name="severity",
                                               choices=LogEntry.SEVERITY_CHOICES,
                                               lookup_type='gte')

    class Meta:
        model = LogEntry
        fields = ('message', 'min_severity', 'category', 'exception', 'ip', 'user')


class BulkEraseSerializer(serializers.Serializer):
    before = serializers.DateTimeField()
    max_severity = serializers.ChoiceField(choices=LogEntry.SEVERITY_CHOICES)
