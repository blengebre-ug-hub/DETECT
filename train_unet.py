import tensorflow as tf
from dataset import get_segmentation_datasets, IMG_SIZE
from model import build_unet
import matplotlib.pyplot as plt

# Enable memory efficiency
tf.config.run_functions_eagerly(False)
try:
    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
except:
    pass

def plot_unet_history(history, save_path="unet_training_history.png"):
    acc = history.history.get('accuracy', [])
    val_acc = history.history.get('val_accuracy', [])
    loss = history.history.get('loss', [])
    val_loss = history.history.get('val_loss', [])

    epochs = range(1, len(loss) + 1)

    plt.figure(figsize=(14, 5))
    if acc and val_acc:
        plt.subplot(1, 2, 1)
        plt.plot(epochs, acc, 'b-o', label='Training accuracy')
        plt.plot(epochs, val_acc, 'r-o', label='Validation accuracy')
        plt.title('Training and Validation Accuracy')
        plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(epochs, loss, 'b-o', label='Training loss')
    plt.plot(epochs, val_loss, 'r-o', label='Validation loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.savefig(save_path)
    print(f"Saved training history to {save_path}")

def train():
    image_dir = '../3D_EUS_PAF_v1_Images'
    mask_dir = '../3D_EUS_PAF_v1_Masks'
    batch_size = 4
    epochs = 15

    train_ds, val_ds = get_segmentation_datasets(image_dir, mask_dir, batch_size=batch_size)

    model = build_unet(img_size=224)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint("segmentation_model.keras", save_best_only=True, monitor="val_loss", mode="min"),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6, verbose=1),
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)
    ]

    print("Starting U-Net Training on Pseudo-Masks...")
    history = model.fit(train_ds, validation_data=val_ds, epochs=epochs, callbacks=callbacks, verbose=1)
    
    plot_unet_history(history)
    print("U-Net training complete. Model saved as segmentation_model.keras")

if __name__ == "__main__":
    train()
