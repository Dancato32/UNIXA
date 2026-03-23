with open('community/templates/community/base.html', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'content-scroll' in line or 'main-area' in line:
        if '{' in line or 'overflow' in line or 'padding' in line or 'height' in line:
            print(f'{i+1}: {line[:150]}')
