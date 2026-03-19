with open('ai_tutor/templates/ai_tutor/chat.html', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '    renderBoardHTML(raw) {'
start_idx = content.find(start_marker)

render_lines_start = content.find('    renderLines(lines) {', start_idx)
search_from = render_lines_start + 100
end_idx = content.find('\n};\n', search_from)
block_end = content.rfind('\n    }', start_idx, end_idx + 4)
old_block = content[start_idx:block_end + 6]

new_block = r"""    renderBoardHTML(raw) {
        // Normalise LaTeX delimiters
        let text = raw
            .replace(/\\\(/g, '$').replace(/\\\)/g, '$')
            .replace(/\\\[/g, '\n$$\n').replace(/\\\]/g, '\n$$\n');

        // Protect math from marked parser using placeholders
        const mathStore = [];
        // Display math $$...$$
        text = text.replace(/\$\$([\s\S]+?)\$\$/g, function(_, m) {
            mathStore.push({ display: true, src: m });
            return 'MATHPH_D_' + (mathStore.length - 1) + '_END';
        });
        // Inline math $...$
        text = text.replace(/\$([^\n$]+?)\$/g, function(_, m) {
            mathStore.push({ display: false, src: m });
            return 'MATHPH_I_' + (mathStore.length - 1) + '_END';
        });

        // Render markdown
        let html = '';
        if (typeof marked !== 'undefined') {
            marked.setOptions({ breaks: true, gfm: true });
            html = marked.parse(text);
        } else {
            html = '<p>' + text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
        }

        // Restore math placeholders with KaTeX
        html = html.replace(/MATHPH_D_(\d+)_END/g, function(_, i) {
            var m = mathStore[parseInt(i)];
            try {
                return '<div class="br-math-display">' + katex.renderToString(m.src.trim(), { displayMode: true, throwOnError: false }) + '</div>';
            } catch(e) { return '<div class="br-math-display">$$' + m.src + '$$</div>'; }
        });
        html = html.replace(/MATHPH_I_(\d+)_END/g, function(_, i) {
            var m = mathStore[parseInt(i)];
            try {
                return katex.renderToString(m.src.trim(), { displayMode: false, throwOnError: false });
            } catch(e) { return '$' + m.src + '$'; }
        });

        return html;
    },

    renderLines(lines) {
        return this.renderBoardHTML(lines.join('\n'));
    }"""

new_content = content[:start_idx] + new_block + content[block_end + 6:]

with open('ai_tutor/templates/ai_tutor/chat.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done. Old length:', len(old_block), '-> New length:', len(new_block))
