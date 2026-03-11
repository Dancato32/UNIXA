from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from materials.models import StudyMaterial
from assignment.models import Assignment
from ai_tutor.models import Conversation
from ai_tutor.models import EssayRequest


@login_required
def dashboard_home(request):
    """Dashboard home view - protected by login required."""
    materials = StudyMaterial.objects.filter(owner=request.user)
    assignments = Assignment.objects.filter(user=request.user)
    
    # Count statistics
    materials_count = materials.count()
    assignments_count = assignments.count()
    
    return render(request, 'dashboard/index.html', {
        'materials': materials[:5],
        'assignments': assignments[:5],
        'materials_count': materials_count,
        'assignments_count': assignments_count,
    })


@login_required
def explore(request):
    """Explore page - discovery and quick navigation hub."""
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
