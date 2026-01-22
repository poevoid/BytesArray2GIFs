import argparse
import json
import os
from PIL import Image, ImageSequence
import sys

def ssd1306_bytes_to_image_horizontal(frame_data, width=32, height=32):
    """
    Convert SSD1306 byte array to PIL Image using horizontal byte layout (Method 3)
    Each byte represents 8 horizontal pixels, MSB first
    """
    img = Image.new('1', (width, height))
    pixels = img.load()
    
    bytes_per_row = width // 8
    
    for y in range(height):
        for byte_x in range(bytes_per_row):
            byte_index = y * bytes_per_row + byte_x
            if byte_index < len(frame_data):
                byte_val = frame_data[byte_index]
                # Extract 8 horizontal pixels from the byte (MSB first)
                for bit in range(8):
                    x = byte_x * 8 + (7 - bit)  # MSB is leftmost pixel
                    if x < width:
                        if byte_val & (1 << bit):
                            pixels[x, y] = 1  # White pixel
                        else:
                            pixels[x, y] = 0  # Black pixel
    
    return img

def parse_wokwi_data(wokwi_data):
    """
    Parse Wokwi animator data which contains frames and timing information
    """
    frames = []
    metadata = {}
    
    if isinstance(wokwi_data, list):
        # Simple case: just an array of frame data
        for frame_data in wokwi_data:
            if isinstance(frame_data, list):
                frames.append({
                    'data': frame_data,
                    'delay': 100  # default delay
                })
    elif isinstance(wokwi_data, dict):
        # Complex case: dictionary with frames and metadata
        if 'frames' in wokwi_data:
            for frame_info in wokwi_data['frames']:
                if isinstance(frame_info, dict) and 'data' in frame_info:
                    frames.append({
                        'data': frame_info['data'],
                        'delay': frame_info.get('delay', 100)
                    })
                elif isinstance(frame_info, list):
                    frames.append({
                        'data': frame_info,
                        'delay': 100
                    })
        # Also check if we have metadata for display size
        if 'metadata' in wokwi_data:
            metadata = wokwi_data['metadata']
    
    return frames, metadata

def create_gif_from_frames(frames, output_path, width=128, height=64, frame_width=32, frame_height=32, x_offset=48, y_offset=16, loop=0):
    """
    Create GIF from frames with proper timing using horizontal byte layout
    """
    if not frames:
        print("No frames to process!")
        return
    
    pil_frames = []
    
    print(f"Processing {len(frames)} frames...")
    print(f"Frame size: {frame_width}x{frame_height}")
    print(f"Position on display: ({x_offset}, {y_offset})")
    
    for i, frame in enumerate(frames):
        print(f"Processing frame {i+1}/{len(frames)}")
        
        # Create full display image
        display_img = Image.new('1', (width, height))
        
        # Convert the frame data using horizontal layout
        frame_img = ssd1306_bytes_to_image_horizontal(frame['data'], frame_width, frame_height)
        
        # Paste the frame onto the display at the correct position
        display_img.paste(frame_img, (x_offset, y_offset))
        
        # Convert to 'P' mode for GIF with proper palette
        img_rgb = display_img.convert('L')  # Convert to grayscale first
        img_p = img_rgb.convert('P', palette=Image.ADAPTIVE, colors=2)
        
        # Set palette for black and white
        palette = [0, 0, 0, 255, 255, 255]  # Black, White
        img_p.putpalette(palette)
        
        pil_frames.append(img_p)
    
    # Save as GIF
    if pil_frames:
        print(f"Saving GIF to {output_path}...")
        pil_frames[0].save(
            output_path,
            save_all=True,
            append_images=pil_frames[1:],
            duration=[frame['delay'] for frame in frames],
            loop=loop,
            disposal=2  # Restore to background
        )
        print("GIF created successfully!")
    else:
        print("No valid frames to save!")

def preview_single_frame(frame_data, output_path, width=128, height=64, frame_width=32, frame_height=32, x_offset=48, y_offset=16):
    """
    Preview a single frame to verify the conversion
    """
    print(f"Previewing frame - data length: {len(frame_data)} bytes")
    
    # Create the frame
    display_img = Image.new('1', (width, height))
    frame_img = ssd1306_bytes_to_image_horizontal(frame_data, frame_width, frame_height)
    display_img.paste(frame_img, (x_offset, y_offset))
    
    # Save original and scaled versions
    display_img.save(output_path)
    print(f"Preview saved as {output_path}")
    
    # Create scaled version for better viewing
    scaled_img = display_img.resize((width * 4, height * 4), Image.NEAREST)
    scaled_path = output_path.replace('.png', '_scaled.png')
    scaled_img.save(scaled_path)
    print(f"Scaled preview saved as {scaled_path}")

