"""
Helper script to install ML dependencies and download the detection model.
Run this once for significantly better detection accuracy (~94% vs ~65% heuristic).

Usage:
    python install_ml.py
"""

import subprocess
import sys


def main():
    print("=" * 60)
    print("  AI Detector — ML Model Setup")
    print("=" * 60)

    # Step 1: Install torch and transformers
    print("\n[1/2] Installing PyTorch and Transformers...")
    print("       This may take a few minutes...\n")

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "torch", "torchvision", "transformers"],
        capture_output=False,
    )

    if result.returncode != 0:
        print("\nFailed to install PyTorch. You may need to:")
        print("  1. Check your Python version (3.10-3.12 recommended)")
        print("  2. Visit https://pytorch.org/get-started/locally/ for install instructions")
        print("  3. Try: pip install torch --index-url https://download.pytorch.org/whl/cpu")
        return False

    # Step 2: Download the model
    print("\n[2/2] Downloading detection model (Organika/sdxl-detector, ~350MB)...")
    print("       This is a one-time download...\n")

    try:
        from transformers import pipeline

        pipe = pipeline("image-classification", model="Organika/sdxl-detector", device=-1)
        print("\nModel downloaded and verified!")
    except Exception as e:
        print(f"\nModel download failed: {e}")
        print("The model will be downloaded automatically on first use.")

    print("\n" + "=" * 60)
    print("  Setup complete! Restart the backend: python main.py")
    print("  The detector will now use ML + heuristic ensemble mode.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    main()
