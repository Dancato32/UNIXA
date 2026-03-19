with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('    renderBoardHTML(raw) {')
# Find end: the closing brace of renderLines
end_search = content.find('    renderLines(lines) {', start)
end_pos = content.find('\n    }', end_search) + 6  # include "    }"

old = content[start:end_pos]
print('Old block length:', len(old))

# Write the new JS directly - no Python escape confusion
# We write the file in two parts around the block
new_js = """    renderBoardHTML(raw) {
        if (!raw) return '';

        var text = raw;

        // Normalise LaTeX delimiters that AI models output
        // \\( ... \\) -> $ ... $   (inline)
        // \\[ ... \\] -> $$ ... $$ (display)
        text = text.replace(/\\\\\(/g, '$').replace(/\\\\\)/g, '$');
        text = text.replace(/\\\\\[/g, '$$').replace(/\\\\\]/g, '$$');

        // Extract math blocks BEFORE markdown parsing
        var mathStore = [];

        // Display math: $$...$$ (greedy-safe, multiline)
        text = text.replace(/\$\$([\s\S]+?)\$\$/g, function(_, m) {
            var idx = mathStore.length;
            mathStore.push({ display: true, src: m.trim() });
            return '\\n\\nNEXAMATH_D_' + idx + '_END\\n\\n';
        });

        // Inline math: $...$ (no newlines inside)
        text = text.replace(/\$([^$\\n]+?)\$/g, function(_, m) {
            var idx = mathStore.length;
            mathStore.push({ display: false, src: m.trim() });
            return 'NEXAMATH_I_' + idx + '_END';
        });

        // Render markdown
        var html = '';
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            html = marked.parse(text);
        } else {
            html = '<p>' + text.replace(/\\n\\n+/g, '</p><p>').replace(/\\n/g, '<br>') + '</p>';
        }

        // Restore display math (marked wraps standalone lines in <p>)
        html = html.replace(/<p>\\s*NEXAMATH_D_(\\d+)_END\\s*<\\/p>/g, function(_, i) {
            return NexaChat._katex(mathStore[parseInt(i)]);
        });
        html = html.replace(/NEXAMATH_D_(\\d+)_END/g, function(_, i) {
            return NexaChat._katex(mathStore[parseInt(i)]);
        });

        // Restore inline math
        html = html.replace(/NEXAMATH_I_(\\d+)_END/g, function(_, i) {
            return NexaChat._katex(mathStore[parseInt(i)]);
        });

        return html;
    },

    _katex(m) {
        if (typeof katex === 'undefined') {
            return m.display
                ? '<div class="br-math-display">$$' + m.src + '$$</div>'
                : '$' + m.src + '$';
        }
        try {
            var out = katex.renderToString(m.src, { displayMode: m.display, throwOnError: false });
            return m.display ? '<div class="br-math-display">' + out + '</div>' : out;
        } catch(e) {
            return m.display ? '<div class="br-math-display">$$' + m.src + '$$</div>' : '$' + m.src + '$';
        }
    },

    renderLines(lines) {
        return this.renderBoardHTML(lines.join('\\n'));
    }"""

new_content = content[:start] + new_js + content[end_pos:]

with open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done. New block length:', len(new_js))

# Verify
with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8') as f:
    verify = f.read()
idx = verify.find('renderBoardHTML(raw)')
print('\n--- VERIFY ---')
print(verify[idx:idx+600])
