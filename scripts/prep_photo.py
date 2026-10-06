"""Przygotowanie zdjęcia (lub logo) pod konwersję do ASCII.

1. Usuwa tło (rembg), żeby został sam obiekt.
2. Podbija lokalny kontrast (CLAHE z OpenCV) — płasko oświetlona twarz
   dostaje prawdziwe światła i cienie.
3. Składa wynik na czystej bieli, więc tło mapuje się na spacje w ASCII.

Wynik: skala szarości `source-prepped.png` w katalogu głównym repo.

    python scripts/prep_photo.py zdjecie.jpg
    python scripts/prep_photo.py jhit.gif --frame 14 --no-rembg   # logo
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"


def remove_background(img: Image.Image) -> Image.Image:
    from rembg import remove  # import tutaj: rembg jest ciężki i opcjonalny

    return remove(img.convert("RGBA"))


def boost_contrast(gray: np.ndarray) -> np.ndarray:
    try:
        import cv2
    except ImportError:
        return np.asarray(ImageOps.autocontrast(Image.fromarray(gray), cutoff=1))
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="zdjęcie źródłowe (jpg/png/gif)")
    ap.add_argument("--frame", type=int, default=0, help="klatka animowanego GIF-a")
    ap.add_argument("--no-rembg", action="store_true", help="pomiń usuwanie tła")
    ap.add_argument("--max-size", type=int, default=1024)
    args = ap.parse_args()

    img = Image.open(args.src)
    if getattr(img, "n_frames", 1) > 1:
        img.seek(args.frame)
    img = img.convert("RGBA")
    img.thumbnail((args.max_size, args.max_size))

    if not args.no_rembg:
        img = remove_background(img)

    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white, img).convert("L")

    gray = boost_contrast(np.asarray(flat))
    # Tło (przezroczyste w oryginale) zostaje idealnie białe po CLAHE.
    alpha = np.asarray(img.getchannel("A"))
    gray = np.where(alpha < 16, 255, gray).astype(np.uint8)

    Image.fromarray(gray, "L").save(OUT)
    print(f"zapisano {OUT.relative_to(ROOT)} ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
