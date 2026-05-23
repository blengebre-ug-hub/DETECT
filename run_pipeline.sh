#!/bin/bash

# 3D EUS AI Pipeline Runner

echo "=========================================="
echo "3D EUS AI System - Pipeline Runner"
echo "=========================================="
echo ""

# Activate virtual environment
source venv/bin/activate

echo "✓ Virtual environment activated"
echo ""

# Step 1: Training
echo "=========================================="
echo "Step 1: Training Model"
echo "=========================================="
python train.py
TRAIN_EXIT=$?

if [ $TRAIN_EXIT -ne 0 ]; then
    echo "❌ Training failed with exit code $TRAIN_EXIT"
    exit 1
fi

echo ""
echo "✓ Training completed successfully"
echo ""

# Step 2: Evaluation
echo "=========================================="
echo "Step 2: Evaluation + Metrics"
echo "=========================================="
python evaluate.py
EVAL_EXIT=$?

if [ $EVAL_EXIT -ne 0 ]; then
    echo "❌ Evaluation failed with exit code $EVAL_EXIT"
    exit 1
fi

echo ""
echo "✓ Evaluation completed successfully"
echo ""

# Summary
echo "=========================================="
echo "✓ PIPELINE COMPLETE!"
echo "=========================================="
echo ""
echo "Output files generated:"
echo "  📊 best_model.keras"
echo "  📈 phase1_history.png"
echo "  📈 phase2_history.png"
echo "  📊 confusion_matrix.png"
echo "  📊 roc_curves.png"
echo "  🔍 gradcam_evaluation/ (10 samples)"
echo ""
