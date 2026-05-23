import os
import glob
import cv2
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

IMG_SIZE = 224

def apply_noise_reduction(image):
    """Apply bilateral filtering to reduce ultrasound speckle noise."""
    image = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
    return image

CLASS_NAMES = [
    "Inter_Sph_Fistula",
    "Inter_Sph_Abscess",
    "Trans_Sph_Fistula",
    "Supra_Sph_Fistla",
    "Pre_Anal_Abscess",
    "Ischiorectal_Abscess",
    "Supra_Levator_Abscess"
]

def load_data(image_dir):
    image_paths = glob.glob(os.path.join(image_dir, '*.[pP][nN][gG]'))
    paths = []
    labels = []

    for path in image_paths:
        basename = os.path.basename(path)
        try:
            prefix = int(basename.split('_')[0])
            if prefix >= 1 and 'augmented_dataset' not in image_dir:
                label = prefix - 1
            else:
                label = prefix
        except Exception as e:
            print(f"Skipping {basename}: {e}")
            continue

        paths.append(path)
        labels.append(label)

    return paths, labels

def get_datasets(image_dir, batch_size=16):
    if os.path.exists('augmented_dataset') and len(os.listdir('augmented_dataset')) > 500:
        print("Using augmented_dataset for training!")
        image_dir = 'augmented_dataset'
        
    paths, y = load_data(image_dir)
    print(f"Total images found: {len(paths)}")
    
    counts = np.bincount(y)
    print(f"Class distribution: {counts}")
    
    try:
        paths_train, paths_temp, y_train, y_temp = train_test_split(paths, y, test_size=0.3, random_state=42, stratify=y)
        paths_val, paths_test, y_val, y_test = train_test_split(paths_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    except ValueError:
        print("Stratified split failed (likely due to small class counts), falling back to random split.")
        paths_train, paths_temp, y_train, y_temp = train_test_split(paths, y, test_size=0.3, random_state=42)
        paths_val, paths_test, y_val, y_test = train_test_split(paths_temp, y_temp, test_size=0.5, random_state=42)
    
    print(f"Train size: {len(paths_train)}, Val size: {len(paths_val)}, Test size: {len(paths_test)}")
    
    def py_apply_noise_reduction(img):
        img_np = img.numpy()
        if img_np.dtype != np.uint8:
            img_np = img_np.astype(np.uint8)
        img_np = apply_noise_reduction(img_np)
        return img_np.astype(np.float32)

    def load_and_preprocess_image(path, label):
        img = tf.io.read_file(path)
        # Use decode_image to support both png and jpeg
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
        
        # Apply noise reduction using py_function
        img = tf.py_function(func=py_apply_noise_reduction, inp=[img], Tout=tf.float32)
        img.set_shape([IMG_SIZE, IMG_SIZE, 3])
        return img, label

    train_ds = tf.data.Dataset.from_tensor_slices((paths_train, y_train))
    val_ds = tf.data.Dataset.from_tensor_slices((paths_val, y_val))
    test_ds = tf.data.Dataset.from_tensor_slices((paths_test, y_test))
    
    AUTOTUNE = tf.data.AUTOTUNE

    # Preprocess datasets
    train_ds = train_ds.map(load_and_preprocess_image, num_parallel_calls=AUTOTUNE)
    val_ds = val_ds.map(load_and_preprocess_image, num_parallel_calls=AUTOTUNE)
    test_ds = test_ds.map(load_and_preprocess_image, num_parallel_calls=AUTOTUNE)

    def augment_only(x, y):
        x = tf.image.random_flip_left_right(x)
        x = tf.image.random_flip_up_down(x)
        x = tf.image.random_brightness(x, 0.2)
        x = tf.image.random_contrast(x, 0.8, 1.2)
        x = tf.image.random_hue(x, 0.1)
        x = tf.image.random_saturation(x, 0.8, 1.2)
        return x, y

    train_ds = train_ds.shuffle(1000).map(
        augment_only,
        num_parallel_calls=AUTOTUNE
    ).batch(batch_size).prefetch(AUTOTUNE)

    val_ds = val_ds.batch(batch_size).prefetch(AUTOTUNE)
    test_ds = test_ds.batch(batch_size).prefetch(AUTOTUNE)
    
    return train_ds, val_ds, test_ds, paths_test, y_test, paths_train, y_train

def get_segmentation_datasets(image_dir, mask_dir, batch_size=16):
    import os
    import glob
    from sklearn.model_selection import train_test_split
    
    image_paths = sorted(glob.glob(os.path.join(image_dir, '*.[pP][nN][gG]')))
    mask_paths = sorted(glob.glob(os.path.join(mask_dir, '*.[pP][nN][gG]')))
    
    # Ensure they match
    assert len(image_paths) == len(mask_paths) and len(image_paths) > 0, "Image and mask counts must match!"
    
    paths_train, paths_val, m_train, m_val = train_test_split(image_paths, mask_paths, test_size=0.2, random_state=42)
    
    def py_apply_noise_reduction(img):
        img_np = img.numpy()
        if img_np.dtype != np.uint8:
            img_np = img_np.astype(np.uint8)
        img_np = apply_noise_reduction(img_np)
        return img_np.astype(np.float32)

    def load_and_preprocess(img_path, mask_path):
        # Load Image
        img = tf.io.read_file(img_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, [IMG_SIZE, IMG_SIZE])
        img = tf.py_function(func=py_apply_noise_reduction, inp=[img], Tout=tf.float32)
        img.set_shape([IMG_SIZE, IMG_SIZE, 3])
        
        # Load Mask
        mask = tf.io.read_file(mask_path)
        mask = tf.image.decode_image(mask, channels=1, expand_animations=False)
        mask = tf.image.resize(mask, [IMG_SIZE, IMG_SIZE])
        mask = mask / 255.0 # Normalize to [0, 1]
        mask.set_shape([IMG_SIZE, IMG_SIZE, 1])
        
        return img, mask

    AUTOTUNE = tf.data.AUTOTUNE
    
    train_ds = tf.data.Dataset.from_tensor_slices((paths_train, m_train))
    train_ds = train_ds.map(load_and_preprocess, num_parallel_calls=AUTOTUNE)
    
    # Simple augmentation for segmentation (flips must apply to both img and mask)
    def augment(img, mask):
        if tf.random.uniform(()) > 0.5:
            img = tf.image.flip_left_right(img)
            mask = tf.image.flip_left_right(mask)
        if tf.random.uniform(()) > 0.5:
            img = tf.image.flip_up_down(img)
            mask = tf.image.flip_up_down(mask)
        img = tf.image.random_brightness(img, 0.2)
        return img, mask
        
    train_ds = train_ds.shuffle(1000).map(augment, num_parallel_calls=AUTOTUNE).batch(batch_size).prefetch(AUTOTUNE)
    
    val_ds = tf.data.Dataset.from_tensor_slices((paths_val, m_val))
    val_ds = val_ds.map(load_and_preprocess, num_parallel_calls=AUTOTUNE).batch(batch_size).prefetch(AUTOTUNE)
    
    return train_ds, val_ds
