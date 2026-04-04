
def count_braces(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract ALL script blocks
    import re
    # Match <script> and <script ...>
    scripts = re.findall(r'<script.*?>\s*(.*?)\s*</script>', content, re.DOTALL)
    
    total_open = 0
    total_close = 0
    
    for i, script in enumerate(scripts):
        open_count = script.count('{')
        close_count = script.count('}')
        print(f"Script {i}: Open={open_count}, Close={close_count}")
        total_open += open_count
        total_close += close_count
    
    print(f"TOTAL: Open={total_open}, Close={total_close}")

if __name__ == "__main__":
    count_braces(r'c:\Users\danie\Downloads\UNIXA-main\materials\templates\materials\viewer.html')
