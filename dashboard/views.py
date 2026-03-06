from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from materials.models import StudyMaterial
from assignment.models import Assignment


@login_required
def dashboard_home(request):
    """Dashboard home view - protected by login required."""
    materials = StudyMaterial.objects.filter(owner=request.user)[:5]
    assignments = Assignment.objects.filter(user=request.user)[:5]
    
    return render(request, 'dashboard/index.html', {
        'materials': materials,
        'assignments': assignments,
    })
