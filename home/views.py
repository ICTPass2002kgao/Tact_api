import os
import uuid
from django.conf import settings
from django.shortcuts import render
from moviepy import VideoFileClip
from rest_framework.response import Response
from rest_framework.decorators import api_view
from home.serializer import AudioSerializer
from .models import Product 
from rest_framework import status 
import logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
def extract_audio(request):
    try:
        video_file = request.FILES.get('video')
        if not video_file:
            return Response({'error': 'No video provided'}, status=400)
        
        # Create media directories
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        # Save temp video
        temp_video_name = f"temp_{uuid.uuid4()}.mp4"
        temp_video_path = os.path.join(settings.MEDIA_ROOT, temp_video_name)
        
        with open(temp_video_path, 'wb+') as f:
            for chunk in video_file.chunks():
                f.write(chunk)
        
        # Prepare audio output
        audios_dir = os.path.join(settings.MEDIA_ROOT, 'audios')
        os.makedirs(audios_dir, exist_ok=True)
        audio_filename = f"audio_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(audios_dir, audio_filename)
        
        # Process video
        try:
            clip = VideoFileClip(temp_video_path)
            clip.audio.write_audiofile(audio_path, verbose=False, logger=None)
            clip.close()
        except Exception as e:
            logger.error(f"MoviePy error: {str(e)}")
            return Response({'error': 'Audio processing failed'}, status=500)
        finally:
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
        
        # Create database record
        audio_record = Product.objects.create(audio=f'audios/{audio_filename}')
        audio_url = request.build_absolute_uri(audio_record.audio.url)
        
        return Response({'audio': audio_url}, status=201)

    except Exception as e:
        logger.exception("Unhandled exception in extract_audio")
        return Response({'error': 'Internal server error'}, status=500)
 