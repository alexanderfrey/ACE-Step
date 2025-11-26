import argparse
import subprocess
from pathlib import Path

from datasets import Dataset


def run_ffmpeg(input_path: Path, output_path: Path, sample_rate: int = 48000):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        str(sample_rate),
        "-ac",
        "2",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed for {input_path} -> {output_path}: {result.stderr.decode(errors='ignore')}"
        )


def build_dataset(
    audio_dir: Path,
    lyrics_dir: Path,
    output_dir: Path,
    tags: list[str],
    recaption: str | None,
    audio_ext: str = ".mp3",
    sample_rate: int = 48000,
):
    audio_dir = audio_dir.expanduser().resolve()
    lyrics_dir = lyrics_dir.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    converted_dir = output_dir / "converted_audio"

    records = []
    for audio_path in sorted(audio_dir.glob(f"*{audio_ext}")):
        base = audio_path.stem
        lyrics_path = lyrics_dir / f"{base}.txt"
        if not lyrics_path.exists():
            print(f"[skip] missing lyrics file for {audio_path.name}")
            continue

        target_audio = converted_dir / f"{base}.wav"
        if not target_audio.exists():
            try:
                run_ffmpeg(audio_path, target_audio, sample_rate=sample_rate)
                print(f"[ok] converted {audio_path.name} -> {target_audio}")
            except Exception as e:
                print(f"[error] convert failed for {audio_path.name}: {e}")
                continue

        with lyrics_path.open(encoding="utf-8") as f:
            norm_lyrics = f.read().strip()
        if not norm_lyrics:
            print(f"[skip] empty lyrics in {lyrics_path}")
            continue

        record = {
            "keys": base,
            "filename": str(target_audio),
            "tags": tags,
            "norm_lyrics": norm_lyrics,
        }
        if recaption:
            record["recaption"] = {"style": recaption}
        records.append(record)

    if not records:
        raise RuntimeError("No valid audio/lyrics pairs found.")

    ds = Dataset.from_list(records)
    output_dir.mkdir(parents=True, exist_ok=True)
    ds.save_to_disk(str(output_dir))
    print(f"Saved dataset with {len(records)} items to {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert MP3s to 48kHz stereo and build a HF disk dataset for LoRA training."
    )
    parser.add_argument("--audio_dir", type=Path, required=True, help="Folder with MP3 files")
    parser.add_argument("--lyrics_dir", type=Path, required=True, help="Folder with .txt lyrics (same basename as audio)")
    parser.add_argument("--output_dir", type=Path, required=True, help="Output path for the HF dataset")
    parser.add_argument(
        "--tags",
        type=str,
        default="pop,midtempo,warm,guitar",
        help="Comma-separated tags applied to every track (edit per song later if needed)",
    )
    parser.add_argument(
        "--recaption",
        type=str,
        default=None,
        help='Optional style hint stored in recaption["style"]',
    )
    parser.add_argument("--audio_ext", type=str, default=".mp3", help="Audio extension to scan for")
    parser.add_argument("--sample_rate", type=int, default=48000, help="Target sample rate for conversion")
    return parser.parse_args()


def main():
    args = parse_args()
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    build_dataset(
        audio_dir=args.audio_dir,
        lyrics_dir=args.lyrics_dir,
        output_dir=args.output_dir,
        tags=tags,
        recaption=args.recaption,
        audio_ext=args.audio_ext,
        sample_rate=args.sample_rate,
    )


if __name__ == "__main__":
    main()
