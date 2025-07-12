from rest_framework import serializers
from home.models import Product
class AudioSerializer(serializers.ModelSerializer):
    video = serializers.FileField(write_only=True)
    
    class Meta:
        model = Product
        fields = ['id','video','uploaded_at','audio']
        read_only_fields = ['audio','uploaded_at']