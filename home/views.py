import os
import uuid
import tempfile
import logging
from django.http import FileResponse
from rest_framework.decorators import api_view
from moviepy import VideoFileClip
from rest_framework.response import Response
from rest_framework import status
import shutil

logger = logging.getLogger(__name__)

@api_view(['POST'])
def extract_audio(request):
    temp_video_path = None
    temp_audio_path = None
    
    try:
        # Validate video file exists
        if 'video' not in request.FILES:
            return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        video_file = request.FILES['video']
        
        # Create temporary video file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            temp_video_path = temp_video.name
            for chunk in video_file.chunks():
                temp_video.write(chunk)
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
            temp_audio_path = temp_audio.name
        
        # Convert to audio
        try:
            clip = VideoFileClip(temp_video_path)
            clip.audio.write_audiofile(temp_audio_path)
            clip.close()
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return Response(
                {'error': 'Audio conversion failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create a copy of the audio file to keep it open
        persistent_audio_path = f"/tmp/audio_{uuid.uuid4()}.mp3"
        shutil.copyfile(temp_audio_path, persistent_audio_path)
        
        # Prepare response with persistent file
        audio_file = open(persistent_audio_path, 'rb')
        response = FileResponse(
            audio_file,
            filename=f"audio_{uuid.uuid4()}.mp3",
            content_type='audio/mpeg'
        )
        
        # Add cleanup callback
        def cleanup():
            try:
                audio_file.close()
                os.unlink(persistent_audio_path)
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")
                
        response.closed.connect(cleanup)
        
        return response
        
    except Exception as e:
        logger.exception("Unhandled exception in extract_audio")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up temporary files
        if temp_video_path and os.path.exists(temp_video_path):
            os.unlink(temp_video_path)
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.unlink(temp_audio_path)