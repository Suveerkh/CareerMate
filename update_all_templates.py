#!/usr/bin/env python3
"""
Script to update all degree page templates to include the reviews section.
"""

import os
import re

# Path to templates directory
templates_dir = 'templates'

# Get all student and graduate templates
student_templates = [f for f in os.listdir(templates_dir) if f.startswith('students_') and f.endswith('.html')]
graduate_templates = [f for f in os.listdir(templates_dir) if f.startswith('graduates_') and f.endswith('.html')]
postgrad_templates = [f for f in os.listdir(templates_dir) if f.startswith('postgraduates_') and f.endswith('.html')]

# Combine all templates
all_templates = student_templates + graduate_templates + postgrad_templates

# Pattern to match the end of the content block
end_pattern = re.compile(r'\s+</div>\n</div>\n{% endblock %}')

# Replacement text
replacement = '''    </div>
    
    <!-- Include the reviews section -->
    {% include 'reviews_section.html' %}
</div>
{% endblock %}'''

# Update each template
for template in all_templates:
    template_path = os.path.join(templates_dir, template)
    
    # Check if file exists
    if not os.path.exists(template_path):
        print(f"Warning: {template_path} does not exist. Skipping.")
        continue
    
    # Read the file content
    with open(template_path, 'r') as file:
        content = file.read()
    
    # Check if the reviews section is already included
    if "{% include 'reviews_section.html' %}" in content:
        print(f"Reviews section already included in {template}. Skipping.")
        continue
    
    # Replace the end pattern with the new content
    if end_pattern.search(content):
        updated_content = end_pattern.sub(replacement, content)
        
        # Write the updated content back to the file
        with open(template_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Updated {template}")
    else:
        print(f"Pattern not found in {template}. Manual update required.")

print("All templates updated successfully!")