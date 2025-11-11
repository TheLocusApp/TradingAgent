#!/usr/bin/env python3
"""Quick script to fix analyst.html by removing garbage after </html>"""

file_path = r"c:\Users\ahmed\CascadeProjects\moon-dev-ai-agents\src\web\templates\analyst.html"

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the first </html> tag
html_end_line = None
for i, line in enumerate(lines):
    if '</html>' in line:
        html_end_line = i
        break

if html_end_line is not None:
    # Keep only up to and including the </html> line
    clean_lines = lines[:html_end_line + 1]
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(clean_lines)
    
    print(f"✅ Fixed! Removed {len(lines) - len(clean_lines)} garbage lines")
    print(f"File now has {len(clean_lines)} lines")
else:
    print("❌ Could not find </html> tag")
