from PIL import Image, ImageDraw, ImageFont
import os

def create_banner():
    # Create a new image with a white background
    width = 1200
    height = 300
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Add text
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf', 60)
    except:
        font = ImageFont.load_default()
    
    text = "Secure Voting Platform"
    # Get text size
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Calculate position to center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Add text to the image
    draw.text((x, y), text, font=font, fill='black')
    
    # Save the image
    image.save('images/banner.png')

if __name__ == '__main__':
    create_banner()