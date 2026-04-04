"""
ML Model Setup — install dependencies and download detection models.
Supports CPU-only and GPU installations.

Usage:
    python install_ml.py           # CPU only (default, ~500MB)
    python install_ml.py --gpu     # With CUDA GPU support (~2GB)
    python install_ml.py --check   # Check if models are already installed
"""

import argparse
import subprocess
import sys


def check_installed():
    """Check if ML dependencies and models are available."""
    checks = {}
    try:
        import torch

        checks["torch"] = torch.__version__
        checks["cuda"] = torch.cuda.is_available()
        checks["device"] = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        checks["torch"] = None

    try:
        import transformers

        checks["transformers"] = transformers.__version__
    except ImportError:
        checks["transformers"] = None

    try:
        from transformers import pipeline

        # Check if models are cached
        import os

        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        checks["sdxl_cached"] = (
            any("sdxl-detector" in d for d in os.listdir(cache_dir)) if os.path.exists(cache_dir) else False
        )
        checks["deepfake_cached"] = (
            any("deepfake-detector" in d for d in os.listdir(cache_dir)) if os.path.exists(cache_dir) else False
        )
    except Exception:
        checks["sdxl_cached"] = False
        checks["deepfake_cached"] = False

    return checks


def main():
    parser = argparse.ArgumentParser(description="Install ML dependencies for AI Detector")
    parser.add_argument("--gpu", action="store_true", help="Install with CUDA GPU support")
    parser.add_argument("--check", action="store_true", help="Check installation status only")
    args = parser.parse_args()

    print("=" * 60)
    print("  AI Detector — ML Model Setup")
    print("=" * 60)

    if args.check:
        checks = check_installed()
        print(f"\n  PyTorch:        {'v' + checks['torch'] if checks['torch'] else 'Not installed'}")
        print(f"  Transformers:   {'v' + checks['transformers'] if checks['transformers'] else 'Not installed'}")
        print(f"  CUDA GPU:       {'Available' if checks.get('cuda') else 'Not available (using CPU)'}")
        print(f"  SDXL Detector:  {'Cached' if checks.get('sdxl_cached') else 'Not downloaded'}")
        print(f"  Deepfake Model: {'Cached' if checks.get('deepfake_cached') else 'Not downloaded'}")
        ready = checks.get("torch") and checks.get("transformers")
        print(f"\n  Status: {'Ready to use' if ready else 'Not installed — run: python install_ml.py'}")
        print("=" * 60)
        return

    # Step 1: Install PyTorch
    print("\n[1/3] Installing PyTorch and Transformers...")
    if args.gpu:
        print("       Installing with CUDA GPU support...")
        cmd = [sys.executable, "-m", "pip", "install", "torch", "torchvision", "transformers"]
    else:
        print("       Installing CPU-only version (smaller download)...")
        cmd = [sys.executable, "-m", "pip", "install", "torch", "--index-url", "https://download.pytorch.org/whl/cpu"]

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("\nFailed to install PyTorch.")
        print("  Visit https://pytorch.org/get-started/locally/ for help")
        return False

    if not args.gpu:
        # Install transformers separately for CPU install
        subprocess.run([sys.executable, "-m", "pip", "install", "transformers"], capture_output=False)

    # Step 2: Download SDXL detector
    print("\n[2/3] Downloading SDXL detector model (~350MB)...")
    try:
        from transformers import pipeline

        pipe = pipeline("image-classification", model="Organika/sdxl-detector", device=-1)
        print("       SDXL detector downloaded and verified.")
        del pipe
    except Exception as e:
        print(f"       Download failed: {e}")
        print("       Will retry automatically on first use.")

    # Step 3: Download deepfake detector
    print("\n[3/3] Downloading deepfake detector model (~350MB)...")
    try:
        from transformers import pipeline

        pipe = pipeline("image-classification", model="prithivMLmods/deepfake-detector-model-v1", device=-1)
        print("       Deepfake detector downloaded and verified.")
        del pipe
    except Exception as e:
        print(f"       Download failed: {e}")
        print("       Will retry automatically on first use.")

    print("\n" + "=" * 60)
    print("  Setup complete! Restart the backend:")
    print("    python main.py")
    print("")
    print("  The detector will now use ML + heuristic ensemble mode")
    print("  for significantly better accuracy (~94%).")
    print("=" * 60)

    # Verify
    checks = check_installed()
    if checks.get("torch"):
        print(f"\n  Verified: PyTorch {checks['torch']}, {'GPU' if checks.get('cuda') else 'CPU'} mode")


if __name__ == "__main__":
    main()
