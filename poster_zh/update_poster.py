import re

# Read base64
with open("qr_base64.txt", "r") as f:
    new_base64 = f.read().strip()

html_path = "aina-poster-final.html"
with open(html_path, "r") as f:
    content = f.read()

# Regex to find the qr-image src
# <img class="qr-image" src="data:image/jpeg;base64,..."
# Be careful with matching.
pattern = r'(<img class="qr-image" src="data:image/jpeg;base64,)([^"]+)(")'

# Check if match exists
if re.search(pattern, content):
    new_content = re.sub(pattern, lambda m: m.group(1) + new_base64 + m.group(3), content)
    with open(html_path, "w") as f:
        f.write(new_content)
    print("Updated HTML with new QR code.")
else:
    print("Could not find QR image tag to replace.")
