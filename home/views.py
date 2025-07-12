import os
import uuid
import logging
from django.conf import settings
from moviepy import VideoFileClip
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Product
from rest_framework import status

logger = logging.getLogger(__name__)

@api_view(['POST'])
def extract_audio(request):
    try:
        # Validate and get video file
        if 'video' not in request.FILES:
            return Response({'error': 'No video file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        video_file = request.FILES['video']
        
        # Handle MEDIA_ROOT configuration
        media_root = getattr(settings, 'MEDIA_ROOT', None)
        if not media_root:
            # Default to BASE_DIR/media if not set
            media_root = os.path.join(settings.BASE_DIR, 'media')
            logger.warning(f"MEDIA_ROOT not set. Using fallback: {media_root}")
        
        # Ensure media directories exist
        try:
            os.makedirs(media_root, exist_ok=True)
            logger.info(f"Media root directory: {media_root}")
        except Exception as dir_error:
            logger.error(f"Failed to create media root: {str(dir_error)}")
            # Fallback to temporary directory
            import tempfile
            media_root = tempfile.mkdtemp()
            logger.warning(f"Using temporary directory: {media_root}")
        
        # Save temporary video file
        temp_video_name = f"temp_{uuid.uuid4()}.mp4"
        temp_video_path = os.path.join(media_root, temp_video_name)
        
        try:
            with open(temp_video_path, 'wb+') as destination:
                for chunk in video_file.chunks():
                    destination.write(chunk)
            logger.info(f"Video saved to: {temp_video_path} ({os.path.getsize(temp_video_path)} bytes)")
        except Exception as save_error:
            logger.error(f"Failed to save video: {str(save_error)}")
            return Response(
                {'error': 'Could not save video file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Prepare audio output
        audios_dir = os.path.join(media_root, 'audios')
        try:
            os.makedirs(audios_dir, exist_ok=True)
            logger.info(f"Audio output directory: {audios_dir}")
        except Exception as audio_dir_error:
            logger.error(f"Failed to create audio directory: {str(audio_dir_error)}")
            return Response(
                {'error': 'Could not create audio directory'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        audio_filename = f"audio_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(audios_dir, audio_filename)
        relative_audio_path = f'audios/{audio_filename}'
        
        # Extract audio using MoviePy - FIXED VERSION
        try:
            logger.info(f"Starting audio extraction to: {audio_path}")
            clip = VideoFileClip(temp_video_path)
            
            # FIX: Use compatible parameters for write_audiofile
            # Remove 'verbose' parameter which causes the error
            clip.audio.write_audiofile(audio_path)
            clip.close()
            logger.info("Audio extraction completed successfully")
        except Exception as processing_error:
            logger.error(f"Audio extraction failed: {str(processing_error)}")
            # Clean up temporary files
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            return Response(
                {'error': 'Audio processing failed. Please check video format.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Ensure temporary video is always removed
            if os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                    logger.info("Temporary video removed")
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {str(cleanup_error)}")
        
        # Save to database
        try:
            audio_record = Product.objects.create(audio=relative_audio_path)
            audio_url = request.build_absolute_uri(audio_record.audio.url)
            logger.info(f"Audio record created: {audio_url}")
            return Response(
                {'audio': audio_url},
                status=status.HTTP_201_CREATED
            )
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            # Clean up audio file if database save failed
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return Response(
                {'error': 'Failed to save audio record'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.exception("Unhandled exception in extract_audio")
        return Response(
            {'error': 'Internal server error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )