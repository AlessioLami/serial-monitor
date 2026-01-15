from PIL import Image, ImageDraw

sizes = [16, 32, 48, 64, 128, 256]
images = []

for size in sizes:
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    padding = size // 8

    draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=size // 6,
        fill='#0c0c0c',
        outline='#22d3ee',
        width=max(1, size // 32)
    )

    dot_radius = size // 10
    dot_x = size // 2
    dot_y = size // 3
    draw.ellipse(
        [dot_x - dot_radius, dot_y - dot_radius,
         dot_x + dot_radius, dot_y + dot_radius],
        fill='#4ade80'
    )

    wave_y = size * 2 // 3
    wave_height = size // 8
    line_width = max(1, size // 20)

    points = []
    for x in range(padding * 2, size - padding * 2, max(1, size // 16)):
        offset = wave_height if (x // (size // 8)) % 2 == 0 else -wave_height // 2
        points.append((x, wave_y + offset))

    if len(points) > 1:
        draw.line(points, fill='#22d3ee', width=line_width)

    images.append(img)

images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
print("icon.ico creato!")
