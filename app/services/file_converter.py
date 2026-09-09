"""Service konversi file: gambar ↔ PDF, DOCX/PPTX ↔ PDF."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

import img2pdf
from pdf2image import convert_from_path

from app.utils.exceptions import AppError

# Format yang didukung untuk konversi
SUPPORTED_CONVERSIONS: dict[str, list[str]] = {
    ".jpg": [".pdf"],
    ".jpeg": [".pdf"],
    ".png": [".pdf"],
    ".docx": [".pdf"],
    ".pptx": [".pdf"],
    ".pdf": [".jpg", ".png", ".docx", ".pptx"],
}


def _get_output_path(original_path: str, target_ext: str) -> str:
    """Generate output path dengan nama unik di direktori yang sama."""
    original = Path(original_path)
    output_name = f"{original.stem}_converted_{uuid4().hex[:8]}{target_ext}"
    return str(original.parent / output_name)


def _image_to_pdf(input_path: str, output_path: str) -> str:
    """Konversi JPG/PNG ke PDF menggunakan img2pdf."""
    try:
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(input_path))
        return output_path
    except Exception as exc:
        raise AppError(f"Gagal konversi gambar ke PDF: {exc}") from exc


def _office_to_pdf(input_path: str, output_dir: str) -> str:
    """Konversi DOCX/PPTX ke PDF menggunakan LibreOffice headless."""
    try:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                input_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AppError(f"LibreOffice gagal: {result.stderr.strip()}")
        input_stem = Path(input_path).stem
        pdf_path = os.path.join(output_dir, f"{input_stem}.pdf")
        if not os.path.isfile(pdf_path):
            raise AppError("File PDF hasil konversi tidak ditemukan.")
        return pdf_path
    except subprocess.TimeoutExpired as exc:
        raise AppError("Konversi memakan waktu terlalu lama (timeout 60 detik).") from exc
    except FileNotFoundError as exc:
        raise AppError("LibreOffice tidak terpasang di sistem.") from exc


def _pdf_to_images(input_path: str, output_dir: str, target_ext: str) -> list[str]:
    """Konversi PDF ke JPG/PNG menggunakan pdf2image + poppler."""
    try:
        images = convert_from_path(input_path, dpi=200)
        output_paths = []
        fmt = "JPEG" if target_ext == ".jpg" else "PNG"
        for i, image in enumerate(images, start=1):
            if len(images) == 1:
                out_name = f"{Path(input_path).stem}_converted{target_ext}"
            else:
                out_name = f"{Path(input_path).stem}_page_{i}{target_ext}"
            out_path = os.path.join(output_dir, out_name)
            image.save(out_path, fmt)
            output_paths.append(out_path)
        return output_paths
    except Exception as exc:
        raise AppError(f"Gagal konversi PDF ke gambar: {exc}") from exc


def _pdf_to_office(input_path: str, output_dir: str, target_ext: str) -> str:
    """Konversi PDF ke DOCX/PPTX menggunakan LibreOffice headless."""
    libreoffice_format = {".docx": "docx", ".pptx": "pptx"}
    fmt = libreoffice_format.get(target_ext)
    if not fmt:
        raise AppError(f"Format target tidak didukung: {target_ext}")
    try:
        result = subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", fmt,
                "--outdir", output_dir,
                input_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise AppError(f"LibreOffice gagal: {result.stderr.strip()}")
        input_stem = Path(input_path).stem
        out_path = os.path.join(output_dir, f"{input_stem}.{fmt}")
        if not os.path.isfile(out_path):
            raise AppError(f"File hasil konversi tidak ditemukan.")
        return out_path
    except subprocess.TimeoutExpired as exc:
        raise AppError("Konversi memakan waktu terlalu lama (timeout 120 detik).") from exc
    except FileNotFoundError as exc:
        raise AppError("LibreOffice tidak terpasang di sistem.") from exc


def convert_file(input_path: str, target_ext: str) -> str | list[str]:
    """
    Konversi file ke format target.

    Args:
        input_path: Path absolut file sumber.
        target_ext: Ekstensi target (termasuk titik, mis. ".pdf").

    Returns:
        str: Path file hasil konversi (untuk output tunggal).
        list[str]: Daftar path file hasil konversi (untuk PDF → multi gambar).

    Raises:
        AppError: Jika konversi gagal atau format tidak didukung.
    """
    input_path = str(Path(input_path).resolve())
    if not os.path.isfile(input_path):
        raise AppError("File sumber tidak ditemukan.")

    source_ext = Path(input_path).suffix.lower()
    target_ext = target_ext.lower()
    if not target_ext.startswith("."):
        target_ext = f".{target_ext}"

    # Validasi kombinasi konversi
    supported = SUPPORTED_CONVERSIONS.get(source_ext, [])
    if target_ext not in supported:
        raise AppError(
            f"Konversi dari {source_ext} ke {target_ext} tidak didukung. "
            f"Format yang didukung: {', '.join(supported)}"
        )

    output_dir = os.path.dirname(input_path)

    # Gambar → PDF
    if source_ext in (".jpg", ".jpeg", ".png") and target_ext == ".pdf":
        output_path = _get_output_path(input_path, ".pdf")
        return _image_to_pdf(input_path, output_path)

    # DOCX/PPTX → PDF
    if source_ext in (".docx", ".pptx") and target_ext == ".pdf":
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = _office_to_pdf(input_path, tmpdir)
            final_path = _get_output_path(input_path, ".pdf")
            shutil.move(pdf_path, final_path)
            return final_path

    # PDF → Gambar (JPG/PNG)
    if source_ext == ".pdf" and target_ext in (".jpg", ".png"):
        return _pdf_to_images(input_path, output_dir, target_ext)

    # PDF → DOCX/PPTX
    if source_ext == ".pdf" and target_ext in (".docx", ".pptx"):
        with tempfile.TemporaryDirectory() as tmpdir:
            office_path = _pdf_to_office(input_path, tmpdir, target_ext)
            final_path = _get_output_path(input_path, target_ext)
            shutil.move(office_path, final_path)
            return final_path

    raise AppError(f"Kombinasi konversi {source_ext} → {target_ext} belum diimplementasikan.")


def get_target_formats(source_ext: str) -> list[str]:
    """Dapatkan daftar format target yang didukung untuk ekstensi sumber."""
    source_ext = source_ext.lower()
    if not source_ext.startswith("."):
        source_ext = f".{source_ext}"
    return SUPPORTED_CONVERSIONS.get(source_ext, [])
