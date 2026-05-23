import os
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.utils.class_weight import compute_class_weight
from dataset import get_datasets, CLASS_NAMES
from model import build_model

# Enable memory efficiency
tf.config.run_functions_eagerly(False)
try:
    gpus = tf.config.list_physical_devices('GPU')
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
except:
    pass

def plot_history(history, save_path="training_history.png"):
    acc = history.history['accuracy']
    val_acc = history.history['val_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epochs = range(1, len(acc) + 1)

    plt.figure(figsize=(14, 5))

    plt.subplot(1, 2, 1)
    plt.plot(epochs, acc, 'b-o', label='Training accuracy', linewidth=2)
    plt.plot(epochs, val_acc, 'r-o', label='Validation accuracy', linewidth=2)
    plt.title('Training and Validation Accuracy', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(1, 2, 2)
    plt.plot(epochs, loss, 'b-o', label='Training loss', linewidth=2)
    plt.plot(epochs, val_loss, 'r-o', label='Validation loss', linewidth=2)
    plt.title('Training and Validation Loss', fontsize=12, fontweight='bold')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    print(f"Saved training history plot to {save_path}")
    plt.close()

def train():
    image_dir = '../3D_EUS_PAF_v1_Images'
    batch_size = 8
    epochs = 20

    train_ds, val_ds, test_ds, X_test, y_test, X_train, y_train = get_datasets(image_dir, batch_size=batch_size)

    # Compute class weights to handle imbalanced datasets
    classes = np.unique(y_train)
    weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train)
    class_weight_dict = {cls: weight for cls, weight in zip(classes, weights)}
    print(f"Computed class weights: {class_weight_dict}")

    model, base_model = build_model(num_classes=len(CLASS_NAMES), img_size=224)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=['accuracy']
    )

    checkpoint_cb = tf.keras.callbacks.ModelCheckpoint(
        "best_model.keras", save_best_only=True, monitor='val_accuracy', mode='max'
    )
    early_stopping_cb = tf.keras.callbacks.EarlyStopping(
        patience=5, restore_best_weights=True, monitor='val_loss'
    )
    reduce_lr_cb = tf.keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6, verbose=1
    )

    print("\n" + "="*60)
    print("Starting training (Phase 1: Feature Extraction)")
    print("="*60)
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=epochs,
        callbacks=[checkpoint_cb, early_stopping_cb, reduce_lr_cb],
        class_weight=class_weight_dict,
        verbose=1
    )

    plot_history(history, save_path="phase1_history.png")

    print("\n" + "="*60)
    print("Starting training (Phase 2: Fine-tuning)")
    print("="*60)
    base_model.trainable = True
    for layer in base_model.layers[:-20]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(),
        metrics=['accuracy']
    )

    history_finetune = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=15,
        callbacks=[checkpoint_cb, early_stopping_cb, reduce_lr_cb],
        class_weight=class_weight_dict,
        verbose=1
    )

    plot_history(history_finetune, save_path="phase2_history.png")

    print("\n" + "="*60)
    print("Evaluating on test set...")
    print("="*60)
    test_loss, test_acc = model.evaluate(test_ds, verbose=0)
    print(f"Test Accuracy: {test_acc:.4f}")
    print(f"Test Loss: {test_loss:.4f}")

if __name__ == "__main__":
    train()
