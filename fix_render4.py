with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('    renderBoardHTML(raw) {')
end_marker = '    renderLines(lines) {'
end = content.find(end_marker, start)
end2 = content.find('\n    }', end) + 6

old_block = content[start:end2]
print('Replacing', len(old_block), 'chars')

# New implementation - uses safe string placeholders that marked won't mangle
new_block = """    renderBoardHTML(raw) {
        if (!raw) return '';

        // Normalise LaTeX delimiter variants
        var text = raw
            .replace(/\\\\\\\\/g, '\\\\')
            .replace(/\\\\\(/g, '$').replace(/\\\\\)/g, '$')
            .replace(/\\\(/g, '$').replace(/\\\)/g, '$')
            .replace(/\\\\\[/g, '$$').replace(/\\\\\]/g, '$$')
            .replace(/\\\[/g, '$$').replace(/\\\]/g, '$$');

        // Extract math BEFORE markdown parsing (marked would mangle it)
        var mathStore = [];

        // Display math $$...$$ first
        text = text.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, function(_, m) {
            var i = mathStore.length;
            mathStore.push({ display: true, src: m.trim() });
            return 'NEXAMATH_DISPLAY_' + i + '_ENDMATH';
        });

        // Inline math $...$
        text = text.replace(/\\$([^$\\n]+?)\\$/g, function(_, m) {
            var i = mathStore.length;
            mathStore.push({ display: false, src: m.trim() });
            return 'NEXAMATH_INLINE_' + i + '_ENDMATH';
        });

        // Render markdown
        var html = '';
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            html = marked.parse(text);
        } else {
            html = '<p>' + text.replace(/\\n\\n+/g, '</p><p>').replace(/\\n/g, '<br>') + '</p>';
        }

        // Restore display math - handle both <p>PLACEHOLDER</p> and bare
        html = html.replace(/<p>\\s*NEXAMATH_DISPLAY_(\\d+)_ENDMATH\\s*<\\/p>/g, function(_, i) {
            return NexaChat._renderMath(mathStore[parseInt(i)]);
        });
        html = html.replace(/NEXAMATH_DISPLAY_(\\d+)_ENDMATH/g, function(_, i) {
            return NexaChat._renderMath(mathStore[parseInt(i)]);
        });

        // Restore inline math
        html = html.replace(/NEXAMATH_INLINE_(\\d+)_ENDMATH/g, function(_, i) {
            return NexaChat._renderMath(mathStore[parseInt(i)]);
        });

        return html;
    },

    _renderMath(m) {
        if (typeof katex === 'undefined') {
            return m.display
                ? '<div class="br-math-display">$$' + m.src + '$$</div>'
                : '$' + m.src + '$';
        }
        try {
            var rendered = katex.renderToString(m.src, { displayMode: m.display, throwOnError: false });
            return m.display ? '<div class="br-math-display">' + rendered + '</div>' : rendered;
        } catch(e) {
            return m.display ? '<div class="br-math-display">$$' + m.src + '$$</div>' : '$' + m.src + '$';
        }
    },

    renderLines(lines) {
        return this.renderBoardHTML(lines.join('\\n'));
    }"""

new_content = content[:start] + new_block + content[end2:]

with open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done. New block:', len(new_block), 'chars')
