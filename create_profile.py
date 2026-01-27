"""Generate profile picture for Focus Agent Slack bot."""
from PIL import Image, ImageDraw

def create_profile_image(size=512):
    # Create image with dark blue background
    img = Image.new('RGB', (size, size), '#1a1a2e')
    draw = ImageDraw.Draw(img)

    center = size // 2

    # Draw horizon line
    horizon_y = int(size * 0.55)
    draw.rectangle([60, horizon_y, size-60, horizon_y+3], fill='#4a5568')

    # Draw sun (orange-red gradient effect with concentric circles)
    sun_radius = 80
    sun_colors = ['#e74c3c', '#e67e22', '#f39c12']
    for i, color in enumerate(sun_colors):
        r = sun_radius - (i * 20)
        draw.ellipse([center-r, horizon_y-r, center+r, horizon_y+r], fill=color)

    # Cover bottom half of sun with background
    draw.rectangle([0, horizon_y, size, size], fill='#1a1a2e')

    # Re-draw horizon line on top
    draw.rectangle([60, horizon_y, size-60, horizon_y+3], fill='#4a5568')

    # Draw sun rays
    ray_color = '#f39c12'
    ray_positions = [
        (center, 140, center, 170),          # top
        (176, 160, 190, 185),                # top-left
        (336, 160, 322, 185),                # top-right
        (130, 210, 155, 225),                # left
        (382, 210, 357, 225),                # right
    ]
    for x1, y1, x2, y2 in ray_positions:
        draw.line([(x1, y1), (x2, y2)], fill=ray_color, width=3)

    # Draw focus circles (subtle)
    circle_color = '#64748b'
    # Outer circle
    draw.ellipse([center-100, center-100, center+100, center+100],
                 outline=circle_color, width=2)
    # Inner circle
    draw.ellipse([center-50, center-50, center+50, center+50],
                 outline=circle_color, width=2)

    # Draw crosshair lines
    draw.line([(center, center-120), (center, center-80)], fill=circle_color, width=2)
    draw.line([(center, center+80), (center, center+120)], fill=circle_color, width=2)
    draw.line([(center-120, center), (center-80, center)], fill=circle_color, width=2)
    draw.line([(center+80, center), (center+120, center)], fill=circle_color, width=2)

    # Center dot
    draw.ellipse([center-6, center-6, center+6, center+6], fill='#f39c12')

    return img


if __name__ == '__main__':
    img = create_profile_image(512)
    img.save('profile.png')
    print("Created profile.png (512x512)")
