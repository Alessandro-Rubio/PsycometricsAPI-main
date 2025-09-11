from rest_framework.decorators import api_view
from rest_framework.response import Response
from bson import ObjectId
from ..db.mongo import test_collection, candidate_collection, result_collection, report_collection
from ..utils.objectIdConversion import convert_objectid 
from ..serializers import ReportSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_report(request):
    if request.method == "POST":
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data

            report_doc = {
                "candidate_id": ObjectId(validated_data["candidate_id"]),
                "test_id": ObjectId(validated_data["test_id"]),
                "result_id": ObjectId(validated_data["result_id"]),
                "hr_id": ObjectId(validated_data["hr_id"]),
                "summary": validated_data["summary"],
                "traits": validated_data["traits"],
                "conflict_style": validated_data["conflict_style"],
                "skills": validated_data["skills"],
                "red_flags": validated_data["red_flags"],
                "recommendations": validated_data["recommendations"],
                "raw_analysis": validated_data["raw_analysis"]
            }

            result = report_collection.insert_one(report_doc)

            return Response({"report_id": str(result.inserted_id)}, status=201)

        return Response(serializer.errors, status=400)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_report_by_candidate(request, candidate_id):
    try:
        # Convertir el candidate_id a ObjectId
        candidate_object_id = ObjectId(candidate_id)
    except:
        return Response({"error": "Invalid candidate ID"}, status=400)

    try:
        # Buscar el reporte por candidate_id
        report = report_collection.find_one({"candidate_id": candidate_object_id})
        
        if not report:
            return Response({"error": "Report not found for this candidate"}, status=404)
        
        # Convertir ObjectId a string para la respuesta JSON
        report = convert_objectid(report)
        
        return Response(report, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_reports_by_hr(request):
    try:
        # Obtener el HR ID del usuario autenticado
        hr_id = request.user.user_id
        if not hr_id:
            return Response({"error": "HR ID not found in token"}, status=401)

        # Convertir el HR ID a ObjectId
        hr_object_id = ObjectId(hr_id)
        
        # Buscar todos los reportes para este HR
        reports = list(report_collection.find({"hr_id": hr_object_id}))
        
        if not reports:
            return Response({"message": "No reports found for this HR"}, status=404)
        
        # Convertir ObjectId a string para cada reporte
        reports = [convert_objectid(report) for report in reports]
        
        return Response(reports, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)