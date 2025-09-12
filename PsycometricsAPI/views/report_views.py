# report_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
from ..db.mongo import report_collection, candidate_collection
from ..utils.objectIdConversion import convert_objectid
from ..serializers import ReportSerializer
import json
from datetime import datetime

@api_view(["POST"])
def receive_interpretation(request):
    """
    Endpoint para recibir la interpretación desde n8n
    """
    try:
        data = request.data
        
        # Validar campos requeridos
        required_fields = ["candidate_id", "summary"]
        for field in required_fields:
            if field not in data:
                return Response(
                    {"error": f"Campo requerido faltante: {field}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Convertir IDs a ObjectId
        interpretation_data = {
            "candidate_id": ObjectId(data["candidate_id"]),
            "test_id": ObjectId(data.get("test_id", "000000000000000000000000")),
            "result_id": ObjectId(data.get("result_id", "000000000000000000000000")),
            "hr_id": ObjectId(data.get("hr_id", "68634fee4a86e24702186e63")),
            "summary": data["summary"],
            "traits": data.get("traits", []),
            "conflict_style": data.get("conflict_style", ""),
            "skills": data.get("skills", {
                "problem_solving": "",
                "communication": "",
                "empathy": "",
                "leadership": "",
                "stress_tolerance": "",
                "integrity": ""
            }),
            "red_flags": data.get("red_flags", []),
            "recommendations": data.get("recommendations", []),
            "raw_analysis": data.get("raw_analysis", ""),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Insertar en la base de datos
        result = report_collection.insert_one(interpretation_data)
        
        # Actualizar el candidato para indicar que tiene reporte
        candidate_collection.update_one(
            {"_id": ObjectId(data["candidate_id"])},
            {"$set": {"has_report": True, "report_id": str(result.inserted_id)}}
        )
        
        return Response(
            {"message": "Interpretación recibida correctamente", "report_id": str(result.inserted_id)},
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            {"error": f"Error al procesar la interpretación: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["GET"])
def get_report_by_candidate(request, candidate_id):
    """
    Obtener reporte por candidate_id
    """
    try:
        report = report_collection.find_one({"candidate_id": ObjectId(candidate_id)})
        if not report:
            return Response(
                {"error": "Reporte no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        report = convert_objectid(report)
        return Response(report)
        
    except Exception as e:
        return Response(
            {"error": f"Error al obtener el reporte: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(["POST"])
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
                "raw_analysis": validated_data["raw_analysis"],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }

            result = report_collection.insert_one(report_doc)

            return Response({"report_id": str(result.inserted_id)}, status=201)

        return Response(serializer.errors, status=400)