#!/usr/bin/python3
import ctypes
from ctypes import c_void_p, c_uint16, c_bool, POINTER
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Load precompiled shared library
lib = ctypes.CDLL("../../drivers/usermode-sdk/build/output/x86/librpusbdisp-drv.so")

# Typedefs from c_interface.h
RoboPeakUsbDisplayDeviceRef = c_void_p
RoboPeakUsbDisplayBitOperationCopy = 0  # enum value for copy operation

lib.RoboPeakUsbDisplayEnable.argtypes = [RoboPeakUsbDisplayDeviceRef]
lib.RoboPeakUsbDisplayEnable.restype = ctypes.c_int

lib.RoboPeakUsbDisplayBitblt.argtypes = [
    RoboPeakUsbDisplayDeviceRef,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int,
    POINTER(c_uint16)
]
lib.RoboPeakUsbDisplayBitblt.restype = ctypes.c_int

lib.RoboPeakUsbDisplayDisposeDevice.argtypes = [RoboPeakUsbDisplayDeviceRef]
lib.RoboPeakUsbDisplayDisposeDevice.restype = ctypes.c_int

# Allocate device pointer
device = RoboPeakUsbDisplayDeviceRef()
if lib.RoboPeakUsbDisplayOpenFirstDevice(ctypes.byref(device)) != 0 or not device:
    raise RuntimeError("No display found")

# Enable display
if lib.RoboPeakUsbDisplayEnable(device) != 0:
    lib.RoboPeakUsbDisplayDisposeDevice(device)
    raise RuntimeError("Failed to enable display")

# Now display is ready to renders something
width, height = 320, 240
img = Image.new("RGB", (width, height), color=(0, 0, 0))  # black background
img2 = Image.open("../res/raspberry.png").convert("RGBA") # Basic image
img.paste(img2, (200, 100), img2) # compose
draw = ImageDraw.Draw(img) # draw

# Draw a rectangle
draw.rectangle([100, 100, 160, 160], fill=(255, 0, 0))  # red rectangle

# Draw text
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
draw.text((20, 80), "Hello!", font=font, fill=(0, 255, 0))  # green text

# Convert RGB16 to b5g6r5
def rgb_to_b5g6r5(r, g, b):
    return ((b >> 3) << 11) | ((g >> 2) << 5) | (r >> 3)

pixels = np.array(img, dtype=np.uint16)  # shape (height, width, 3)
r = pixels[:, :, 0] >> 3
g = pixels[:, :, 1] >> 2
b = pixels[:, :, 2] >> 3

framebuffer = ((b << 11) | (g << 5) | r).astype(np.uint16).flatten()

# Send framebuffer to the device
lib.RoboPeakUsbDisplayBitblt(device, 0, 0, width, height, RoboPeakUsbDisplayBitOperationCopy, framebuffer.ctypes.data_as(POINTER(c_uint16)))




