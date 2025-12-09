import os
import sys
import subprocess
import argparse
import platform
import math
from PIL import Image

def parse_size(size_str):
    """Parses a size string (e.g., '5MB', '500KB') into bytes."""
    size_str = size_str.strip().upper()
    if size_str.endswith("GB"):
        return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
    elif size_str.endswith("MB"):
        return int(float(size_str[:-2]) * 1024 * 1024)
    elif size_str.endswith("KB"):
        return int(float(size_str[:-2]) * 1024)
    elif size_str.endswith("B"):
        return int(float(size_str[:-1]))
    else:
        return int(size_str)

def get_file_size(path):
    return os.path.getsize(path)

def compress_image(input_path, output_path, target_bytes):
    img = Image.open(input_path)
    
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    min_quality = 5
    quality = 95
    resize_factor = 0.9
    temp_path = output_path + ".temp.jpg"

    while True:
        img.save(temp_path, "JPEG", quality=quality, optimize=True)
        current_size = get_file_size(temp_path)
        print(f"Image Pass | Quality: {quality} | Size: {current_size/1024:.2f} KB")

        if current_size <= target_bytes:
            break
            
        if quality > min_quality:
            quality -= 5
        else:
            width, height = img.size
            new_width = int(width * resize_factor)
            new_height = int(height * resize_factor)
            print(f"Quality lowest. Resizing to {new_width}x{new_height}")
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            quality = 85 

    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(temp_path, output_path)

def get_video_duration(input_path):
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration", 
        "-of", "default=noprint_wrappers=1:nokey=1", input_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting video duration. Is FFmpeg installed? {e}")
        sys.exit(1)

def compress_video(input_path, output_path, target_bytes):
    duration = get_video_duration(input_path)
    
    # --- CORE FIX: SUBTRACT OVERHEAD MARGIN ---
    # We remove 5% from the target size to account for:
    # 1. MP4 Container Overhead (Headers, Muxing info) which is usually 1-2%
    # 2. Bitrate fluctuation (variable bitrate encoding isn't byte-perfect)
    overhead_margin = 0.05 
    usable_bytes = target_bytes * (1 - overhead_margin)
    
    target_total_bitrate = (usable_bytes * 8) / duration
    
    # Default Audio Bitrate
    audio_bitrate = 128 * 1000

    # Dynamic Audio Adjustment
    # If the video is being squeezed very hard, lower audio quality to save space
    if target_total_bitrate < 1000000: # Less than 1MB/s total
        audio_bitrate = 96 * 1000
    if target_total_bitrate < 500000:  # Less than 500kb/s total
        audio_bitrate = 64 * 1000

    video_bitrate = target_total_bitrate - audio_bitrate
    
    if video_bitrate < 1000:
        print("Error: Target size is impossibly small for this video duration.")
        sys.exit(1)

    print(f"Video Duration: {duration:.2f}s")
    print(f"Target Total Size (w/ 5% buffer): {usable_bytes / (1024*1024):.2f} MB")
    print(f"Target Video Bitrate: {int(video_bitrate/1000)}k")
    print(f"Target Audio Bitrate: {int(audio_bitrate/1000)}k")

    devnull = "NUL" if platform.system() == "Windows" else "/dev/null"
    
    # Pass 1
    pass1_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-b:v", str(int(video_bitrate)), "-pass", "1",
        "-f", "mp4", devnull
    ]
    
    # Pass 2
    pass2_cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-b:v", str(int(video_bitrate)), "-pass", "2",
        "-c:a", "aac", "-b:a", str(int(audio_bitrate)),
        output_path
    ]

    print("Running Pass 1 (Analysis)...")
    subprocess.run(pass1_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("Running Pass 2 (Compression)...")
    # We suppress Pass 2 output too, unless you want to see the wall of text
    # Remove stdout=... if you want to see FFmpeg progress
    subprocess.run(pass2_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cleanup logs
    for f in os.listdir("."):
        if f.startswith("ffmpeg2pass"):
            try:
                os.remove(f)
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description="Compress Image or Video to a target file size.")
    parser.add_argument("input", help="Path to input file")
    parser.add_argument("size", help="Target size (e.g., 5MB, 500KB)")
    parser.add_argument("-o", "--output", help="Output file path (optional)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print("Input file not found.")
        sys.exit(1)

    target_bytes = parse_size(args.size)
    current_size = get_file_size(args.input)
    
    print(f"Input: {args.input}")
    print(f"Current Size: {current_size / (1024*1024):.2f} MB")
    print(f"Target Size:  {target_bytes / (1024*1024):.2f} MB")

    if current_size <= target_bytes:
        print("File is already smaller than target size. No action needed.")
        sys.exit(0)

    if args.output:
        output_path = args.output
    else:
        filename, ext = os.path.splitext(args.input)
        output_path = f"{filename}_compressed{ext}"

    ext = os.path.splitext(args.input)[1].lower()
    image_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    video_exts = ['.mp4', '.mov', '.avi', '.mkv', '.flv']

    if ext in image_exts:
        if output_path.lower().endswith(".png"):
            print("Warning: Compressing to PNG is difficult due to lossless nature. Converting to JPG recommended.")
        compress_image(args.input, output_path, target_bytes)
    elif ext in video_exts:
        compress_video(args.input, output_path, target_bytes)
    else:
        print("Unsupported file format.")
        sys.exit(1)

    final_size = get_file_size(output_path)
    print(f"\nDone! Saved to: {output_path}")
    print(f"Final Size: {final_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    main()