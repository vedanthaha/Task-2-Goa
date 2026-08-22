
import sys
from PIL import Image

def process_icon(input_path, out_ico_path, out_apple_path):
    img = Image.open(input_path).convert("RGBA")
    
    # Get bounding box of non-transparent pixels to crop whitespace
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    
    # Make it square by padding with transparent pixels if necessary
    width, height = img.size
    max_dim = max(width, height)
    new_img = Image.new("RGBA", (max_dim, max_dim), (0, 0, 0, 0))
    # Center it
    new_img.paste(img, ((max_dim - width) // 2, (max_dim - height) // 2))
    
    # Save favicon.ico with multiple sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48)]
    new_img.save(out_ico_path, format="ICO", sizes=icon_sizes)
    print(f"Saved {out_ico_path} with sizes {icon_sizes}")
    
    # Save apple-icon.png (usually 180x180)
    apple_img = new_img.resize((180, 180), resample=Image.Resampling.LANCZOS)
    apple_img.save(out_apple_path, format="PNG")
    print(f"Saved {out_apple_path} with size 180x180")

process_icon("public/voice-logo.png", "src/app/favicon.ico", "src/app/apple-icon.png")

