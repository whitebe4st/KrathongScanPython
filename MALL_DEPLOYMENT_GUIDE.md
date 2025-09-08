# 🏬 Mall Deployment Setup Guide

## 🚀 Quick Setup for Public Access

Your KrathongScanner needs a public URL to work in the mall. Here's the **easiest solution**:

### ✅ **Option 1: ngrok (Recommended for Mall)**

1. **Sign up for ngrok** (free):

   - Visit: https://ngrok.com
   - Create free account (takes 30 seconds)
   - Get your auth token from dashboard

2. **Setup ngrok**:

   ```bash
   # Download ngrok manually if automatic download fails
   # Visit: https://ngrok.com/download
   # Extract ngrok.exe to a folder in your PATH

   # Set your auth token (replace YOUR_TOKEN with actual token)
   ngrok authtoken YOUR_TOKEN
   ```

3. **Test the setup**:
   ```bash
   # Start the server - it will use ngrok automatically
   python web/server.py
   ```

### ✅ **Option 2: LocalTunnel (Alternative)**

If ngrok doesn't work, use LocalTunnel:

```bash
# Install localtunnel globally
npm install -g localtunnel

# Start your server in one terminal
python web/server.py

# In another terminal, create tunnel
npx localtunnel --port 5000
```

### ✅ **Option 3: Cloudflare Tunnel (Most Reliable)**

For production mall deployment:

```bash
# Download cloudflared
# Visit: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# Create instant tunnel (no signup required)
cloudflared tunnel --url http://localhost:5000
```

## 🎯 **What You'll Get**

✅ **Public HTTPS URL** like: `https://abc123.ngrok.io`
✅ **QR Code Generated** automatically for customer scanning
✅ **High-Quality Display QR** saved as `qr_mall_display.png`
✅ **Mobile-Optimized Interface** in Thai language
✅ **Real-time Processing** with automatic ArUco detection

## 📱 **Mall Deployment Checklist**

- [ ] Public tunnel established (ngrok/cloudflare)
- [ ] QR code printed for customer displays
- [ ] Test upload/download from mobile phone
- [ ] Check internet connection stability
- [ ] Verify processing pipeline works with real krathong photos

## 🔧 **Troubleshooting**

**"All tunnel methods failed":**

- Check internet connection
- Try ngrok with auth token
- Use cloudflared as backup

**"ngrok download failed":**

- Download ngrok manually from https://ngrok.com/download
- Extract to a folder in your system PATH

**"Processing timeout":**

- Check ArUco markers on krathong templates
- Ensure good lighting for photo capture

---

**Ready for Mall Deployment!** 🎉

Once you have a public URL, customers can:

1. Scan QR code with phone
2. Upload krathong photos
3. Download transparent PNG files
4. Share their digital krathongs!
