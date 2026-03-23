with open('community/templates/community/workspace_detail.html', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'panel-chat' in line:
        for j in range(i, min(i+6, len(lines))):
            print(f'{j+1}: {lines[j][:150]}')
        print('---')
        break
# Also check task-board height
for i, line in enumerate(lines):
    if 'task-board' in line and 'height' in line:
        print(f'{i+1}: {line[:150]}')
