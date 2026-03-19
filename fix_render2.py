with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the renderMathInElement block after streaming finishes (lines 865-868)
old1 = """        if (wrap) wrap.dataset.plain = fullText;
        document.getElementById('actions-' + msgId).style.display = '';
        if (typeof renderMathInElement === 'function') {
            try { renderMathInElement(el, { delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}], throwOnError: false }); } catch(e) {}
        }
        NexaUI.scrollToBottom();"""

new1 = """        if (wrap) wrap.dataset.plain = fullText;
        document.getElementById('actions-' + msgId).style.display = '';
        NexaUI.scrollToBottom();"""

# Remove renderMathInElement after renderBoardHTML in board render
old2 = """            element.innerHTML = NexaChat.renderBoardHTML(text);
            if (typeof renderMathInElement === 'function') {
                try { renderMathInElement(element, { delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}], throwOnError: false }); } catch(e) {}
            }"""

new2 = """            element.innerHTML = NexaChat.renderBoardHTML(text);"""

# Remove renderMathInElement in parseBoard
old3 = """        content.innerHTML = html;
        if (typeof renderMathInElement === 'function') {
            try { renderMathInElement(content, { delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}], throwOnError: false }); } catch(e) {}
        }"""

new3 = """        content.innerHTML = html;"""

# Remove the init renderMathInElement block
old4 = """    // Render KaTeX on existing messages
    if (typeof renderMathInElement === 'function') {
        document.querySelectorAll('.board-render').forEach(el => {
            try { renderMathInElement(el, { delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}], throwOnError: false }); } catch(e) {}
        });
    }"""

new4 = ""

replacements = [(old1, new1), (old2, new2), (old3, new3), (old4, new4)]
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print('Replaced:', repr(old[:60]))
    else:
        print('NOT FOUND:', repr(old[:60]))

with open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
