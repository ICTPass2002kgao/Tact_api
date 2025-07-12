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

@api_view(['POST'])
def extract_audio(request):
    serializer = AudioSerializer(data=request.data)
    if serializer.is_valid():
        try:
            video_file = request.FILES['video']
 
            temp_video_path = os.path.join(
                settings.MEDIA_ROOT, f"temp_{uuid.uuid4()}.mp4"
            )
            with open(temp_video_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
 
            audios_dir = os.path.join(settings.MEDIA_ROOT, 'audios')
            os.makedirs(audios_dir, exist_ok=True)
 
            audio_filename = f"audio_{uuid.uuid4()}.mp3"
            audio_path = os.path.join(audios_dir, audio_filename)
 
            clip = VideoFileClip(temp_video_path)
            clip.audio.write_audiofile(audio_path)
 
            os.remove(temp_video_path)
 
            audio_record = Product.objects.create(audio=f'audios/{audio_filename}')
 
            return Response(
                {'audio': audio_record.audio.url},
                status=status.HTTP_201_CREATED
            )

        except Exception as e: 
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)