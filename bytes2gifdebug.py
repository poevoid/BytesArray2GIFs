import json
from PIL import Image
import argparse

def debug_frame_conversion(frame_data, width=32, height=32, method=1):
    """
    Debug different conversion methods to find the right one
    """
    print(f"Debugging frame conversion - Method {method}")
    print(f"Frame data: {len(frame_data)} bytes")
    print(f"Expected for {width}x{height}: {width * height // 8} bytes")
    
    img = Image.new('1', (width, height))
    pixels = img.load()
    
    if method == 1:
        # Method 1: Standard SSD1306 - pages of 8 pixels
        pages = height // 8
        for page in range(pages):
            for x in range(width):
                byte_index = page * width + x
                if byte_index < len(frame_data):
                    byte_val = frame_data[byte_index]
                    for bit in range(8):
                        y = page * 8 + bit
                        if y < height:
                            if byte_val & (1 << (7 - bit)):  # MSB at top
                                pixels[x, y] = 1
    
    elif method == 2:
        # Method 2: Reverse bit order (LSB at top)
        pages = height // 8
        for page in range(pages):
            for x in range(width):
                byte_index = page * width + x
                if byte_index < len(frame_data):
                    byte_val = frame_data[byte_index]
                    for bit in range(8):
                        y = page * 8 + bit
                        if y < height:
                            if byte_val & (1 << bit):  # LSB at top
                                pixels[x, y] = 1
    
    elif method == 3:
        # Method 3: Horizontal bytes (unlikely but let's check)
        bytes_per_row = width // 8
        for y in range(height):
            for byte_x in range(bytes_per_row):
                byte_index = y * bytes_per_row + byte_x
                if byte_index < len(frame_data):
                    byte_val = frame_data[byte_index]
                    for bit in range(8):
                        x = byte_x * 8 + bit
                        if x < width:
                            if byte_val & (1 << (7 - bit)):
                                pixels[x, y] = 1
    
    elif method == 4:
        # Method 4: Vertical bytes, little-endian
        bytes_per_column = height // 8
        for x in range(width):
            for byte_y in range(bytes_per_column):
                byte_index = x * bytes_per_column + byte_y
                if byte_index < len(frame_data):
                    byte_val = frame_data[byte_index]
                    for bit in range(8):
                        y = byte_y * 8 + bit
                        if y < height:
                            if byte_val & (1 << bit):
                                pixels[x, y] = 1
    
    elif method == 5:
        # Method 5: Adafruit GFX format - might be different
        # Try treating it as a simple bitmap
        pages = height // 8
        for page in range(pages):
            for x in range(width):
                byte_index = page * width + x
                if byte_index < len(frame_data):
                    byte_val = frame_data[byte_index]
                    # Reverse the entire byte
                    reversed_byte = int('{:08b}'.format(byte_val)[::-1], 2)
                    for bit in range(8):
                        y = page * 8 + bit
                        if y < height:
                            if reversed_byte & (1 << bit):
                                pixels[x, y] = 1
    
    return img

def analyze_frame_data(frame_data, width=32, height=32):
    """
    Analyze the frame data to understand its structure
    """
    print("\n=== Frame Data Analysis ===")
    print(f"Total bytes: {len(frame_data)}")
    print(f"Expected bytes for {width}x{height}: {width * height // 8}")
    
    # Check if it matches expected size
    expected_bytes = width * height // 8
    if len(frame_data) == expected_bytes:
        print("✓ Frame size matches expected")
    else:
        print(f"✗ Frame size mismatch: got {len(frame_data)}, expected {expected_bytes}")
    
    # Analyze byte patterns
    print(f"First 10 bytes: {frame_data[:10]}")
    print(f"Last 10 bytes: {frame_data[-10:]}")
    
    # Count non-zero bytes to see if there's actual data
    non_zero = sum(1 for b in frame_data if b != 0)
    print(f"Non-zero bytes: {non_zero}/{len(frame_data)} ({non_zero/len(frame_data)*100:.1f}%)")
    
    # Check for patterns in the first "page"
    pages = height // 8
    print(f"\nFirst page analysis (0-{width-1} bytes):")
    first_page = frame_data[:width]
    print(f"First page bytes: {first_page}")

def main():
    parser = argparse.ArgumentParser(description='Debug SSD1306 frame conversion')
    parser.add_argument('input', help='Input JSON file with frame data')
    parser.add_argument('--frame', type=int, default=0, help='Frame number to debug (0-based)')
    parser.add_argument('--width', type=int, default=32, help='Frame width')
    parser.add_argument('--height', type=int, default=32, help='Frame height')
    
    args = parser.parse_args()
    
    # Read the JSON file
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    # Extract frames
    if isinstance(data, list):
        frames = data
    elif isinstance(data, dict) and 'frames' in data:
        frames = [f['data'] for f in data['frames']]
    else:
        print("Unknown JSON format")
        return
    
    if args.frame >= len(frames):
        print(f"Frame {args.frame} not available (only {len(frames)} frames)")
        return
    
    frame_data = frames[args.frame]
    
    # Analyze the frame data
    analyze_frame_data(frame_data, args.width, args.height)
    
    # Try all conversion methods
    for method in range(1, 6):
        img = debug_frame_conversion(frame_data, args.width, args.height, method)
        img.save(f'debug_method_{method}.png')
        # Also create scaled version
        img_scaled = img.resize((args.width * 8, args.height * 8), Image.NEAREST)
        img_scaled.save(f'debug_method_{method}_scaled.png')
        print(f"Saved debug_method_{method}.png and scaled version")
    
    print("\nCheck all debug_method_*.png files to see which one looks correct!")

if __name__ == "__main__":
    main()