import os
import uuid
import tempfile
import logging
from django.http import FileResponse
from rest_framework.decorators import api_view
from moviepy import VideoFileClip
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

@api_view(['POST'])
def extract_audio(request):
    try:
        # Validate video file exists
        if 'video' not in request.FILES:
            return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        video_file = request.FILES['video']
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video, \
             tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio:
            
            # Save video to temp file
            for chunk in video_file.chunks():
                temp_video.write(chunk)
            temp_video.flush()
            
            try:
                # Convert to audio
                clip = VideoFileClip(temp_video.name)
                clip.audio.write_audiofile(temp_audio.name)
                clip.close()
                
                # Prepare response
                temp_audio.seek(0)  # Rewind to beginning
                response = FileResponse(
                    temp_audio,
                    filename=f"audio_{uuid.uuid4()}.mp3",
                    content_type='audio/mpeg'
                )
                
                # Add CORS headers if needed
                response["Access-Control-Allow-Origin"] = "*"
                
                return response
                
            except Exception as e:
                logger.error(f"Conversion error: {str(e)}")
                return Response(
                    {'error': 'Audio conversion failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            finally:
                # Clean up temp files
                os.unlink(temp_video.name)
                os.unlink(temp_audio.name)
    
    except Exception as e:
        logger.exception("Unhandled exception in extract_audio")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )