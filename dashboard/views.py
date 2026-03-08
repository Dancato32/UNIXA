from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from materials.models import StudyMaterial
from assignment.models import Assignment


@login_required
def dashboard_home(request):
    """Dashboard home view - protected by login required."""
    materials = StudyMaterial.objects.filter(owner=request.user)
    assignments = Assignment.objects.filter(user=request.user)
    
    # Count statistics
    materials_count = materials.count()
    assignments_count = assignments.count()
    
    return render(request, 'dashboard/index_new.html', {
        'materials': materials[:5],
        'assignments': assignments[:5],
        'materials_count': materials_count,
        'assignments_count': assignments_count,
    })
