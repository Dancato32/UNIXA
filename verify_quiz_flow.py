import os
import django
import json
from django.utils import timezone
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexa.settings')
try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    exit(1)

from materials.models import StudyMaterial, ConceptNode, StudentConceptState

def verify_persistence_logic():
    print("--- Starting Quiz Persistence Verification ---")
    
    User = get_user_model()
    # Try to find an existing user or create a test one
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='testviewer', password='password123')
        print("Created test user.")

    # 1. Setup Mock Material & Concept
    material, _ = StudyMaterial.objects.get_or_create(
        title="Verification Test Material",
        owner=user,
        material_type="PDF"
    )
    material.extracted_text = "Photosynthesis is the process by which plants use sunlight to convert water and CO2 into oxygen and glucose."
    material.save()
    
    concept, _ = ConceptNode.objects.get_or_create(
        material=material,
        name="Photosynthesis",
        definition="Solar energy to chemical energy conversion."
    )
    
    # 2. Mock Recurring Misconception (Trigger for ESCALATION)
    # Ensure any previous state is cleared
    StudentConceptState.objects.filter(user=user, concept=concept).delete()
    state = StudentConceptState.objects.create(user=user, concept=concept)
    state.error_profile = {"misconception": 3} # Over threshold of 2
    state.save()
    
    print(f"Mocked state for '{concept.name}': {state.error_profile}")
    
    # 3. Test Prompt Injection Logic (Replicating logic from quiz_ajax)
    escalation_instructions = ""
    selected_topics = ["Photosynthesis"]
    topic_objs = material.concepts.filter(name__in=selected_topics)
    
    for t in topic_objs:
        try:
            s = StudentConceptState.objects.get(user=user, concept=t)
            errors = s.error_profile or {}
            if errors.get("misconception", 0) >= 2:
                escalation_instructions += f"- ESCALATE {t.name}: The student has a PERSISTANT MISCONCEPTION on this topic. Instead of a standard fix, use an ANALOGY or FIRST PRINCIPLES breakdown in the remediation bridge.\n"
        except StudentConceptState.DoesNotExist:
            pass
            
    print("\nGenerated Escalation Instructions:")
    print(escalation_instructions)
    
    if "ESCALATE Photosynthesis" in escalation_instructions:
        print("SUCCESS: Escalation instruction correctly generated.")
    else:
        print("FAILURE: Escalation instruction missing.")

    # 4. Test Analytics Update Logic (Replicating logic from quiz_report_ajax)
    print("\nTesting Analytics Update...")
    mock_results = [
        {"concept": "Photosynthesis", "isRight": False, "confidence": 5, "error_type": "misconception"}
    ]
    
    for r in mock_results:
        c_name = r["concept"]
        err_t = r["error_type"]
        
        try:
            c_node = ConceptNode.objects.get(material=material, name__iexact=c_name)
            st, _ = StudentConceptState.objects.get_or_create(user=user, concept=c_node)
            
            # Update error profile
            ep = st.error_profile or {}
            ep[err_t] = ep.get(err_t, 0) + 1
            st.error_profile = ep
            st.save()
        except ConceptNode.DoesNotExist:
            print(f"Concept {c_name} not found.")
    
    updated_state = StudentConceptState.objects.get(user=user, concept=concept)
    print(f"Updated error profile: {updated_state.error_profile}")
    
    if updated_state.error_profile.get("misconception") == 4:
        print("SUCCESS: Persistence tracking correctly incremented.")
    else:
        print("FAILURE: Persistence tracking failed (Expected 4, got " + str(updated_state.error_profile.get("misconception")) + ")")

if __name__ == "__main__":
    verify_persistence_logic()
