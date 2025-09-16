"""
Simple QR Generator for KrathongScanner
Generate QR codes for any URL manually
"""

import os
import sys

import qrcode


def generate_qr_code(url, filename="manual_qr.png"):
    """Generate high-quality QR code for given URL"""
    try:
        print(f"🌐 Creating QR code for: {url}")

        # Create high-quality QR code for mall display
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=6,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save QR code
        img.save(filename)

        print(f"📱 QR code saved: {os.path.abspath(filename)}")
        print("🏬 Ready for mall deployment!")
        print("✅ QR code generation complete!")

        return True

    except Exception as e:
        print(f"❌ Failed to generate QR code: {e}")
        return False


def main():
    print("🚀 QR Code Generator for KrathongScanner")
    print("=" * 50)

    if len(sys.argv) > 1:
        # URL provided as command line argument
        url = sys.argv[1]
    else:
        # Ask user for URL
        url = input("🌐 Enter the tunnel URL: ").strip()

    if not url:
        print("❌ No URL provided")
        return

    if not url.startswith("http"):
        url = "https://" + url

    # Generate filename based on URL
    filename = f"qr_{url.split('/')[-1].split('.')[0]}.png"

    # Generate QR code
    if generate_qr_code(url, filename):
        print(f"\n💡 To use this QR code:")
        print(f"   1. Print the file: {filename}")
        print(f"   2. Display it for customers to scan")
        print(f"   3. Customers will be directed to: {url}")


if __name__ == "__main__":
    main()
