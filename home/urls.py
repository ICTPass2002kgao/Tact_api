

from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import extract_audio

urlpatterns = [
    path('extract-audio/', extract_audio, name='extract_audio'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
