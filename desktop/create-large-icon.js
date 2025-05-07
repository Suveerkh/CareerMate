const fs = require('fs');
const path = require('path');
const { createCanvas, loadImage } = require('canvas');

async function createLargeIcon() {
  try {
    // Path to the original icon
    const originalIconPath = path.join(__dirname, 'icons', 'icon.png');
    
    // Path for the new 512x512 icon
    const newIconPath = path.join(__dirname, 'icons', 'icon-512x512.png');
    
    // Create a 512x512 canvas
    const canvas = createCanvas(512, 512);
    const ctx = canvas.getContext('2d');
    
    // Load the original image
    const img = await loadImage(originalIconPath);
    
    // Calculate position to center the image
    const x = (512 - img.width) / 2;
    const y = (512 - img.height) / 2;
    
    // Draw the image centered on the canvas
    ctx.drawImage(img, x, y);
    
    // Save the canvas as a PNG file
    const out = fs.createWriteStream(newIconPath);
    const stream = canvas.createPNGStream();
    stream.pipe(out);
    
    out.on('finish', () => {
      console.log(`Created 512x512 icon at ${newIconPath}`);
    });
  } catch (error) {
    console.error('Error creating icon:', error);
  }
}

createLargeIcon();