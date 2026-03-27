from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from materials.models import StudyMaterial
from assignment.models import Assignment
from ai_tutor.models import Conversation, EssayRequest


@login_required
def index(request):
    return render(request, 'dashboard/index.html')


@login_required
def explore(request):
    materials = StudyMaterial.objects.filter(owner=request.user)
    assignments = Assignment.objects.filter(user=request.user)
    essays = EssayRequest.objects.filter(user=request.user)
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, 'dashboard/explore.html', {
        'materials_count': materials.count(),
        'assignments_count': assignments.count(),
        'essays_count': essays.count(),
        'ai_sessions': conversations.count(),
    })
