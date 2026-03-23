with open('community/templates/community/workspace_detail.html', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')

OLD = """/* Break ws-shell out of the .page wrapper */
.page:has(.ws-shell){padding:0;max-width:100%;margin:0;}
.ws-shell{display:flex;height:calc(100dvh - 48px);background:var(--ws-bg);overflow:hidden;}"""

NEW = """/* Make workspace fill the full available area */
.page:has(.ws-shell){padding:0;max-width:100%;margin:0;height:100%;}
.content-scroll:has(.ws-shell){overflow:hidden;padding:0;height:calc(100dvh - 48px);}
.ws-shell{display:flex;height:100%;width:100%;background:var(--ws-bg);overflow:hidden;}"""

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print('Fixed (exact)')
elif OLD.replace('\n','\r\n') in content:
    content = content.replace(OLD.replace('\n','\r\n'), NEW.replace('\n','\r\n'), 1)
    print('Fixed (CRLF)')
else:
    print('ERROR: not found')

with open('community/templates/community/workspace_detail.html', 'wb') as f:
    f.write(content.encode('utf-8'))
print('Written')
