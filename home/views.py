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

class SelfCleaningFileResponse(FileResponse):
    """Custom response that deletes file after sending"""
    def __init__(self, file_path, *args, **kwargs):
        self.file_path = file_path
        file = open(file_path, 'rb')
        super().__init__(file, *args, **kwargs)
    
    def close(self):
        super().close()
        try:
            if os.path.exists(self.file_path):
                os.unlink(self.file_path)
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

@api_view(['POST'])
def extract_audio(request):
    temp_video_path = None
    temp_audio_path = None
    persistent_audio_path = None
    
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
        
        # Create temporary audio file path
        temp_audio_path = tempfile.mktemp(suffix='.mp3')
        
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
        
        # Create a persistent audio file
        persistent_audio_path = tempfile.mktemp(suffix='.mp3')
        shutil.copyfile(temp_audio_path, persistent_audio_path)
        
        # Create custom response that auto-deletes file
        return SelfCleaningFileResponse(
            persistent_audio_path,
            filename=f"audio_{uuid.uuid4()}.mp3",
            content_type='audio/mpeg'
        )
        
    except Exception as e:
        logger.exception("Unhandled exception in extract_audio")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    finally:
        # Clean up temporary files
        for path in [temp_video_path, temp_audio_path]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except Exception as e:
                    logger.error(f"Error deleting temp file: {str(e)}")