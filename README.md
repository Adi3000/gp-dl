# Google Photos Downloader

**A Python-based Google Photos downloader built with Selenium.**

This tool automates the process of downloading photos from Google Photos albums by simulating user interaction with the web interface. It uses Selenium to open shared album links, click the "Download all" button, and extract the images to your local system.

## ✨ Features

* 🔗 Accepts public/shared Google Photos album URLs
* 🖱️ Simulates browser behavior to download photos via the "Download all" option
* 🗃️ Automatically extracts downloaded `.zip` files into organized folders
* 🛠️ Works without needing any API keys or OAuth setup
* 📂 Supports batch downloading of multiple album links

## 🛑 Why not use the Google Photos API?

As of recent updates, **the original Google Photos API is deprecated**. While the **Google Picker API** is still available, it comes with several major limitations:

* 🚫 You must select each photo manually — no "select all" option
* 📉 Limited to a maximum number of items (up to 100 photos per interaction)
* 🔐 Requires setting up a Google Cloud project and API credentials

Due to these restrictions, this Selenium-based solution is one of the few remaining ways to fully automate bulk downloads from Google Photos albums.

## ⚠️ Disclaimer

* The project was not made by AI, just the README.
* It automates actions that a human user would normally perform in a browser.
* Be aware of Google’s Terms of Service before using this tool.

## 🧰 Requirements

* Python 3.11+
* Selenium
* Chrome or Chromium + WebDriver

## 💡 Usage

```bash
python main.py --album-urls YOUR_ALBUM_LINK_HERE --output-dir test_images
```
