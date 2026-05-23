#!/usr/bin/env python3
"""
Unified Pipeline Runner for 3D EUS AI System
Automates: augmentation → segmentation training → classification training → evaluation
"""

import os
import sys
import time
import argparse
from datetime import datetime

def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def run_command(script_name, description):
    """Run a Python script and handle errors."""
    print(f"\n→ {description}...")
    start_time = time.time()

    try:
        exec(open(script_name).read())
        elapsed = time.time() - start_time
        print(f"✓ {description} completed in {elapsed:.1f}s")
        return True
    except Exception as e:
        print(f"✗ Error in {description}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run full 3D EUS AI pipeline")
    parser.add_argument('--skip-augment', action='store_true', help='Skip data augmentation')
    parser.add_argument('--skip-seg', action='store_true', help='Skip segmentation training')
    parser.add_argument('--skip-clf', action='store_true', help='Skip classification training')
    parser.add_argument('--eval-only', action='store_true', help='Run evaluation only')
    parser.add_argument('--quick', action='store_true', help='Quick run (reduced epochs for testing)')

    args = parser.parse_args()

    print_section("3D EUS AI SYSTEM - FULL PIPELINE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    pipeline_log = []
    total_start = time.time()

    # ========== STEP 1: DATA AUGMENTATION ==========
    if not args.skip_augment and not args.eval_only:
        print_section("STEP 1: DATA AUGMENTATION (2000 images)")
        print("Generating augmented dataset with:")
        print("  • Rotation, shift, zoom, shear")
        print("  • Median filtering, CLAHE, sharpening")
        print("  • Brightness & contrast enhancement")
        print("  • Target: 2000 balanced images (286/class)")

        success = run_command('augment_data.py', 'Data augmentation')
        pipeline_log.append(('Data Augmentation', success))
    else:
        print_section("STEP 1: SKIPPED (Data Augmentation)")

    # ========== STEP 2: SEGMENTATION ==========
    if not args.skip_seg and not args.eval_only:
        print_section("STEP 2: SEGMENTATION MODEL (U-Net)")
        print("Training U-Net for anomaly segmentation:")
        print("  • Architecture: Encoder-Decoder with skip connections")
        print("  • Input: 224×224 ultrasound images")
        print("  • Output: Binary segmentation masks")

        success = run_command('train_unet.py', 'U-Net training')
        pipeline_log.append(('U-Net Training', success))

        print("\nEvaluating segmentation...")
        success = run_command('evaluate_segmentation.py', 'Segmentation evaluation')
        pipeline_log.append(('Segmentation Evaluation', success))
    else:
        print_section("STEP 2: SKIPPED (Segmentation)")

    # ========== STEP 3: CLASSIFICATION ==========
    if not args.skip_clf and not args.eval_only:
        print_section("STEP 3: CLASSIFICATION MODEL (EfficientNetB3)")
        print("Training EfficientNetB3 for 7-class classification:")
        print("  • Phase 1: Feature extraction (frozen backbone)")
        print("  • Phase 2: Fine-tuning (unfrozen top layers)")
        print("  • Classes:")
        from dataset import CLASS_NAMES
        for i, cls in enumerate(CLASS_NAMES, 1):
            print(f"    {i}. {cls}")

        success = run_command('train.py', 'Classification training')
        pipeline_log.append(('Classification Training', success))
    else:
        print_section("STEP 3: SKIPPED (Classification)")

    # ========== STEP 4: EVALUATION ==========
    print_section("STEP 4: COMPREHENSIVE EVALUATION")
    print("Generating evaluation metrics and visualizations:")
    print("  • Confusion matrix & ROC curves")
    print("  • Precision, recall, F1-score, AUC-ROC")
    print("  • Grad-CAM explainability visualizations")

    success = run_command('evaluate.py', 'Classification evaluation')
    pipeline_log.append(('Classification Evaluation', success))

    # ========== STEP 5: EXPLAINABILITY ==========
    print_section("STEP 5: MODEL EXPLAINABILITY")
    print("Generating Grad-CAM visualizations...")

    success = run_command('explainability.py', 'Grad-CAM generation')
    pipeline_log.append(('Explainability', success))

    # ========== SUMMARY ==========
    total_time = time.time() - total_start
    print_section("PIPELINE COMPLETE")

    print("\n📊 RESULTS SUMMARY:")
    for task, success in pipeline_log:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status} - {task}")

    passed = sum(1 for _, s in pipeline_log if s)
    total = len(pipeline_log)
    print(f"\n  Passed: {passed}/{total}")
    print(f"  Total time: {total_time/60:.1f} minutes")

    print("\n📁 OUTPUT FILES:")
    print("  • best_model.keras - Classification model")
    print("  • segmentation_model.keras - Segmentation model")
    print("  • phase1_history.png, phase2_history.png - Training curves")
    print("  • confusion_matrix.png, roc_curves.png - Evaluation plots")
    print("  • gradcam_evaluation/ - Attention visualizations")
    print("  • unet_training_history.png - Segmentation training curve")
    print("  • segmentation_confusion.png, segmentation_roc.png")

    print("\n🚀 NEXT STEPS:")
    print("  1. Review training curves for overfitting")
    print("  2. Check confusion matrix for misclassifications")
    print("  3. Examine Grad-CAM visualizations for model explanations")
    print("  4. Run batch predictions: python predict.py --image-dir <path>")
    print("  5. Deploy with: python app.py")

    print(f"\n✓ Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    main()
