with open('materials/views.py', encoding='utf-8') as f:
    content = f.read()

# Find the free_models list and replace it — llama first, it handles context best
old_models = '''        free_models = [
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "google/gemma-3-27b-it:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen3-4b:free",
            "google/gemma-3-12b-it:free",
        ]'''

new_models = '''        free_models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "mistralai/mistral-small-3.1-24b-instruct:free",
            "google/gemma-3-27b-it:free",
            "google/gemma-3-12b-it:free",
        ]'''

assert old_models in content, "free_models block not found"
content = content.replace(old_models, new_models, 1)

# Fix the full_text limit — 6000 chars is safer for free models
content = content.replace(
    'full_text = material.extracted_text[:12000]',
    'full_text = material.extracted_text[:6000]',
    1
)

with open('materials/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Models reordered, context capped at 6000.")
