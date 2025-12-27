import qrcode

APP_URL = "https://image-labeler-app.onrender.com"
QR_CODE_FILENAME = "app_qr_code.png"

def generate_qr_code(url, filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"QR code for {url} saved as {filename}")

if __name__ == "__main__":
    generate_qr_code(APP_URL, QR_CODE_FILENAME)
