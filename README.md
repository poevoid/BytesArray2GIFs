# BytesArray2GIFs
complimentary scripts that make gifs from arduino byte array animations, cuz I wanted gifs of some of the wokwi animations.

### First, make sure you have Pillow installed via pip:
```python -m pip install pillow```

## Scripts Overview

### 1. Frame Extractor (extract_frames.py)

Extracts frame data from Arduino C++ code and creates JSON format for the GIF converter.

Usage:

* Basic extraction:
 `python extract_frames.py animation.ino -o frames.json`

* With custom frame delay:
 `python extract_frames.py animation.ino -o frames.json --delay 50`

* Simple array format (no metadata):
 `python extract_frames.py animation.ino -o frames.json --format simple`

* Input: Arduino .ino file with frame arrays

* Output: JSON file with frame data and timing information


### 2. GIF Converter (bytes2gif.py)

Converts the extracted frame data into an animated GIF.

Usage:

* Basic conversion
 `python bytes2gif.py frames.json -o animation.gif`

* With custom positioning (from drawBitmap parameters)
 `python bytes2gif.py frames.json -o animation.gif --frame-width 32 --frame-height 32 --x-offset 48 --y-offset 16`

* Scaled output with infinite loop
 `python bytes2gif.py frames.json -o animation.gif --scale 4 --loop 0`

* Preview a single frame first
 `python bytes2gif.py frames.json --preview 0`

#### Parameters:
* `--width, --height`: Display dimensions (default: 128x64)

* `--frame-width, --frame-height`: Actual animation size

* `--x-offset, --y-offset`: Position on display (from drawBitmap())

* `--scale`: Output scaling factor

* `--loop`: Loop count (0 = infinite)

* `--preview`: Preview specific frame number


### 3. Debug Tool (bytes2gifdebug.py)
Helps troubleshoot conversion issues by testing different byte layout methods on frame 0.

Usage:

`python bytes2gifdebug.py frames.json --frame 0 --width YOURGIFWIDTH --height YOURGIFHEIGHT`

This creates debug_method_1.png through debug_method_5.png, showing different conversion attempts.
