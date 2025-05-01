from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import VideoInputSerializer
from .utils import download_audio, transcribe_audio, extract_keywords, get_practice_questions_from_gemini

@api_view(['POST'])
def video_process_view(request):
    serializer = VideoInputSerializer(data=request.data)
    if serializer.is_valid():
        video_url = serializer.validated_data['video_url']
        watched_till = serializer.validated_data['watched_till']
        
        audio_path = download_audio(video_url)
        transcript = transcribe_audio(audio_path, watched_till)
        keywords = extract_keywords(transcript)
        gemini_response = get_practice_questions_from_gemini(keywords)

        return Response({
            "keywords": keywords,
            "practice_questions": gemini_response
        })

    return Response(serializer.errors, status=400)
