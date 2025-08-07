from rest_framework.decorators import api_view
from rest_framework.response import Response
from bson import ObjectId
from ..db.mongo import test_collection, candidate_collection, result_collection
from ..utils.objectIdConversion import convert_objectid 

@api_view(["POST"])
def test(request):
    if request.method == "POST":
        candidate_id = request.data.get("candidate_id")
        if not candidate_id:
            return Response({"error": "Candidate ID is required"}, status=400)
        try:
            candidate = candidate_collection.find_one({"_id": ObjectId(candidate_id)})
        except Exception:
            return Response({"error": "Invalid candidate ID"}, status=400)
        if not candidate:
            return Response({"error": "Invalid candidate ID"}, status=404)

        # Check if candidate has already submitted a result
        existing_result = result_collection.find_one({"candidate_id": ObjectId(candidate_id)})
        if existing_result:
            return Response({"error": "Candidate has already submitted a test"}, status=409)

        test = test_collection.find_one()
        if not test:
            return Response({"error": "No test found"}, status=404)

        test = convert_objectid(test)
        return Response(test, status=200)