# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pillow",
# ]
# ///

from PIL import Image
import base64
from io import BytesIO

def crop_center_square(img):
    width, height = img.size
    
    # We want a tighter crop to avoid the icon/text above the QR code.
    # Let's crop to 75% of the width.
    # And we'll center this square in the image.
    
    crop_dim = int(min(width, height) * 0.75)
    
    center_x = width // 2
    center_y = height // 2
    
    # Typically QR code is slightly above the visual center of the screen because of footer? 
    # Or below header?
    # Let's stick to geometric center of the screenshot.
    
    half_crop = crop_dim // 2
    
    left = center_x - half_crop
    right = center_x + half_crop
    top = center_y - half_crop
    bottom = center_y + half_crop
    
    img_cropped = img.crop((left, top, right, bottom))
    return img_cropped

if __name__ == "__main__":
    img = Image.open("qrcode.jpg")
    cropped = crop_center_square(img)
    
    buffered = BytesIO()
    cropped.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    print(img_str)
