#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Application Directories and Files
This script ensures all necessary directories and placeholder files exist
"""

import os
import sys
import logging
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Project paths
project_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(project_dir, 'app')
static_dir = os.path.join(app_dir, 'static')
splash_dir = os.path.join(static_dir, 'splash')
uploads_dir = os.path.join(static_dir, 'uploads')
icons_dir = os.path.join(static_dir, 'icons')

# Create required directories
required_dirs = [
    os.path.join(app_dir, 'logs'),
    os.path.join(app_dir, 'data'),
    os.path.join(app_dir, 'backups'),
    splash_dir,
    uploads_dir,
    icons_dir
]

def create_directories():
    """Create all required directories"""
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    return True

def create_placeholder_image(width, height, filename, text=None):
    """Create a placeholder image with text"""
    # Create a blue-gray gradient background
    img = Image.new('RGB', (width, height), color=(24, 62, 110))
    draw = ImageDraw.Draw(img)
    
    # Draw text if provided
    if text:
        try:
            # Try to use a built-in font or default to system font
            font_size = min(width, height) // 10
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Draw the text in the center
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
            position = ((width - text_width) // 2, (height - text_height) // 2)
            draw.text(position, text, font=font, fill=(255, 255, 255))
            
        except Exception as e:
            logger.warning(f"Error adding text to image: {e}")
    
    # Save the image
    try:
        img.save(filename)
        logger.info(f"Created placeholder image: {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving image {filename}: {e}")
        return False

def create_splash_images():
    """Create splash screen images for different device sizes"""
    splash_sizes = [
        (640, 1136, "splash-640x1136.png", "640×1136"),
        (750, 1334, "splash-750x1334.png", "750×1334"),
        (1242, 2208, "splash-1242x2208.png", "1242×2208"),
        (1125, 2436, "splash-1125x2436.png", "1125×2436")
    ]
    
    for width, height, filename, size_text in splash_sizes:
        filepath = os.path.join(splash_dir, filename)
        text = f"Quincaillerie App\n{size_text}"
        create_placeholder_image(width, height, filepath, text)
    
    return True

def create_icon_images():
    """Create icon images in different sizes"""
    icon_sizes = [
        (72, 72, "icon-72x72.png"),
        (96, 96, "icon-96x96.png"),
        (128, 128, "icon-128x128.png"),
        (144, 144, "icon-144x144.png"),
        (152, 152, "icon-152x152.png"),
        (192, 192, "icon-192x192.png"),
        (384, 384, "icon-384x384.png"),
        (512, 512, "icon-512x512.png"),
        (180, 180, "apple-touch-icon.png")
    ]
    
    for width, height, filename in icon_sizes:
        filepath = os.path.join(static_dir, filename)
        text = f"{width}×{height}" if width > 72 else None
        create_placeholder_image(width, height, filepath, text)
    
    return True

def main():
    """Main execution function"""
    logger.info("Setting up application directories and placeholder files...")
    
    # Create required directories
    create_directories()
    
    # Create splash screen images
    create_splash_images()
    
    # Create icon images
    create_icon_images()
    
    logger.info("Directory and file setup complete!")
    return True

if __name__ == "__main__":
    try:
        # Check if Pillow is installed
        import PIL
        success = main()
        sys.exit(0 if success else 1)
    except ImportError:
        logger.error("Pillow library is required to create placeholder images.")
        logger.error("Please install it using: pip install pillow")
        sys.exit(1)
