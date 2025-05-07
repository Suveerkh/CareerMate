import os

def create_blank_icon():
    # Path for the new 512x512 icon
    new_icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon_512.png')
    
    # Create a blank 512x512 PNG file
    with open(new_icon_path, 'wb') as f:
        # PNG header
        f.write(b'\x89PNG\r\n\x1a\n')
        
        # IHDR chunk (image header)
        f.write(b'\x00\x00\x00\x0d')  # Length of IHDR chunk data (13 bytes)
        f.write(b'IHDR')              # Chunk type
        f.write(b'\x00\x00\x02\x00')  # Width (512)
        f.write(b'\x00\x00\x02\x00')  # Height (512)
        f.write(b'\x08')              # Bit depth (8)
        f.write(b'\x06')              # Color type (RGBA)
        f.write(b'\x00')              # Compression method
        f.write(b'\x00')              # Filter method
        f.write(b'\x00')              # Interlace method
        f.write(b'\x00\x00\x00\x00')  # CRC (placeholder)
        
        # IDAT chunk (image data - minimal transparent image)
        # This is a very small transparent image data
        f.write(b'\x00\x00\x00\x0e')  # Length of IDAT chunk data
        f.write(b'IDAT')              # Chunk type
        f.write(b'\x78\x9c\x63\x60\x60\x60\x00\x00\x00\x04\x00\x01')  # Minimal compressed data
        f.write(b'\x00\x00\x00\x00')  # CRC (placeholder)
        
        # IEND chunk (end of image)
        f.write(b'\x00\x00\x00\x00')  # Length of IEND chunk data (0 bytes)
        f.write(b'IEND')              # Chunk type
        f.write(b'\xae\x42\x60\x82')  # CRC
    
    print(f"Created blank 512x512 icon at {new_icon_path}")

if __name__ == "__main__":
    create_blank_icon()