from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
import json
from .utils import (
    extract_video_id,
    get_transcript,
    extract_keywords_gemini,
    get_practice_questions_from_gemini
)
from django.utils.text import slugify
from .models import VideoInput
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import VideoInputSerializer  # you'll need this

@api_view(['POST'])
def generate_practice_questions(request):
    try:
        data = json.loads(request.body)
        video_url = data.get("url")
        timestamp = int(data.get("timestamp", 0))  # Timestamp in seconds

        if not video_url or timestamp <= 0:
            return JsonResponse({"error": "Invalid URL or timestamp."}, status=400)

        video_id = extract_video_id(video_url)
        if not video_id:
            return JsonResponse({"error": "Could not extract video ID."}, status=400)

        # Create slug using user + video_url
        slug = slugify(f"{request.user.username}-{video_url}")

        # Create or update existing entry
        video_input, created = VideoInput.objects.update_or_create(
            slug=slug,
            defaults={
                "video_url": video_url,
                "watched_till": timestamp,
                "owner": request.user
            }
        )

        transcript_data = get_transcript(video_id)
        if not transcript_data:
            return JsonResponse({"error": "Transcript not found or disabled."}, status=404)

        filtered_text = " ".join(
            segment.text
            for segment in transcript_data["transcript"]
            if segment.start <= timestamp
        )

        if not filtered_text.strip():
            return JsonResponse({"error": "Transcript up to given timestamp is empty."}, status=400)

        keywords = extract_keywords_gemini(filtered_text, 7)
        if not keywords:
            return JsonResponse({"error": "Could not extract keywords."}, status=500)

        questions = get_practice_questions_from_gemini(keywords)

        return JsonResponse({
            "keywords": keywords,
            "questions": questions
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_video_inputs(request):
    videos = VideoInput.objects.filter(owner=request.user)
    serializer = VideoInputSerializer(videos, many=True)
    return Response(serializer.data)
