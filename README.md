# Robotcontrol
# Line Following Robot | Hackathon MVP

Решение для задачи по компьютерному зрению: программа анализирует видео с робота, находит черную линию на белом фоне и вычисляет скорости левого и правого моторов для движения по траектории.

## Описание

На вход программе подается видео с камеры робота.  
Задача решения:

- распознать черную линию на белом фоне;
- вычислить скорости моторов робота;
- сохранить результат в лог-файл;
- при необходимости сохранить debug-видео с визуализацией работы алгоритма.

## Стек

- Python 3.10+
- OpenCV
- NumPy


##Запуск
py -m src.main Resources/checkline/for_pub/eval1/robot_2026-03-13_10-27-09 outputs/eval1_user.txt outputs/eval1_debug.mp4

## Структура проекта

```text
.
├── resources/
├── requirements.txt
└── src/
    ├── config.py
    ├── main.py
    ├── services/
    │   └── LineTrackerService.py
    └── domain/
        └── interfaces/
            └── ILineTracker.py
