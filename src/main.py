from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, Tuple

import cv2

try:
    from src.config import Config
    from src.services.LineTrackerService import LineTrackerService
except ImportError:
    from config import Config
    from services.LineTrackerService import LineTrackerService


def ensure_parent_dir(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def write_results(output_txt_path: Path, results: List[Tuple[int, int]]) -> None:
    ensure_parent_dir(output_txt_path)

    with output_txt_path.open("w", encoding="utf-8") as f:
        for frame_idx, (left_speed, right_speed) in enumerate(results, start=1):
            f.write(f"{frame_idx} {int(left_speed)} {int(right_speed)}\n")


def create_debug_writer(
    debug_video_path: Path,
    fps: float,
    width: int,
    height: int,
) -> cv2.VideoWriter:
    ensure_parent_dir(debug_video_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(str(debug_video_path), fourcc, fps, (width, height))


def pad_results(results: List[Tuple[int, int]], target_frames: int) -> List[Tuple[int, int]]:
    if len(results) >= target_frames:
        return results[:target_frames]

    if not results:
        pad_value = (0, 0)
    else:
        pad_value = results[-1]

    while len(results) < target_frames:
        results.append(pad_value)

    return results


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage:\n"
            "  python -m src.main <input_video.avi> <output_log.txt> [debug_output.mp4]\n"
            "or\n"
            "  python src/main.py <input_video.avi> <output_log.txt> [debug_output.mp4]"
        )
        sys.exit(1)

    input_video_path = Path(sys.argv[1])
    output_txt_path = Path(sys.argv[2])
    debug_video_path: Optional[Path] = Path(sys.argv[3]) if len(sys.argv) >= 4 else None

    if not input_video_path.exists():
        print(f"Input video not found: {input_video_path}")
        sys.exit(1)

    config = Config()
    tracker = LineTrackerService(config)

    cap = cv2.VideoCapture(str(input_video_path))
    if not cap.isOpened():
        print(f"Failed to open video: {input_video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 640)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 480)

    debug_writer: Optional[cv2.VideoWriter] = None
    if debug_video_path is not None:
        debug_writer = create_debug_writer(debug_video_path, fps, width, height)

    results: List[Tuple[int, int]] = []
    frame_index = 0
    max_frames = config.TARGET_FRAMES

    try:
        while frame_index < max_frames:
            ok, frame = cap.read()
            if not ok:
                break

            left_speed, right_speed, debug_frame = tracker.process_frame(frame)
            results.append((int(left_speed), int(right_speed)))

            if debug_writer is not None:
                cv2.putText(
                    debug_frame,
                    f"frame={frame_index + 1}",
                    (20, height - 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                debug_writer.write(debug_frame)

            frame_index += 1

    finally:
        cap.release()
        if debug_writer is not None:
            debug_writer.release()

    results = pad_results(results, config.TARGET_FRAMES)
    write_results(output_txt_path, results)

    print(f"Saved {len(results)} lines to: {output_txt_path}")
    if debug_video_path is not None:
        print(f"Saved debug video to: {debug_video_path}")


if __name__ == "__main__":
    main()