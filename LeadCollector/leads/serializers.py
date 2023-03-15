from rest_framework import serializers
from leads.models import LeadsModel


class LeadsModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeadsModel
        fields = '__all__'