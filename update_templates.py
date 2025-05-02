#!/usr/bin/env python3
"""
Script to update all degree page templates to include the reviews section.
"""

import os
import re

# List of all degree page templates
degree_templates = [
    'graduates_msc.html',
    'graduates_mcom.html',
    'graduates_ma.html',
    'graduates_med.html',
    'graduates_pgdm.html',
    'students_arts_ba.html',
    'students_science_bsc.html',
    'students_commerce_bba.html',
    'students_commerce_bcom.html',
    'students_education_bed.html',
    'students_science_btech.html'
]

# Path to templates directory
templates_dir = 'templates'

# Pattern to match the end of the content block
end_pattern = re.compile(r'\s+</div>\n</div>\n{% endblock %}')

# Replacement text
replacement = '''    </div>
    
    <!-- Include the reviews section -->
    {% include 'reviews_section.html' %}
</div>
{% endblock %}'''

# Update each template
for template in degree_templates:
    template_path = os.path.join(templates_dir, template)
    
    # Check if file exists
    if not os.path.exists(template_path):
        print(f"Warning: {template_path} does not exist. Skipping.")
        continue
    
    # Read the file content
    with open(template_path, 'r') as file:
        content = file.read()
    
    # Replace the end pattern with the new content
    updated_content = end_pattern.sub(replacement, content)
    
    # Write the updated content back to the file
    with open(template_path, 'w') as file:
        file.write(updated_content)
    
    print(f"Updated {template_path}")

print("All templates updated successfully!")