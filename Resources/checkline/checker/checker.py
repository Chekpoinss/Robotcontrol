THRESHOLD = 20   # допустимая разница скоростей (можно менять)

def read_file(filename):
    data = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 3:
                continue

            frame = int(parts[0])
            motor1 = float(parts[1])
            motor2 = float(parts[2])

            data[frame] = (motor1, motor2)
    return data


true_data = read_file("true.txt")
user_data = read_file("user.txt")

common_frames = sorted(set(true_data.keys()) & set(user_data.keys()))

if not common_frames:
    print("Нет совпадающих кадров")
    exit()

score = 0
total = len(common_frames)

for frame in common_frames:
    t1, t2 = true_data[frame]
    u1, u2 = user_data[frame]

    diff1 = abs(t1 - u1)
    diff2 = abs(t2 - u2)

    if diff1 < THRESHOLD and diff2 < THRESHOLD:
        score += 1

accuracy = (score / total) * 100

print(f"Кадров проверено: {total}")
print(f"Итоговый счёт: {score}")
print(f"Точность: {accuracy:.2f}%")