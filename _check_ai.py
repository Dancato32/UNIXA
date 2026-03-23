with open('community/templates/community/nexa_home.html','rb') as f:
    raw = f.read()
c = raw.decode('utf-8','replace')

# Find nxWsLoadOverviewAI
idx = c.find('function nxWsLoadOverviewAI(')
print(c[idx:idx+800])
print()
# Find the chat endpoint used elsewhere (working chat)
idx2 = c.find("fetch('/ai_tutor/chat/'")
print('ai_tutor/chat/ at:', idx2)
idx3 = c.find("fetch(\"/ai_tutor/chat/\"")
print('ai_tutor/chat/ (double quote) at:', idx3)
# Check what endpoint the main chat uses
idx4 = c.find('/community/nexa/chat/')
print('/community/nexa/chat/ at:', idx4)
idx5 = c.find('nexa/chat')
print('nexa/chat at:', idx5, repr(c[idx5:idx5+60]) if idx5!=-1 else '')
