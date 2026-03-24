from dataclasses import dataclass


@dataclass(slots=True)
class Config:
    TARGET_FRAMES: int = 500

    # В примерах логов первые кадры часто идут 0 0,
    # поэтому держим небольшой стартовый "разгон".
    STARTUP_ZERO_FRAMES: int = 12

    # Скорости
    BASE_SPEED: int = 170
    SEARCH_SPEED: int = 130
    MIN_SPEED: int = 0
    MAX_SPEED: int = 255

    # PD-регулятор
    KP: float = 128.0
    KD: float = 44.0

    # Сглаживание скоростей
    EMA_ALPHA: float = 0.62
    OUTPUT_EMA_ALPHA: float = 0.4
    OUTPUT_SCALE_AROUND_BASE: float = 0.9

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
    LOST_LINE_HOLD_FRAMES: int = 10
    LOST_LINE_STOP_AFTER: int = 24
    LOST_LINE_TURN_FACTOR: float = 0.46

    # Детект "замершего" видеопотока (часто на конце ролика):
    # если кадры почти не меняются достаточно долго, останавливаемся.
    STATIC_DIFF_THRESHOLD: float = 1.0
    STATIC_STOP_FRAMES: int = 8

    # Защита от бесконечного "кручения" на краю кадра:
    # если ошибка слишком большая слишком долго, считаем трек потерянным.
    EXTREME_ERROR_THRESHOLD: float = 0.72
    EXTREME_ERROR_STOP_FRAMES: int = 22

    # Для debug
    DRAW_ROI: bool = True
    DRAW_MASK_PREVIEW: bool = False