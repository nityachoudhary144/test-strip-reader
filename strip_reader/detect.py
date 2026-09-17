from __future__ import annotations

import cv2
import numpy as np

BG_DISTANCE = 45
MIN_AREA_FRACTION = 0.015
MIN_ELONGATION = 1.5
UNWRAP_WIDTH = 760
UNWRAP_MAX_HEIGHT = 200
MIN_UNWRAP_HEIGHT = 40


def background_colour(bgr: np.ndarray) -> np.ndarray:
    edge = 10
    rings = [
        bgr[:edge].reshape(-1, 3),
        bgr[-edge:].reshape(-1, 3),
        bgr[:, :edge].reshape(-1, 3),
        bgr[:, -edge:].reshape(-1, 3),
    ]
    return np.median(np.concatenate(rings), axis=0)


def find_strip(bgr: np.ndarray) -> np.ndarray | None:
    height, width = bgr.shape[:2]

    background = background_colour(bgr)
    distance = np.linalg.norm(bgr.astype(np.float32) - background, axis=2)
    mask = ((distance > BG_DISTANCE) * 255).astype(np.uint8)

    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_AREA_FRACTION * height * width:
            continue

        rect = cv2.minAreaRect(contour)
        (_, _), (rect_w, rect_h), _ = rect
        long_side, short_side = max(rect_w, rect_h), min(rect_w, rect_h)
        if short_side < 1 or long_side / short_side < MIN_ELONGATION:
            continue

        if area > best_area:
            best_area = area
            best = rect

    return None if best is None else cv2.boxPoints(best).astype(np.float32)


def order_corners(points: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float32)
    centroid = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - centroid[1], points[:, 0] - centroid[0])
    ordered = points[np.argsort(angles)]

    if np.linalg.norm(ordered[2] - ordered[1]) > np.linalg.norm(ordered[1] - ordered[0]):
        ordered = np.roll(ordered, -1, axis=0)

    if ordered[0][0] > ordered[2][0]:
        ordered = ordered[[2, 3, 0, 1]]

    return ordered.astype(np.float32)


def unwrap_strip(bgr: np.ndarray, quad: np.ndarray) -> np.ndarray:
    corners = order_corners(quad)

    long_side = max(
        np.linalg.norm(corners[1] - corners[0]),
        np.linalg.norm(corners[2] - corners[3]),
    )
    short_side = max(
        np.linalg.norm(corners[3] - corners[0]),
        np.linalg.norm(corners[2] - corners[1]),
    )

    width = UNWRAP_WIDTH
    height = int(
        np.clip(
            width * short_side / max(long_side, 1e-6),
            MIN_UNWRAP_HEIGHT,
            UNWRAP_MAX_HEIGHT,
        )
    )

    destination = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(corners, destination)
    return cv2.warpPerspective(bgr, matrix, (width, height), flags=cv2.INTER_LINEAR)


def manual_quad(
    shape: tuple[int, ...],
    angle: float,
    cx: float,
    cy: float,
    length: float,
    thickness: float,
) -> np.ndarray:
    height, width = shape[:2]
    centre = np.array([cx * width, cy * height])
    half_length = 0.5 * length * width
    half_thickness = 0.5 * thickness * height

    theta = np.deg2rad(angle)
    along = np.array([np.cos(theta), np.sin(theta)])
    across = np.array([-np.sin(theta), np.cos(theta)])

    return np.array(
        [
            centre - half_length * along - half_thickness * across,
            centre + half_length * along - half_thickness * across,
            centre + half_length * along + half_thickness * across,
            centre - half_length * along + half_thickness * across,
        ],
        dtype=np.float32,
    )
