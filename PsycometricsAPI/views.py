# Create your views here.
from django.shortcuts import render
from rest_framework import viewsets
from .models import HR, Test, Candidate, Result
from .serializers import HRSerializer, TestSerializer, CandidateSerializer, ResultSerializer

#Vistas usando render 

# Vistas para la API REST
class HRViewSet(viewsets.ModelViewSet):
    queryset = HR.objects.all()
    serializer_class = HRSerializer

class TestViewSet(viewsets.ModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer

class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer

class ResultViewSet(viewsets.ModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
