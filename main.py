from geotiff import GeoTiff, geotiff
import os
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

DATA_DIR = 'data-astgtm'
OUTPUT_RES = (5120, 3200)  # (5020, 2824) printable area
PIXEL_SIZE = 38.25  # microns
Z_LAYER_SIZE = 100  # microns
DATA_RESOLTION_XY_deg = 1 / 3600  # 1 arc second
DATA_RESOLUTION_XY = 30  # meters
DATA_RESOLUTION_Z = 1  # meters
PRINTABLE_AREA = (5020, 2824)
PRINT_MARGIN_FACTOR = 0.85
BASE_LAYERS = 50
Z_HEIGHT_MULT = 1.0
LAYER_REPEATS = 1
LAYER_SKIPS = 1
OUTPUT_DIR = 'out-sf'
NORTH_SOUTH_EXTENT = 0.3  # degrees latitude

center = (37.71580036603404, -122.39505208180861) # SF city
# center = (37.809638612919, -122.36600653263841) # SF bay
# center = (39.089915551656375, -120.03122040686522)  # LT
EAST_WEST_EXTENT = 16 * NORTH_SOUTH_EXTENT / 9
region_TL = (center[1] + NORTH_SOUTH_EXTENT / 2, center[0] - EAST_WEST_EXTENT / 2)
region_BR = (center[1] - NORTH_SOUTH_EXTENT / 2, center[0] + EAST_WEST_EXTENT / 2)
region_box = [region_TL, region_BR]
print(region_box)

def crop_region_box(int_box, gt):
    gt_extent = gt.tif_shape
    int_box = [
        (np.clip(int_box[0][0], 0, gt_extent[0]), np.clip(int_box[0][1], 0, gt_extent[1])),
        (np.clip(int_box[1][0], 0, gt_extent[0]), np.clip(int_box[1][1], 0, gt_extent[1]))
    ]

os.makedirs(OUTPUT_DIR, exist_ok=True)
fnames = os.listdir(DATA_DIR)
for fname in fnames:
    if 'dem.tif' not in fname:
        continue
    gt = GeoTiff(os.path.join(DATA_DIR, fname))
    # print()
    print(gt.tif_bBox)
    # 37.827043605106915, -122.5408915954636
    # 37.649969830367006, -122.34176881067887
    try:
        tif_shape = gt.tif_shape
        alt_array = gt.read()
        ((x_min, y_min), (x_max, y_max)) = gt.get_int_box(region_box)
        x_min = np.clip(x_min, 0, tif_shape[1])
        x_max = np.clip(x_max, 0, tif_shape[1])
        y_min = np.clip(y_min, 0, tif_shape[0])
        y_max = np.clip(y_max, 0, tif_shape[0])
        z_data = np.array(alt_array[y_min:y_max, x_min:x_max]).astype(float)
        # print(int_box)
    except geotiff.BoundaryNotInTifError:
        print('bnite')
        continue
    if z_data.shape[0] <= 0 or z_data.shape[1] <= 0:
        print('shape 0')
        continue
    
    z_data = np.transpose(z_data)
    plt.imshow(z_data)
    plt.show()
    base_size = z_data.shape[::-1]
    base_size_meters = tuple([base_size[i] * DATA_RESOLUTION_XY for i in range(len(base_size))])
    resize_factor = min(
        [PRINTABLE_AREA[i] * PRINT_MARGIN_FACTOR / base_size[i] for i in range(len(PRINTABLE_AREA))]
    )
    z_resize_factor = resize_factor * (DATA_RESOLUTION_Z * Z_LAYER_SIZE) / (DATA_RESOLUTION_XY * PIXEL_SIZE)
    z_data *= z_resize_factor * Z_HEIGHT_MULT
    resized_size = int(base_size[0] * resize_factor), int(base_size[1] * resize_factor)
    print(resized_size)
    fill_layer = Image.new('L', resized_size, 'white')
    full_fill_img = Image.new('L', OUTPUT_RES)
    full_fill_img.paste(
        fill_layer,
        ((OUTPUT_RES[0] - resized_size[0]) // 2, (OUTPUT_RES[1] - resized_size[1]) // 2)
    )
    for fill_idx in range(BASE_LAYERS):
        full_fill_img.save(f'{OUTPUT_DIR}/{fill_idx}.png')
    start_z = int(np.min(z_data))
    stop_z = int(np.max(z_data))
    total_z_count = (stop_z - start_z) // LAYER_SKIPS
    for z_idx, z in enumerate(range(start_z, stop_z + 1, LAYER_SKIPS)):
        print(f'{z_idx} / {total_z_count}')
        z_slice = z_data >= z
        slice_img = Image.fromarray(z_slice).convert('L')
        slice_img_resize = slice_img.resize(resized_size, Image.Resampling.NEAREST)
        output_img = Image.new('L', OUTPUT_RES)
        output_img.paste(
            slice_img_resize,
            ((OUTPUT_RES[0] - resized_size[0]) // 2, (OUTPUT_RES[1] - resized_size[1]) // 2)
        )
        output_slice_idx = BASE_LAYERS + z_idx * LAYER_REPEATS
        for repeat_idx in range(LAYER_REPEATS):
            output_img.save(f'{OUTPUT_DIR}/{output_slice_idx}.png')
            output_slice_idx += 1

