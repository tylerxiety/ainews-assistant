import base64
from PIL import Image
import sys
import os

image_path = "/Users/tylerxie/.gemini/antigravity/brain/25c6472e-342f-4c11-b2cf-c0bffb316250/uploaded_media_1769870408166.jpg"

try:
    img = Image.open(image_path)
    width, height = img.size
    
    # The user wants to avoid the icon above the title.
    # In a WeChat group QR screenshot, the QR code is roughly in the middle.
    # We want a square crop for the poster.
    
    # Let's try to find the center square.
    # Usually the QR code is about 60-70% of the width.
    
    # Let's define a crop size.
    crop_size = min(width, height)
    
    # Center crop
    left = (width - crop_size) / 2
    top = (height - crop_size) / 2
    right = (width + crop_size) / 2
    bottom = (height + crop_size) / 2
    
    # Adjust top to be slightly lower if we want to avoid top content? 
    # Actually, the user said "move the qr code up bit".
    # if the icon is showing, it means the crop is too high (incorporating top elements).
    # So we want to crop lower? 
    # Wait, "move the qr code up bit" in the context of the poster frame means shift the image content up?
    # No, "so do not show the half icon above the group title". 
    # If the user sees the icon, it means the viewer is seeing the part ABOVE the QR code.
    # So we need to crop out the top part more aggressively.
    
    # Let's assume the QR code is square and centered horizontally.
    # We will approximate the QR code location.
    # In a typical screenshot, the QR code starts below the header.
    
    # We'll stick to a center square crop first, but maybe zoom in a bit (crop inner).
    # If we crop the center square of a vertical screenshot, we usually get the middle part.
    # The icon is usually in the top half.
    
    # Let's try cropping the center square.
    
    # Actually, let's take a crop that is 80% of width, centered.
    crop_dim = int(width * 0.8)
    
    # Calculate center
    center_x = width // 2
    center_y = height // 2
    
    # The QR code center might be slightly lower than image center because of header? 
    # Or higher because of footer text?
    # Usually it's roughly center.
    
    # Let's shift the crop down slightly to avoid the top icon if centering captures it.
    # But usually center crop removes top and bottom of a phone screenshot effectively.
    
    # Let's just do a center square crop based on width (since it's portrait usually).
    # And we'll crop a bit off the edges to zoom in on the QR code.
    
    final_size = width # We'll start with full width square
    
    # Create a square crop
    # If height > width, we take the middle 'width' height.
    if height > width:
        top_y = (height - width) // 2
        # However, we might want to nudge it down if the top icon is appearing. 
        # But if the previous one showed an icon, maybe it wasn't cropping enough.
        # Let's try to just take the center square.
        crop_box = (0, top_y, width, top_y + width)
    else:
        # Landscape or square
        left_x = (width - height) // 2
        crop_box = (left_x, 0, left_x + height, height)
        
    cropped_img = img.crop(crop_box)
    
    # Save to buffer
    from io import BytesIO
    buffered = BytesIO()
    cropped_img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    # Print the base64 string
    print(img_str)

except Exception as e:
    sys.stderr.write(f"Error: {e}")
    sys.exit(1)
