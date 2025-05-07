import os
import sys
import subprocess

def create_large_icon():
    # Path to the original icon
    original_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
    
    # Path for the new 512x512 icon
    new_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon_512.png')
    
    # Check if the original icon exists
    if not os.path.exists(original_icon_path):
        print(f"Error: Original icon not found at {original_icon_path}")
        return
    
    # Create a simple HTML file that will resize the image using canvas
    html_path = os.path.join(os.path.dirname(__file__), 'resize_icon.html')
    with open(html_path, 'w') as f:
        f.write(f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Icon Resizer</title>
        </head>
        <body>
            <canvas id="canvas" width="512" height="512" style="display:none;"></canvas>
            <img id="source" src="icons/icon.png" style="display:none;">
            <script>
                window.onload = function() {{
                    var canvas = document.getElementById('canvas');
                    var ctx = canvas.getContext('2d');
                    var img = document.getElementById('source');
                    
                    // Clear canvas with transparent background
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                    
                    // Calculate position to center the image
                    var x = (512 - img.width) / 2;
                    var y = (512 - img.height) / 2;
                    
                    // Draw the image centered
                    ctx.drawImage(img, x, y);
                    
                    // Convert to data URL
                    var dataURL = canvas.toDataURL('image/png');
                    
                    // Display the data URL for copying
                    document.body.innerHTML = '<textarea style="width:100%;height:200px;">' + dataURL + '</textarea>' +
                                             '<p>Copy this data URL and save it as a PNG file using an online converter.</p>';
                }};
            </script>
        </body>
        </html>
        ''')
    
    print(f"Created HTML resizer at {html_path}")
    print("Please open this HTML file in a browser, copy the data URL, and use an online converter to save it as a PNG.")
    print("Then save the resulting PNG as 'icons/icon_512.png'")
    
    # Alternative approach: create a simple copy of the original icon
    try:
        # Just copy the original icon to the new location
        import shutil
        shutil.copy2(original_icon_path, new_icon_path)
        print(f"Copied original icon to {new_icon_path}")
        print("Note: This is just a copy, not resized to 512x512.")
        print("For production, please use the HTML method above or an image editor to create a proper 512x512 icon.")
    except Exception as e:
        print(f"Error copying icon: {e}")

if __name__ == "__main__":
    create_large_icon()