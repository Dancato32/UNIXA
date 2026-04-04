
def check_braces(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract script content
    import re
    scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
    
    for i, script in enumerate(scripts):
        stack = []
        for j, char in enumerate(script):
            if char == '{':
                stack.append(j)
            elif char == '}':
                if not stack:
                    print(f"Extra closing brace in script {i} at position {j}")
                else:
                    stack.pop()
        
        if stack:
            for pos in stack:
                # Find line number
                line_no = content[:content.find(script) + pos].count('\n') + 1
                print(f"Unclosed opening brace in script {i} at line {line_no}")

if __name__ == "__main__":
    check_braces(r'c:\Users\danie\Downloads\UNIXA-main\materials\templates\materials\viewer.html')
