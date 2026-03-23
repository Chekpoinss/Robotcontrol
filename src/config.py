from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    TARGET_FRAMES: int = 500

    # В примерах логов первые кадры часто идут 0 0,
    # поэтому держим небольшой стартовый "разгон".
    STARTUP_ZERO_FRAMES: int = 12

    # Скорости
    BASE_SPEED: int = 170
    SEARCH_SPEED: int = 110
    MIN_SPEED: int = 0
    MAX_SPEED: int = 255

    # PD-регулятор
    KP: float = 115.0
    KD: float = 38.0

    # Сглаживание скоростей
    EMA_ALPHA: float = 0.45

    # ROI по Y: смотрим в нижнюю часть кадра
    CROP_Y_START: float = 0.55
    CROP_Y_END: float = 1.0

    # Бинаризация
    THRESHOLD_VAL: int = 105
    USE_OTSU: bool = True
    GAUSSIAN_BLUR_KERNEL: int = 5

    # Морфология
    OPEN_KERNEL_SIZE: int = 3
    CLOSE_KERNEL_SIZE: int = 5

    # Минимальная площадь линии
    MIN_CONTOUR_AREA: int = 250

    # Если линия потеряна, столько кадров пытаемся "докрутиться",
    # потом отдаём 0 0
    LOST_LINE_STOP_AFTER: int = 8

    # Для debug
    DRAW_ROI: bool = True
    DRAW_MASK_PREVIEW: bool = False