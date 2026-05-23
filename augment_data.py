import os
import glob
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from dataset import CLASS_NAMES
import random

def apply_median_filter(img):
    return cv2.medianBlur(img, 5)

def apply_clahe(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl,a,b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def apply_sharpening(img):
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    return cv2.filter2D(img, -1, kernel)

def apply_contrast_enhancement(img):
    alpha = 1.3 # Contrast control
    beta = 10   # Brightness control
    return cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

def apply_random_filter(img):
    filters = [apply_median_filter, apply_clahe, apply_sharpening, apply_contrast_enhancement, lambda x: x]
    chosen_filter = random.choice(filters)
    return chosen_filter(img)


def augment_dataset(target_images=2000):
    input_dir = '../3D_EUS_PAF_v1_Images'
    output_dir = 'augmented_dataset'
    os.makedirs(output_dir, exist_ok=True)

    # Calculate images per class to reach target total
    images_per_class = target_images // len(CLASS_NAMES)
    print(f"Target total images: {target_images}")
    print(f"Images per class: {images_per_class}")
    print(f"Actual total will be: {images_per_class * len(CLASS_NAMES)}\n")

    datagen = ImageDataGenerator(
        rotation_range=40,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest',
        brightness_range=[0.8, 1.2],
        channel_shift_range=20.0
    )

    image_paths = glob.glob(os.path.join(input_dir, '*.[pP][nN][gG]'))

    class_images = {i: [] for i in range(len(CLASS_NAMES))}
    for path in image_paths:
        basename = os.path.basename(path)
        try:
            prefix = basename.split('_')[0]
            label = int(prefix) - 1
            class_images[label].append(path)
        except:
            continue

    total_generated = 0

    for label, paths in class_images.items():
        print(f"Class {CLASS_NAMES[label]} has {len(paths)} original images.")
        if len(paths) == 0:
            continue

        for i, path in enumerate(paths):
            img = cv2.imread(path)
            cv2.imwrite(os.path.join(output_dir, f"{label:02d}_{CLASS_NAMES[label]}_orig_{i}.png"), img)

        images_needed = images_per_class - len(paths)
        if images_needed <= 0:
            print(f"  Skipping augmentation (already have {len(paths)} >= {images_per_class})")
            total_generated += len(paths)
            continue

        print(f"  Generating {images_needed} augmented images for {CLASS_NAMES[label]}...")

        generated = 0
        while generated < images_needed:
            for path in paths:
                if generated >= images_needed:
                    break

                img = cv2.imread(path)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img = img.reshape((1,) + img.shape)

                for batch in datagen.flow(img, batch_size=1):
                    aug_img = batch[0].astype('uint8')
                    aug_img = cv2.cvtColor(aug_img, cv2.COLOR_RGB2BGR)
                    
                    # Apply one of the requested advanced filters randomly
                    aug_img = apply_random_filter(aug_img)
                    
                    out_path = os.path.join(output_dir, f"{label:02d}_{CLASS_NAMES[label]}_aug_{generated}.png")
                    cv2.imwrite(out_path, aug_img)
                    generated += 1
                    break

        total_generated += len(paths) + images_needed

    print(f"\n{'='*60}")
    print(f"Data augmentation complete!")
    print(f"Total images generated: {total_generated}")
    print(f"Dataset saved to: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    augment_dataset(target_images=2000)
