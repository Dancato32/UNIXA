content = open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8').read()
old = "delimiters: [{left:'$',right:'$',display:true},{left:'$',right:'$',display:false}]"
new = "delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]"
count = content.count(old)
print('Found', count, 'occurrences')
fixed = content.replace(old, new)
open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8').write(fixed)
print('Done')
