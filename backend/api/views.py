from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from .generation import generate_answer
from rest_framework import status

user_data = []

@csrf_exempt
@api_view(['POST'])
def ask(request):
    question = request.data.get('question')
    print(question)
    name = request.data.get('name', 'User')
    if not question:
        return Response({"error": "Question is required."},
                        status = status.HTTP_400_BAD_REQUEST)
    try:
        answer = generate_answer(question)
    except Exception as e:
        # return error with CORS header so frontend can receive it
        resp = Response({"error": str(e)},
                        status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        resp["Access-Control-Allow-Origin"] = "*"
        return resp
    
    print(answer)
    resp = Response({"name": name,
                     "question": question,
                     "answer": answer})
    resp["Access-Control-Allow-Origin"] = "*"
    return resp

    
