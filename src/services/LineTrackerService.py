import cv2
import numpy as np

try:
    from src.domain.interfaces.ILineTracker import ILineTracker
    from src.config import Config
except ImportError:
    from domain.interfaces.ILineTracker import ILineTracker
    from config import Config


class LineTrackerService(ILineTracker):
    def __init__(self, config: Config):
        self.cfg = config

        self.prev_error: float = 0.0
        self.prev_left: float = float(self.cfg.BASE_SPEED)
        self.prev_right: float = float(self.cfg.BASE_SPEED)

        self.frame_index: int = 0
        self.lost_line_frames: int = 0
        self.prev_gray: np.ndarray | None = None
        self.static_frame_count: int = 0
        self.extreme_error_frames: int = 0

    def process_frame(self, frame: np.ndarray) -> tuple[int, int, np.ndarray]:
        debug_frame = frame.copy()
        h, w = frame.shape[:2]
        gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            frame_diff = 999.0
        else:
            frame_diff = float(cv2.absdiff(gray_full, self.prev_gray).mean())

        self.prev_gray = gray_full

        if frame_diff < self.cfg.STATIC_DIFF_THRESHOLD:
            self.static_frame_count += 1
        else:
            self.static_frame_count = 0

        crop_start = int(h * self.cfg.CROP_Y_START)
        crop_end = int(h * self.cfg.CROP_Y_END)
        roi = frame[crop_start:crop_end, :]

        mask = self._build_line_mask(roi)
        contour = self._find_main_contour(mask)

        line_found = contour is not None

        if line_found:
            cx = self._get_contour_center_x(contour)
            error_norm = (cx - (w / 2.0)) / (w / 2.0)
            self.lost_line_frames = 0

            if abs(error_norm) >= self.cfg.EXTREME_ERROR_THRESHOLD:
                self.extreme_error_frames += 1
            else:
                self.extreme_error_frames = 0

            turn = (self.cfg.KP * error_norm) + (
                self.cfg.KD * (error_norm - self.prev_error)
            )

            raw_left = self.cfg.BASE_SPEED + turn
            raw_right = self.cfg.BASE_SPEED - turn

            self.prev_error = error_norm
        else:
            self.lost_line_frames += 1
            self.extreme_error_frames = 0
            raw_left, raw_right = self._get_lost_line_speeds()

        # Сглаживание
        left_smooth = (self.cfg.EMA_ALPHA * raw_left) + (
            (1.0 - self.cfg.EMA_ALPHA) * self.prev_left
        )
        right_smooth = (self.cfg.EMA_ALPHA * raw_right) + (
            (1.0 - self.cfg.EMA_ALPHA) * self.prev_right
        )

        self.prev_left = left_smooth
        self.prev_right = right_smooth

        left_clamped = self._clamp_speed(left_smooth)
        right_clamped = self._clamp_speed(right_smooth)

        # Стартовые кадры = 0 0
        if self.frame_index < self.cfg.STARTUP_ZERO_FRAMES:
            left_clamped = 0
            right_clamped = 0

        # Если видеоряд "замер" на серии кадров, безопасно останавливаемся.
        if self.static_frame_count >= self.cfg.STATIC_STOP_FRAMES:
            left_clamped = 0
            right_clamped = 0

        if self.extreme_error_frames >= self.cfg.EXTREME_ERROR_STOP_FRAMES:
            left_clamped = 0
            right_clamped = 0

        self._draw_debug(
            debug_frame=debug_frame,
            mask=mask,
            contour=contour,
            crop_start=crop_start,
            crop_end=crop_end,
            left_speed=left_clamped,
            right_speed=right_clamped,
            line_found=line_found,
        )

        self.frame_index += 1
        return left_clamped, right_clamped, debug_frame

    def _get_lost_line_speeds(self) -> tuple[float, float]:
        sign = 1.0 if self.prev_error >= 0 else -1.0
        search_turn = self.cfg.KP * self.cfg.LOST_LINE_TURN_FACTOR

        # На короткой потере линии держим предыдущую динамику:
        # это обычно ближе к "истинным" логам, чем резкое торможение.
        if self.lost_line_frames <= self.cfg.LOST_LINE_HOLD_FRAMES:
            hold_left = self.prev_left
            hold_right = self.prev_right
        else:
            hold_left = self.cfg.BASE_SPEED
            hold_right = self.cfg.BASE_SPEED

        target_left = hold_left + (search_turn * sign)
        target_right = hold_right - (search_turn * sign)

        # После длинной потери линии считаем, что трасса потеряна надолго.
        # Для соответствия эталонным логам безопаснее отдавать полную остановку.
        if self.lost_line_frames > self.cfg.LOST_LINE_STOP_AFTER:
            target_left = 0.0
            target_right = 0.0

        return target_left, target_right

    def _build_line_mask(self, roi: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        blur_ksize = self.cfg.GAUSSIAN_BLUR_KERNEL
        if blur_ksize % 2 == 0:
            blur_ksize += 1

        gray = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

        if self.cfg.USE_OTSU:
            _, mask = cv2.threshold(
                gray,
                0,
                255,
                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
            )
        else:
            _, mask = cv2.threshold(
                gray,
                self.cfg.THRESHOLD_VAL,
                255,
                cv2.THRESH_BINARY_INV,
            )

        open_kernel = np.ones(
            (self.cfg.OPEN_KERNEL_SIZE, self.cfg.OPEN_KERNEL_SIZE),
            dtype=np.uint8,
        )
        close_kernel = np.ones(
            (self.cfg.CLOSE_KERNEL_SIZE, self.cfg.CLOSE_KERNEL_SIZE),
            dtype=np.uint8,
        )

        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)

        return mask

    def _find_main_contour(self, mask: np.ndarray):
        contours, _ = cv2.findContours(
            mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return None

        valid_contours = [
            cnt for cnt in contours if cv2.contourArea(cnt) >= self.cfg.MIN_CONTOUR_AREA
        ]

        if not valid_contours:
            return None

        return max(valid_contours, key=cv2.contourArea)

    def _get_contour_center_x(self, contour) -> int:
        moments = cv2.moments(contour)

        if moments["m00"] > 0:
            return int(moments["m10"] / moments["m00"])

        x, _, w, _ = cv2.boundingRect(contour)
        return x + (w // 2)

    def _clamp_speed(self, value: float) -> int:
        value = max(self.cfg.MIN_SPEED, min(self.cfg.MAX_SPEED, value))
        return int(round(value))

    def _draw_debug(
        self,
        debug_frame: np.ndarray,
        mask: np.ndarray,
        contour,
        crop_start: int,
        crop_end: int,
        left_speed: int,
        right_speed: int,
        line_found: bool,
    ) -> None:
        h, w = debug_frame.shape[:2]

        if self.cfg.DRAW_ROI:
            cv2.rectangle(
                debug_frame,
                (0, crop_start),
                (w - 1, crop_end - 1),
                (255, 255, 0),
                2,
            )

        roi_debug = debug_frame[crop_start:crop_end, :]

        if contour is not None:
            cv2.drawContours(roi_debug, [contour], -1, (0, 255, 0), 2)

            cx = self._get_contour_center_x(contour)
            cy = roi_debug.shape[0] // 2
            cv2.circle(roi_debug, (cx, cy), 6, (0, 0, 255), -1)

            cv2.line(
                roi_debug,
                (roi_debug.shape[1] // 2, 0),
                (roi_debug.shape[1] // 2, roi_debug.shape[0] - 1),
                (255, 0, 255),
                2,
            )

        status = "LINE" if line_found else "LOST"
        cv2.putText(
            debug_frame,
            f"frame={self.frame_index + 1}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            debug_frame,
            f"L={left_speed} R={right_speed}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            debug_frame,
            f"status={status}",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255) if line_found else (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

        if self.cfg.DRAW_MASK_PREVIEW:
            preview = cv2.resize(mask, (220, 120))
            preview_bgr = cv2.cvtColor(preview, cv2.COLOR_GRAY2BGR)
            ph, pw = preview_bgr.shape[:2]

            y1 = max(0, h - ph - 20)
            y2 = y1 + ph
            x1 = max(0, w - pw - 20)
            x2 = x1 + pw

            debug_frame[y1:y2, x1:x2] = preview_bgr