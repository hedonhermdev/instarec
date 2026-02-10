#!/usr/bin/env uv run

import cv2
import numpy as np
import argparse
import sys

MIN_AREA_RATIO = 0.03  # 3% of frame
ASPECT_MIN = 0.6
ASPECT_MAX = 1.6


def extract_card(image_path, debug=False):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not load image")

    h, w = img.shape[:2]
    frame_area = h * w

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. MSER region detection
    mser = cv2.MSER_create()
    mser.setMinArea(500)
    mser.setMaxArea(int(0.5 * img.shape[0] * img.shape[1]))
    regions, _ = mser.detectRegions(gray)

    if not regions:
        return None, 0.0

    # 2. Convert regions to bounding boxes
    boxes = []
    for r in regions:
        x, y, bw, bh = cv2.boundingRect(r)
        boxes.append([x, y, x + bw, y + bh])

    boxes = np.array(boxes)

    # 3. Merge overlapping boxes (card is union of many regions)
    x1 = boxes[:, 0].min()
    y1 = boxes[:, 1].min()
    x2 = boxes[:, 2].max()
    y2 = boxes[:, 3].max()

    bw = x2 - x1
    bh = y2 - y1

    area_ratio = (bw * bh) / frame_area
    aspect = bw / bh

    if area_ratio < MIN_AREA_RATIO:
        return None, area_ratio

    if not (ASPECT_MIN <= aspect <= ASPECT_MAX):
        return None, area_ratio

    card = img[y1:y2, x1:x2]

    if debug:
        dbg = img.copy()
        cv2.rectangle(dbg, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return card, area_ratio, dbg

    return card, area_ratio


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("frame")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    result = extract_card(args.frame, debug=args.debug)

    if args.debug:
        card, score, dbg = result
    else:
        card, score = result

    if card is None or card.size == 0:
        print(f"❌ No embedded card detected (area_ratio={score:.3f})")
        sys.exit(1)

    cv2.imwrite("card.jpg", card)
    if args.debug:
        cv2.imwrite("debug.jpg", dbg)

    print(f"✅ Card extracted → card.jpg (area_ratio={score:.3f})")


if __name__ == "__main__":
    main()
