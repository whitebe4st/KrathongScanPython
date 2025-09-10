#!/usr/bin/env python3
"""
Simple script to generate QR code files
"""

import os

import qrcode


def generate_qr_files():
    """Generate QR code files for local and public access"""

    # URLs to generate QR codes for
    local_url = "http://127.0.0.1:5000"
    public_url = "https://example.ngrok-free.app"  # Placeholder

    # Create static directory
    static_dir = "static"
    os.makedirs(static_dir, exist_ok=True)

    # Generate local QR code
    print("📱 Generating local QR code...")
    local_qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    local_qr.add_data(local_url)
    local_qr.make(fit=True)
    local_img = local_qr.make_image(fill_color="black", back_color="white")

    # Save local QR code
    local_path = os.path.join(static_dir, "qr_local.png")
    local_img.save(local_path)
    print(f"✅ Local QR code saved: {local_path}")

    # Generate public QR code (placeholder)
    print("🌍 Generating public QR code...")
    public_qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    public_qr.add_data(public_url)
    public_qr.make(fit=True)
    public_img = public_qr.make_image(fill_color="black", back_color="white")

    # Save public QR code
    public_path = os.path.join(static_dir, "qr_public.png")
    public_img.save(public_path)
    print(f"✅ Public QR code saved: {public_path}")

    print("\n📂 QR code files generated in static/ directory:")
    print(f"   • qr_local.png  → {local_url}")
    print(f"   • qr_public.png → {public_url}")


if __name__ == "__main__":
    generate_qr_files()
