"""Generate simple icons for FocusPrompter Chrome extension."""
from PIL import Image, ImageDraw

def create_icon(size):
    """Create a simple sunrise/focus icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    padding = size // 8
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill='#e94560'
    )

    # Inner circle (sun)
    inner_padding = size // 4
    draw.ellipse(
        [inner_padding, inner_padding, size - inner_padding, size - inner_padding],
        fill='#f39c12'
    )

    # Center dot
    center = size // 2
    dot_size = size // 10
    draw.ellipse(
        [center - dot_size, center - dot_size, center + dot_size, center + dot_size],
        fill='#1a1a2e'
    )

    return img


if __name__ == '__main__':
    for size in [16, 48, 128]:
        img = create_icon(size)
        img.save(f'icons/icon{size}.png')
        print(f'Created icon{size}.png')
