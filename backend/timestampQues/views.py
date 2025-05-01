from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .utils import (
    extract_video_id,
    get_transcript,
    extract_keywords_gemini,
    get_practice_questions_from_gemini
)


@csrf_exempt
@require_http_methods(["POST"])
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

        transcript_data = get_transcript(video_id)
        if not transcript_data:
            return JsonResponse({"error": "Transcript not found or disabled."}, status=404)

        # Filter transcript segments up to the given timestamp
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
        print(questions)
        return JsonResponse({
            "keywords": keywords,
            "questions": questions
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
