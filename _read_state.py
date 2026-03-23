with open('community/templates/community/workspace_detail.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

print('File size:', len(c))

# Find task engine modal
idx = c.find('task-engine-modal')
print('task-engine-modal at:', idx)

# Find existing tools/panels
for tool in ['nexa-word', 'nexa-sheets', 'nexa-slides', 'panel-office', 'office-suite', 'ws-editor', 'deep-search', 'aim-view-finish']:
    i = c.find(tool)
    if i != -1:
        print(tool, '->', i, repr(c[i:i+60]))

# Find the task engine JS functions
for fn in ['openTaskEngine', 'teShowTab', 'teStartTask', 'teRunAutopilot', 'teSaveEntryData']:
    i = c.find('function ' + fn)
    print(fn, '->', i)

# Find where the main script block ends
idx_script_end = c.rfind('</script>')
print('Last </script> at:', idx_script_end)
print(repr(c[idx_script_end-100:idx_script_end+20]))
