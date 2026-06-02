import os
import re

def remove_defer(match):
    tag = match.group(0)
    # Remove 'defer' keyword (either 'defer' or 'defer=""' or 'defer="defer"')
    cleaned = re.sub(r'\bdefer\b(?:\s*=\s*["\']\w*["\'])?', '', tag)
    # Normalize spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = cleaned.replace(' >', '>')
    return cleaned

def main():
    root_dir = r"c:\Users\HP\Desktop\skillswap-campus-complete\frontend"
    # Match any script tag containing socket.io
    pattern = re.compile(r'<script\b[^>]*src="[^"]*socket\.io[^"]*"[^>]*>\s*</script>', re.IGNORECASE)
    
    count = 0
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = pattern.sub(remove_defer, content)
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Removed defer from: {file}")
                    count += 1
    print(f"Completed! Modified {count} files.")

if __name__ == "__main__":
    main()
