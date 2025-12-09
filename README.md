# Media Target Compressor

**Media Target Compressor** is a cross-platform command-line utility written in Python. It takes an image or video input and compresses it to a **specific target file size** (e.g., "Make this video 8MB" or "Make this image 500KB").

It is designed to be intelligent:
*   **Videos:** Calculates the exact bitrate needed based on duration to hit the target size using a 2-pass FFmpeg encoding.
*   **Images:** Uses an iterative algorithm to lower quality or resize dimensions until the file fits the target.

## Features

*   🎯 **Precise Targeting:** Accepts human-readable sizes (e.g., `10MB`, `500KB`, `1GB`).
*   🎬 **Video Support:** Uses industry-standard FFmpeg for high-efficiency H.264 compression.
*   🖼️ **Image Support:** intelligently handles JPEGs and PNGs using Pillow.
*   💻 **Cross-Platform:** Works on Windows, macOS, and Linux.
*   📉 **Smart Logic:** 
    *   If a file is already smaller than the target, it does nothing.
    *   If an image cannot be compressed enough via quality settings, it automatically resizes dimensions.

## Prerequisites

1.  **Python 3.6+**
2.  **FFmpeg** (Required for video processing)

### Installing FFmpeg

*   **Windows:** [Download Build](https://gyan.dev/ffmpeg/builds/), extract, and add the `bin` folder to your System PATH.
*   **macOS:** `brew install ffmpeg`
*   **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg`

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/media-target-compressor.git
    cd media-target-compressor
    ```

2.  Install the Python requirements:
    ```bash
    pip install Pillow
    ```

## Usage

Basic syntax:
```bash
python compress.py [INPUT_FILE] [TARGET_SIZE]