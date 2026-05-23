#!/usr/bin/env python3
"""Quick test to verify dataset shape before training."""

from dataset import get_datasets, CLASS_NAMES

print("Testing dataset pipeline...")
train_ds, val_ds, test_ds, X_test, y_test, X_train, y_train = get_datasets('../3D_EUS_PAF_v1_Images', batch_size=16)

print("\n✓ Dataset created successfully!")
print(f"✓ Train dataset: {train_ds}")
print(f"✓ Val dataset: {val_ds}")
print(f"✓ Test dataset: {test_ds}")

print("\nSampling one batch from training set...")
for x_batch, y_batch in train_ds.take(1):
    print(f"✓ Batch shape: {x_batch.shape}")
    print(f"✓ Labels shape: {y_batch.shape}")
    print(f"✓ X dtype: {x_batch.dtype}")
    print(f"✓ Y dtype: {y_batch.dtype}")
    print(f"✓ X range: [{x_batch.numpy().min():.3f}, {x_batch.numpy().max():.3f}]")

print("\n✓ Dataset test PASSED - ready for training!")
