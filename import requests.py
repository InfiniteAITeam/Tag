import requests
import json
import os

# ================= CONFIGURATION =================
# Replace these with your actual details
FIGMA_TOKEN = "YOUR_ACCESS_TOKEN_HERE"
FILE_KEY = "YOUR_FILE_KEY_HERE"

# Configuration for image quality
SCALE = 1  # 1 for standard, 2 for retina
FORMAT = "png" # png, jpg, svg, or pdf
OUTPUT_FOLDER = "figma_export"
# =================================================

headers = {
    "X-Figma-Token": FIGMA_TOKEN
}

def extract_text_from_node(node):
    """Recursively find all text within a specific screen/node."""
    text_content = []
    
    if "children" in node:
        for child in node["children"]:
            text_content.extend(extract_text_from_node(child))
            
    if node["type"] == "TEXT" and "characters" in node:
        # You can also capture style info here (font, size) if needed
        text_content.append(node["characters"])
        
    return text_content

def main():
    # 1. Create output directory
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created folder: {OUTPUT_FOLDER}")

    # 2. Get the File Data (The JSON Tree)
    print("Fetching file structure...")
    url_file = f"https://api.figma.com/v1/files/{FILE_KEY}"
    response = requests.get(url_file, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching file: {response.json()}")
        return

    data = response.json()
    document = data['document']
    
    # 3. Identify all "Screens" (Top-Level Frames) across all pages
    screens = {} # Dictionary to store {node_id: node_data}
    
    print("Scanning for screens...")
    for page in document['children']:
        print(f" - Scanning Page: {page['name']}")
        for node in page['children']:
            # We assume Top-Level FRAMES are the screens
            if node['type'] == 'FRAME':
                screens[node['id']] = {
                    "name": node['name'],
                    "data": node
                }

    if not screens:
        print("No top-level frames found. Make sure your screens are not inside Groups.")
        return

    print(f"Found {len(screens)} screens. Fetching image URLs...")

    # 4. Get Image URLs for these screens
    # The API requires a comma-separated list of IDs
    node_ids = list(screens.keys())
    node_ids_string = ",".join(node_ids)
    
    url_images = f"https://api.figma.com/v1/images/{FILE_KEY}"
    params = {
        "ids": node_ids_string,
        "format": FORMAT,
        "scale": SCALE
    }
    
    img_response = requests.get(url_images, headers=headers, params=params)
    img_data = img_response.json()
    
    if "err" in img_data and img_data["err"]:
        print(f"Error getting images: {img_data['err']}")
        return

    # 5. Process each screen: Download Image + Extract Text
    images_map = img_data['images'] # {node_id: url}
    
    for node_id, screen_info in screens.items():
        safe_name = "".join([c for c in screen_info['name'] if c.isalnum() or c in (' ', '-', '_')]).strip()
        print(f"Processing: {safe_name}...")

        # --- A. Save Text Content ---
        all_text = extract_text_from_node(screen_info['data'])
        text_filename = f"{OUTPUT_FOLDER}/{safe_name}.txt"
        with open(text_filename, "w", encoding="utf-8") as f:
            f.write(f"Screen Name: {screen_info['name']}\n")
            f.write(f"Node ID: {node_id}\n")
            f.write("="*30 + "\n")
            f.write("\n".join(all_text))

        # --- B. Download Image ---
        image_url = images_map.get(node_id)
        if image_url:
            img_filename = f"{OUTPUT_FOLDER}/{safe_name}.{FORMAT}"
            img_r = requests.get(image_url)
            if img_r.status_code == 200:
                with open(img_filename, "wb") as f:
                    f.write(img_r.content)
            else:
                print(f"   Failed to download image for {safe_name}")
        else:
            print(f"   No image URL generated for {safe_name} (might be empty)")

    print(f"\nDone! Check the '{OUTPUT_FOLDER}' folder.")

if __name__ == "__main__":
    main()