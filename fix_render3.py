with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('    renderBoardHTML(raw) {')
end = content.find('\n    renderLines(lines) {', start)
end2 = content.find('\n    }', end) + 6  # include closing brace

old_block = content[start:end2]
print('Replacing block of', len(old_block), 'chars')

new_block = r"""    renderBoardHTML(raw) {
        if (!raw) return '';

        // Step 1: normalise all LaTeX delimiter variants to $ and $$
        let text = raw
            .replace(/\\\\\(/g, '$').replace(/\\\\\)/g, '$')
            .replace(/\\\(/g, '$').replace(/\\\)/g, '$')
            .replace(/\\\\\[/g, '$$').replace(/\\\\\]/g, '$$')
            .replace(/\\\[/g, '$$').replace(/\\\]/g, '$$');

        // Step 2: extract math blocks BEFORE markdown parsing
        // Use unique tokens that marked won't touch
        const mathStore = [];
        const PH = '\x02MATH';  // non-printable prefix, safe from markdown

        // Display math: $$...$$ (must come before inline)
        text = text.replace(/\$\$([\s\S]+?)\$\$/g, function(_, m) {
            var idx = mathStore.length;
            mathStore.push({ display: true, src: m.trim() });
            return '\n\n' + PH + 'D' + idx + '\x03\n\n';
        });

        // Inline math: $...$
        text = text.replace(/\$([^$\n]+?)\$/g, function(_, m) {
            var idx = mathStore.length;
            mathStore.push({ display: false, src: m.trim() });
            return PH + 'I' + idx + '\x03';
        });

        // Step 3: render markdown
        var html = '';
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            html = marked.parse(text);
        } else {
            html = '<p>' + text.replace(/\n\n+/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
        }

        // Step 4: restore math with KaTeX
        // Display math placeholder (may be inside a <p> tag from marked)
        html = html.replace(/<p>\s*\x02MATHD(\d+)\x03\s*<\/p>/g, function(_, i) {
            var m = mathStore[parseInt(i)];
            if (typeof katex === 'undefined') return '<div class="br-math-display">$$' + m.src + '$$</div>';
            try {
                return '<div class="br-math-display">' + katex.renderToString(m.src, { displayMode: true, throwOnError: false }) + '</div>';
            } catch(e) { return '<div class="br-math-display">$$' + m.src + '$$</div>'; }
        });
        // Fallback: display math not wrapped in <p>
        html = html.replace(/\x02MATHD(\d+)\x03/g, function(_, i) {
            var m = mathStore[parseInt(i)];
            if (typeof katex === 'undefined') return '<div class="br-math-display">$$' + m.src + '$$</div>';
            try {
                return '<div class="br-math-display">' + katex.renderToString(m.src, { displayMode: true, throwOnError: false }) + '</div>';
            } catch(e) { return '<div class="br-math-display">$$' + m.src + '$$</div>'; }
        });
        // Inline math
        html = html.replace(/\x02MATHI(\d+)\x03/g, function(_, i) {
            var m = mathStore[parseInt(i)];
            if (typeof katex === 'undefined') return '$' + m.src + '$';
            try {
                return katex.renderToString(m.src, { displayMode: false, throwOnError: false });
            } catch(e) { return '$' + m.src + '$'; }
        });

        return html;
    },

    renderLines(lines) {
        return this.renderBoardHTML(lines.join('\n'));
    }"""

new_content = content[:start] + new_block + content[end2:]

with open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done. New block length:', len(new_block))
