from rest_framework.decorators import api_view
from rest_framework.response import Response
from bson import ObjectId
from ..db.mongo import test_collection, candidate_collection, result_collection, report_collection
from ..utils.objectIdConversion import convert_objectid 
from ..serializers import ReportSerializer

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
                "raw_analysis": validated_data["raw_analysis"]
            }

            result = report_collection.insert_one(report_doc)

            return Response({"report_id": str(result.inserted_id)}, status=201)

        return Response(serializer.errors, status=400)

@api_view(["GET"])
def report_detail(request, id):
    try:
        candidate_id = ObjectId(id)
    except Exception:
        return Response({"error": "Invalid candidate ID"}, status=400)

    report = report_collection.find_one({"candidate_id": candidate_id})
    if not report:
        return Response({"error": "Report not found"}, status=404)

    report = convert_objectid(report)
    return Response(report, status=200)