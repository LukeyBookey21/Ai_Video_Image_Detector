#!/usr/bin/env python3
"""
AI Detector CLI — check images and videos from the command line.

Usage:
    python cli.py photo.jpg
    python cli.py video.mp4
    python cli.py *.png
    python cli.py --verbose photo.jpg
    python cli.py --json photo.jpg
    python cli.py folder/
"""

import argparse
import glob
import json
import os
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


def get_confidence_phrase(confidence, is_ai):
    subject = "AI-generated" if is_ai else "authentic"
    if confidence >= 85:
        return f"Very confident this is {subject}"
    if confidence >= 65:
        return f"Fairly confident this is {subject}"
    if confidence >= 40:
        return "Some concerns about this content"
    return "Not certain — treat with caution"


def analyze_image(detector, path):
    from PIL import Image

    img = Image.open(path)
    with open(path, "rb") as f:
        raw = f.read()
    return detector.detect_image(img, raw_bytes=raw)


def analyze_video(detector, path):
    from video_processor import get_video_processor

    proc = get_video_processor(detector)
    return proc.analyze_video(path)


def print_result(path, result, verbose=False, use_json=False):
    if use_json:
        print(json.dumps({"file": path, **result}, indent=2, default=str))
        return

    verdict = result.get("verdict", "Unknown")
    confidence = result.get("confidence", 0)
    ai_prob = result.get("ai_probability", 0)
    is_ai = verdict == "AI-Generated"

    # Color codes
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    if is_ai:
        color = RED
        icon = "⚠"
    elif confidence < 40:
        color = YELLOW
        icon = "?"
    else:
        color = GREEN
        icon = "✓"

    fname = os.path.basename(path)
    phrase = get_confidence_phrase(confidence, is_ai)

    print(f"\n  {color}{BOLD}{icon} {verdict}{RESET}")
    print(f"  {DIM}{fname}{RESET}")
    print(f"  {phrase} ({ai_prob}% AI probability)")

    if verbose:
        details = result.get("details", {})
        explanation = result.get("explanation", "")

        if explanation:
            print(f"\n  {DIM}Explanation:{RESET}")
            # Word wrap at 70 chars
            words = explanation.split()
            line = "    "
            for word in words:
                if len(line) + len(word) > 74:
                    print(line)
                    line = "    "
                line += word + " "
            if line.strip():
                print(line)

        print(f"\n  {DIM}Signals:{RESET}")
        for key in [
            "metadata_analysis",
            "frequency_analysis",
            "statistical_analysis",
            "texture_analysis",
            "srm_analysis",
            "color_analysis",
            "face_analysis",
        ]:
            if key in details:
                score = details[key].get("ai_score", 0)
                name = key.replace("_analysis", "").replace("_", " ").title()
                bar_len = int(score / 5)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                print(f"    {name:20s} {bar} {score}%")

        # Video-specific
        ta = result.get("temporal_analysis", {})
        if ta:
            print(f"\n  {DIM}Video Analysis:{RESET}")
            print(f"    Temporal score:  {ta.get('temporal_ai_score', 0)}%")
            if ta.get("animation_detected"):
                print(f"    {YELLOW}Animation/stop-motion detected{RESET}")
            if ta.get("duplicate_frame_ratio", 0) > 0:
                print(f"    Duplicate frames: {ta['duplicate_frame_ratio']*100:.0f}%")

        flags = details.get("metadata_analysis", {}).get("flags", [])
        if flags:
            print(f"\n  {DIM}Flags: {', '.join(flags)}{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="AI Detector — check if images/videos are AI-generated",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py photo.jpg              Check a single image
  python cli.py video.mp4              Check a video
  python cli.py *.png                  Check all PNGs in current dir
  python cli.py photos/                Check all files in a folder
  python cli.py -v photo.jpg           Verbose with signal breakdown
  python cli.py --json photo.jpg       Output as JSON
  python cli.py --watch ~/Downloads    Auto-check new downloads
        """,
    )
    parser.add_argument("files", nargs="+", help="Image/video files or folders to check")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed signal breakdown")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--csv", action="store_true", help="Output one CSV line per file (file,verdict,probability)")
    parser.add_argument("--watch", action="store_true", help="Watch folder for new files and auto-check them")
    parser.add_argument("--threshold", type=float, default=None, help="Custom detection threshold (default: 0.33)")
    args = parser.parse_args()

    # Collect all files
    all_files = []
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    video_exts = {".mp4", ".avi", ".mov", ".webm", ".mkv"}

    for pattern in args.files:
        if os.path.isdir(pattern):
            for fname in sorted(os.listdir(pattern)):
                fpath = os.path.join(pattern, fname)
                if os.path.isfile(fpath):
                    all_files.append(fpath)
        elif "*" in pattern or "?" in pattern:
            all_files.extend(sorted(glob.glob(pattern)))
        elif os.path.isfile(pattern):
            all_files.append(pattern)
        else:
            print(f"  Warning: {pattern} not found, skipping", file=sys.stderr)

    # Watch mode — monitor folder for new files
    if args.watch:
        watch_dirs = [p for p in args.files if os.path.isdir(p)]
        if not watch_dirs:
            print("  --watch requires a folder path.", file=sys.stderr)
            sys.exit(1)

        print(f"\n  Loading detector...", end="", flush=True)
        from detector import detector as ai_detector

        ai_detector.load_model()
        mode = "ML + Heuristic" if ai_detector.ml_mode else "Heuristic"
        print(f" ready ({mode} mode)")
        print(f"  Watching {', '.join(watch_dirs)} for new files...")
        print(f"  Press Ctrl+C to stop.\n")

        seen = set()
        supported = image_exts | video_exts
        # Seed with existing files
        for d in watch_dirs:
            for f in os.listdir(d):
                seen.add(os.path.join(d, f))

        try:
            while True:
                for d in watch_dirs:
                    for f in sorted(os.listdir(d)):
                        fpath = os.path.join(d, f)
                        if fpath in seen:
                            continue
                        seen.add(fpath)
                        ext = os.path.splitext(f)[1].lower()
                        if ext not in supported:
                            continue
                        # Wait a moment for file to finish writing
                        time.sleep(0.5)
                        try:
                            if ext in video_exts:
                                result = analyze_video(ai_detector, fpath)
                            else:
                                result = analyze_image(ai_detector, fpath)
                            print_result(fpath, result, verbose=args.verbose, use_json=args.json)
                        except Exception as e:
                            print(f"  Error: {f}: {e}", file=sys.stderr)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n  Stopped watching.")
        sys.exit(0)

    if not all_files:
        print("No files to check.", file=sys.stderr)
        sys.exit(1)

    # Load detector
    quiet = args.json or args.csv
    if not quiet:
        print(f"\n  Loading detector...", end="", flush=True)

    from detector import detector as ai_detector

    ai_detector.load_model()

    if not quiet:
        mode = "ML + Heuristic" if ai_detector.ml_mode else "Heuristic"
        print(f" ready ({mode} mode)")
        print(f"  Checking {len(all_files)} file{'s' if len(all_files) != 1 else ''}...")

    if args.csv:
        print("file,verdict,ai_probability,confidence")

    # Process files
    results = []
    start = time.time()

    for path in all_files:
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in video_exts:
                result = analyze_video(ai_detector, path)
            elif ext in image_exts:
                result = analyze_image(ai_detector, path)
            else:
                if not args.json:
                    print(f"\n  Skipping {os.path.basename(path)} (unsupported format)")
                continue

            if args.csv:
                v = result.get("verdict", "")
                print(f"{os.path.basename(path)},{v},{result.get('ai_probability', 0)},{result.get('confidence', 0)}")
            else:
                print_result(path, result, verbose=args.verbose, use_json=args.json)
            results.append(
                {"file": path, "verdict": result.get("verdict"), "ai_probability": result.get("ai_probability")}
            )
        except Exception as e:
            if args.json:
                print(json.dumps({"file": path, "error": str(e)}))
            elif args.csv:
                print(f"{os.path.basename(path)},ERROR,0,0")
            else:
                print(f"\n  Error on {os.path.basename(path)}: {e}", file=sys.stderr)

    elapsed = round(time.time() - start, 1)

    # Summary
    if not quiet and len(results) > 1:
        ai_count = sum(1 for r in results if r["verdict"] == "AI-Generated")
        real_count = sum(1 for r in results if r["verdict"] == "Real/Authentic")
        print(f"\n  {'─' * 40}")
        print(f"  {len(results)} files checked in {elapsed}s")
        print(f"  AI-Generated: {ai_count}  |  Authentic: {real_count}")
        print()


if __name__ == "__main__":
    main()
