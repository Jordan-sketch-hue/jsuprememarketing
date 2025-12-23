Place background images you want the site to use into this folder.

Filename mapping used by the app (see `app.py -> bg_image_for`):

- ./images/home_bg_1920x1080.jpg
- ./images/insights_bg_1920x1080.jpg
- ./images/start_bg_1920x1080.jpg
- ./images/privacy_bg_1920x1080.jpg
- ./images/terms_bg_1920x1080.jpg
 ./images/thank_you_bg_1920x1080.jpg

How the app serves images:
- The app prefers `./static/img/` if present. It will also look in `./images/`.
- When a file above exists, the app returns a URL like `/static/img/<filename>` which maps to whichever folder contains the file.

Quick options:
1) Save your attached image(s) into this folder with one of the filenames above (e.g., `home_bg_1920x1080.jpg`).
2) Run the helper script at `scripts/fetch_placeholder_images.py` to download example backgrounds.

To use the helper script:

1. Install dependencies:

   pip install -r requirements.txt

2. Run the script:

   python scripts/fetch_placeholder_images.py

This will download 1920x1080 placeholder images into `images/` using the filenames above.

After adding images, restart the Flask server if it's already running.