def main():
    parser = argparse.ArgumentParser(description='Convert SSD1306 byte arrays to GIF using horizontal byte layout')
    parser.add_argument('input', help='Input JSON file with frame data')
    parser.add_argument('-o', '--output', help='Output GIF file', default='animation.gif')
    parser.add_argument('--width', type=int, default=128, help='Display width (default: 128)')
    parser.add_argument('--height', type=int, default=64, help='Display height (default: 64)')
    parser.add_argument('--frame-width', type=int, default=32, help='Actual frame width (default: 32)')
    parser.add_argument('--frame-height', type=int, default=32, help='Actual frame height (default: 32)')
    parser.add_argument('--x-offset', type=int, default=48, help='X offset for frame (default: 48)')
    parser.add_argument('--y-offset', type=int, default=16, help='Y offset for frame (default: 16)')
    parser.add_argument('--loop', type=int, default=0, help='Loop count (0=infinite, default: 0)')
    parser.add_argument('--scale', type=int, default=4, help='Scale factor for output (default: 4)')
    parser.add_argument('--preview', type=int, help='Preview frame number (0-based)')
    
    args = parser.parse_args()
    
    # Read input file
    try:
        with open(args.input, 'r') as f:
            wokwi_data = json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Parse frames from Wokwi data
    frames, metadata = parse_wokwi_data(wokwi_data)
    
    if not frames:
        print("No valid frame data found in input file!")
        sys.exit(1)
    
    # Use metadata if available
    if metadata:
        args.width = metadata.get('display_width', args.width)
        args.height = metadata.get('display_height', args.height)
        args.frame_width = metadata.get('frame_width', args.frame_width)
        args.frame_height = metadata.get('frame_height', args.frame_height)
        frame_delay = metadata.get('frame_delay', 100)
        # Update frame delays if they weren't already set
        for frame in frames:
            if frame.get('delay', 100) == 100:
                frame['delay'] = frame_delay
    
    print(f"Processing {len(frames)} frames")
    print(f"Display: {args.width}x{args.height}")
    print(f"Frame: {args.frame_width}x{args.frame_height} at ({args.x_offset}, {args.y_offset})")
    
    # Preview a single frame if requested
    if args.preview is not None and 0 <= args.preview < len(frames):
        print(f"Previewing frame {args.preview}")
        preview_single_frame(
            frames[args.preview]['data'],
            f'preview_frame_{args.preview}.png',
            args.width, args.height,
            args.frame_width, args.frame_height,
            args.x_offset, args.y_offset
        )
        return
    
    # Create temporary GIF
    temp_output = "temp_" + args.output
    create_gif_from_frames(
        frames, temp_output, 
        args.width, args.height,
        args.frame_width, args.frame_height,
        args.x_offset, args.y_offset,
        args.loop
    )
    
    # Scale the GIF if requested
    if args.scale > 1:
        print(f"Scaling GIF by factor {args.scale}...")
        try:
            with Image.open(temp_output) as img:
                # Get all frames
                scaled_frames = []
                durations = []
                
                for frame in ImageSequence.Iterator(img):
                    # Scale the frame
                    new_size = (frame.width * args.scale, frame.height * args.scale)
                    scaled_frame = frame.resize(new_size, Image.NEAREST)
                    scaled_frames.append(scaled_frame)
                    
                    # Get duration
                    if 'duration' in frame.info:
                        durations.append(frame.info['duration'])
                    else:
                        durations.append(frames[0]['delay'])  # Use first frame's delay
                
                # Save scaled GIF
                scaled_frames[0].save(
                    args.output,
                    save_all=True,
                    append_images=scaled_frames[1:],
                    duration=durations,
                    loop=args.loop,
                    disposal=2
                )
            # Remove temp file
            os.remove(temp_output)
            print(f"Scaled GIF saved as {args.output}")
        except Exception as e:
            print(f"Error scaling GIF: {e}")
            # If scaling fails, just rename the temp file
            os.rename(temp_output, args.output)
    else:
        os.rename(temp_output, args.output)

if __name__ == "__main__":
    main()
