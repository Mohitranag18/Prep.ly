from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import University, Course, QuestionPaper
from .serializers import UniversitySerializer, CourseSerializer, QuestionPaperSerializer

from pdf2image import convert_from_bytes
from PIL import Image
import base64
import io
import google.generativeai as genai
from django.conf import settings

# Configure Gemini
genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)

# Convert image to base64
def image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

# Extract text from PDF using Gemini
def extract_text_with_gemini_from_pdf(pdf_bytes):
    images = convert_from_bytes(pdf_bytes, dpi=200)
    model = genai.GenerativeModel("gemini-1.5-pro")
    extracted_text = ""

    for img in images:
        base64_img = image_to_base64(img)
        response = model.generate_content([
            {
                "type": "text",
                "text": "Extract all text from this image. Return only the text.",
            },
            {
                "type": "image",
                "image": {
                    "data": base64.b64decode(base64_img),
                    "mime_type": "image/png"
                }
            }
        ])
        extracted_text += response.text.strip() + "\n"

    return extracted_text.strip()

# --- Upload & List Question Papers ---
@api_view(['GET', 'POST'])
def question_paper_list_create(request):
    if request.method == 'GET':
        university = request.GET.get('university')
        course = request.GET.get('course')
        semester = request.GET.get('semester')
        subject = request.GET.get('subject')

        qps = QuestionPaper.objects.all()

        if university:
            qps = qps.filter(university__name__icontains=university)
        if course:
            qps = qps.filter(course__name__icontains=course)
        if semester:
            qps = qps.filter(semester=semester)
        if subject:
            qps = qps.filter(subject__icontains=subject)

        serializer = QuestionPaperSerializer(qps, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = QuestionPaperSerializer(data=request.data)
        if serializer.is_valid():
            qp_instance = serializer.save()

            # Extract text from uploaded PDF using Gemini OCR
            try:
                with qp_instance.pdf_file.open('rb') as f:
                    pdf_bytes = f.read()
                    text = extract_text_with_gemini_from_pdf(pdf_bytes)

                qp_instance.parsed_text = text.strip()
                qp_instance.save()
            except Exception as e:
                return Response({"error": "PDF parsing failed", "details": str(e)}, status=500)

            return Response(QuestionPaperSerializer(qp_instance).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- Get Individual Paper ---
@api_view(['GET'])
def question_paper_detail(request, pk):
    try:
        qp = QuestionPaper.objects.get(pk=pk)
    except QuestionPaper.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    serializer = QuestionPaperSerializer(qp)
    return Response(serializer.data)
