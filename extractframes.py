import re
import json
import argparse
import sys

def extract_frames_robust(code_text):
    """
    Most robust frame extraction - finds the frames array and parses it manually
    """
    # Find the frames array definition
    lines = code_text.split('\n')
    in_frames_array = False
    frames = []
    current_frame = []
    brace_depth = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Look for the start of frames array
        if 'frames[][]' in stripped or ('frames' in stripped and '[][' in stripped):
            if '{' in stripped:
                in_frames_array = True
                brace_depth = 1
                # Extract starting brace content
                after_brace = stripped.split('{', 1)[1]
                if '}' in after_brace:
                    # Single line frame
                    frame_content = after_brace.split('}', 1)[0]
                    numbers = extract_numbers(frame_content)
                    frames.append(numbers)
                    in_frames_array = False
                    brace_depth = 0
                else:
                    current_frame = extract_numbers(after_brace)
            continue
        
        if in_frames_array:
            if '{' in stripped:
                brace_depth += stripped.count('{')
                # New frame starting
                after_brace = stripped.split('{', 1)[1]
                current_frame = extract_numbers(after_brace)
            elif '}' in stripped:
                brace_depth -= stripped.count('}')
                # Frame ending or array ending
                before_brace = stripped.split('}', 1)[0]
                current_frame.extend(extract_numbers(before_brace))
                if current_frame:
                    frames.append(current_frame)
                    current_frame = []
                if brace_depth <= 0:
                    in_frames_array = False
            else:
                # Regular line in frame array
                current_frame.extend(extract_numbers(stripped))
    
    return frames

def extract_numbers(text):
    """Extract all numbers from text"""
    numbers = []
    # Remove comments
    text = re.sub(r'//.*', '', text)
    # Find all sequences of digits
    number_matches = re.findall(r'\b\d+\b', text)
    for match in number_matches:
        numbers.append(int(match))
    return numbers

def brute_force_extract(code_text):
    """
    Brute force extraction - find everything that looks like frame data
    """
    # Look for the characteristic pattern of frame data
    # Multiple lines with { followed by numbers and commas
    frames = []
    
    # Find all sections that look like frame data
    frame_sections = re.findall(r'\{[^}]*\}', code_text)
    
    for section in frame_sections:
        # Only process sections that have the right pattern (lots of numbers)
        numbers = extract_numbers(section)
        if len(numbers) >= 16:  # Reasonable minimum for a frame
            frames.append(numbers)
    
    return frames

def main():
    parser = argparse.ArgumentParser(description='Extract SSD1306 frame data from Arduino code')
    parser.add_argument('input', help='Input Arduino C++ file')
    parser.add_argument('-o', '--output', help='Output JSON file', default='frames.json')
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input, 'r') as f:
            code_text = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    print("Extracting frame data from code...")
    
    # Try multiple extraction methods
    frames = []
    
    # Method 1: Find the frames array specifically
    frame_match = re.search(r'frames\s*\[\s*\]\s*\[\s*\d*\s*\]\s*=\s*\{(.*?)\};', code_text, re.DOTALL)
    if frame_match:
        frames_content = frame_match.group(1)
        # Extract individual frames
        frame_blocks = re.findall(r'\{(.*?)\}', frames_content, re.DOTALL)
        for block in frame_blocks:
            numbers = extract_numbers(block)
            if numbers:
                frames.append(numbers)
    
    # Method 2: Brute force if first method didn't work
    if not frames:
        frames = brute_force_extract(code_text)
    
    # Extract other parameters
    delay_match = re.search(r'FRAME_DELAY\s*\(\s*(\d+)\s*\)', code_text)
    frame_delay = int(delay_match.group(1)) if delay_match else 100
    
    width_match = re.search(r'FRAME_WIDTH\s*\(\s*(\d+)\s*\)', code_text)
    height_match = re.search(r'FRAME_HEIGHT\s*\(\s*(\d+)\s*\)', code_text)
    width = int(width_match.group(1)) if width_match else 32
    height = int(height_match.group(1)) if height_match else 32
    
    print(f"Found {len(frames)} frames")
    print(f"Frame delay: {frame_delay}ms")
    print(f"Frame dimensions: {width}x{height}")
    
    if frames:
        # Create output
        output = {
            "metadata": {
                "frame_delay": frame_delay,
                "frame_width": width,
                "frame_height": height,
                "frame_count": len(frames)
            },
            "frames": [{"data": frame, "delay": frame_delay} for frame in frames]
        }
        
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"JSON output saved to {args.output}")
        print(f"First frame sample: {frames[0][:10]}...")
    else:
        print("ERROR: No frames found!")
        print("Trying debug mode...")
        
        # Debug: show what we found
        frame_arrays = re.findall(r'\{[^}]+\}', code_text)
        print(f"Found {len(frame_arrays)} potential frame arrays")
        for i, arr in enumerate(frame_arrays[:3]):
            print(f"Array {i}: {arr[:100]}...")

if __name__ == "__main__":
    main()