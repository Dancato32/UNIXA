with open('community/templates/community/workspace_detail.html', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

# Fix the broken Django template logic for chat message classes
# The old logic: {% if msg.sender == request.user and not msg.content|slice:':4' == '[AI]' %}
# Django doesn't support `not x == y` inline — it needs `x != y` or a different structure
OLD = """        <div class="chat-msg {% if msg.sender == request.user and not msg.content|slice:':4' == '[AI]' %}mine{% elif msg.content|slice:':4' == '[AI]' %}ai-msg{% endif %}" id="msg-{{ msg.id }}">"""

NEW = """        {% with is_ai=msg.content|slice:":4" %}
        <div class="chat-msg {% if is_ai == '[AI]' %}ai-msg{% elif msg.sender == request.user %}mine{% endif %}" id="msg-{{ msg.id }}">
        {% endwith %}"""

# Actually we need to keep the with block open through the end of the message div
# Let's do a more targeted fix — just fix the class line and keep the rest
OLD2 = '        <div class="chat-msg {% if msg.sender == request.user and not msg.content|slice:\':4\' == \'[AI]\' %}mine{% elif msg.content|slice:\':4\' == \'[AI]\' %}ai-msg{% endif %}" id="msg-{{ msg.id }}">'

NEW2 = '        <div class="chat-msg {% if msg.content|slice:":4" == "[AI]" %}ai-msg{% elif msg.sender == request.user %}mine{% endif %}" id="msg-{{ msg.id }}">'

if OLD2 in content:
    content = content.replace(OLD2, NEW2, 1)
    print('Template fix applied (exact)')
elif OLD2.replace("'", '"') in content:
    content = content.replace(OLD2.replace("'", '"'), NEW2, 1)
    print('Template fix applied (quote variant)')
else:
    # Try finding it by a unique substring
    marker = 'and not msg.content|slice'
    if marker in content:
        # Find the full line
        idx = content.index(marker)
        line_start = content.rindex('\n', 0, idx) + 1
        line_end = content.index('\n', idx)
        old_line = content[line_start:line_end]
        new_line = '        <div class="chat-msg {% if msg.content|slice:":4" == "[AI]" %}ai-msg{% elif msg.sender == request.user %}mine{% endif %}" id="msg-{{ msg.id }}">'
        content = content[:line_start] + new_line + content[line_end:]
        print('Template fix applied (line replacement)')
    else:
        print('Template fix: marker not found, checking current state...')
        # Check what's there now
        if 'msg.content|slice:":4" == "[AI]" %}ai-msg' in content:
            print('Already fixed!')
        else:
            print('ERROR: could not find the line to fix')

with open('community/templates/community/workspace_detail.html', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Written successfully')
