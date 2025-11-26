"""
Download all videos from a YouTube channel as MP3 files.

Requirements:
- yt-dlp (pip install yt-dlp)
- ffmpeg available on PATH (already present per user)

Usage:
    python scripts/download_channel_mp3.py \\
        --channel_url https://www.youtube.com/@ChannelHandle \\
        --output_dir /path/to/output \\
        --max_concurrent 2

Notes:
- This script uses yt-dlp’s channel pagination to fetch all uploads.
- Audio is extracted at the best available quality and converted to MP3.
"""

import argparse
import subprocess
from pathlib import Path


def ensure_output_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def download_channel(channel_url: str, output_dir: Path, max_concurrent: int):
    """
    Download channel videos as MP3 using yt-dlp.
    """
    ensure_output_dir(output_dir)

    # yt-dlp template: %(title)s-%(id)s.%(ext)s to avoid collisions
    output_template = str(output_dir / "%(title)s-%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "--yes-playlist",
        "--ignore-errors",
        "--no-abort-on-error",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",  # best
        "--concurrent-fragments",
        str(max_concurrent),
        "--output",
        output_template,
        channel_url,
    ]

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download all YouTube channel videos as MP3 using yt-dlp."
    )
    parser.add_argument(
        "--channel_url",
        type=str,
        required=True,
        help="Channel URL or handle, e.g., https://www.youtube.com/@ChannelHandle",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        required=True,
        help="Directory to store MP3 files",
    )
    parser.add_argument(
        "--max_concurrent",
        type=int,
        default=2,
        help="Max concurrent fragments (controls download speed vs. throttling)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    download_channel(args.channel_url, args.output_dir, args.max_concurrent)


if __name__ == "__main__":
    main()
