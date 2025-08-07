from rest_framework import serializers

class HRSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    gender = serializers.CharField(max_length=10)
    company = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, max_length=128)

class CandidateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    gender = serializers.CharField(max_length=10)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    hr_id = serializers.CharField()
    cv = serializers.URLField(required=False, allow_blank=True)
    candidate_evaluation = serializers.ChoiceField(choices=["pending", "approved", "rejected"], default="pending")
    code = serializers.RegexField(
        regex=r"^[A-Z0-9]{6}$",
        max_length=6,
        min_length=6,
        error_messages={
            "invalid": "The code must be exactly 6 characters long and contain only uppercase letters or digits."
        }
    )

class ResponseSerializer(serializers.Serializer):
    question_id = serializers.CharField()
    response = serializers.CharField()

class ResultSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    test_id = serializers.CharField()
    candidate_id = serializers.CharField()
    hr_id = serializers.CharField()
    completed_at = serializers.DateTimeField(required=False)
    responses = ResponseSerializer(many=True)

class ResponseOptionSerializer(serializers.Serializer):
    option = serializers.CharField()
    value = serializers.IntegerField()

class QuestionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    question = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField())

class TestSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    questions = QuestionSerializer(many=True)

class ReportSerializer(serializers.Serializer):
    candidate_id = serializers.CharField()
    test_id = serializers.CharField()
    result_id = serializers.CharField()
    hr_id = serializers.CharField()
    summary = serializers.CharField()
    traits = serializers.ListField(child=serializers.CharField())
    conflict_style = serializers.CharField()
    skills = serializers.DictField(
        child=serializers.CharField(),
        default={
            "problem_solving": "",
            "communication": "",
            "empathy": "",
            "leadership": "",
            "stress_tolerance": "",
            "integrity": ""
        }
    )
    red_flags = serializers.ListField(child=serializers.CharField())
    recommendations = serializers.ListField(child=serializers.CharField())
    raw_analysis = serializers.CharField()