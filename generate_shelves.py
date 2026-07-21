#!/bin/python3
from PIL import Image, ImageDraw
import numpy as np

NUM_SHELVES = 3
IMAGE_WIDTH = 800
IMAGE_HEIGHT = 600
CELL_SIZE = 20
SHELF_WIDTH = 400
SHELF_HEIGHT = 2 * CELL_SIZE
SHELF_COLOR = (128, 128, 128)
BACKGROUND_COLOR = (255, 255, 255)
GAP = 5 * CELL_SIZE
GRID_COLOR = (200, 200, 200)

def draw_shelves(num_shelves):
    img = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    total_height = num_shelves * SHELF_HEIGHT + (num_shelves - 1) * GAP
    start_y = round((IMAGE_HEIGHT - total_height) / 2 / CELL_SIZE) * CELL_SIZE
    start_x = round((IMAGE_WIDTH - SHELF_WIDTH) / 2 / CELL_SIZE) * CELL_SIZE

    shelves = []
    for i in range(num_shelves):
        y = start_y + i * (SHELF_HEIGHT + GAP)
        draw.rectangle([start_x, y, start_x + SHELF_WIDTH - 1, y + SHELF_HEIGHT - 1], fill=SHELF_COLOR)
        shelves.append({
            "id": i + 1,
            "x1": start_x,
            "y1": y,
            "x2": start_x + SHELF_WIDTH,
            "y2": y + SHELF_HEIGHT,
            "center_x": start_x + SHELF_WIDTH // 2,
            "center_y": y + SHELF_HEIGHT // 2,
        })

    return img, shelves

def fill_grid_cells(img, matrix):
    draw = ImageDraw.Draw(img)
    for r, row in enumerate(matrix):
        for c, val in enumerate(row):
            if val == 1:
                x0 = c * CELL_SIZE
                y0 = r * CELL_SIZE
                draw.rectangle([x0, y0, x0 + CELL_SIZE - 1, y0 + CELL_SIZE - 1], fill=SHELF_COLOR)
    return img

def draw_grid(draw):
    for x in range(0, IMAGE_WIDTH, CELL_SIZE):
        draw.line([(x, 0), (x, IMAGE_HEIGHT)], fill=GRID_COLOR)
    for y in range(0, IMAGE_HEIGHT, CELL_SIZE):
        draw.line([(0, y), (IMAGE_WIDTH, y)], fill=GRID_COLOR)

def build_binary_matrix(img):
    cols = IMAGE_WIDTH // CELL_SIZE
    rows = IMAGE_HEIGHT // CELL_SIZE
    matrix = []
    for r in range(rows):
        row = []
        for c in range(cols):
            x0 = c * CELL_SIZE
            y0 = r * CELL_SIZE
            non_white = False
            for dy in range(CELL_SIZE):
                for dx in range(CELL_SIZE):
                    px = img.getpixel((x0 + dx, y0 + dy))
                    if px != BACKGROUND_COLOR:
                        non_white = True
                        break
                if non_white:
                    break
            row.append(1 if non_white else 0)
        matrix.append(row)
    return matrix

def print_matrix(matrix):
    cols = len(matrix[0])
    header = "     " + "".join(f"{c:>2}" for c in range(cols))
    print(header)
    print("     " + "----" * cols)
    for r, row in enumerate(matrix):
        print(f"r{r:>2} |" + "".join(f" {v} " for v in row))

def print_distances(shelves):
    print(f"{'Shelf A':>8} {'Shelf B':>8} {'Distance (px)':>14} {'Distance (px)':>14}")
    print(f"{'':>8} {'':>8} {'(top-top)':>14} {'(center-center)':>14}")
    print("-" * 44)
    for i in range(len(shelves)):
        for j in range(i + 1, len(shelves)):
            top_dist = abs(shelves[j]["y1"] - shelves[i]["y1"])
            center_dist = abs(shelves[j]["center_y"] - shelves[i]["center_y"])
            print(f"{shelves[i]['id']:>8} {shelves[j]['id']:>8} {top_dist:>14} {center_dist:>14}")

if __name__ == "__main__":
    img, shelves = draw_shelves(NUM_SHELVES)

    matrix = build_binary_matrix(img)

    fill_grid_cells(img, matrix)

    draw = ImageDraw.Draw(img)
    draw_grid(draw)
    img.save("shelves.png")

    print(f"Generated image with {NUM_SHELVES} shelves: shelves.png\n")
    print_distances(shelves)
    print(f"\nBinary matrix (CELL_SIZE={CELL_SIZE}px):")
    print(f"Rows={len(matrix)}, Cols={len(matrix[0])}")
    print_matrix(matrix)
    np.save('bin_mask.npy', matrix)
