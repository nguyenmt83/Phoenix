# HƯỚNG DẪN TRIỂN KHAI HỆ THỐNG GLMS PHOENIX GOLF

## 🌟 PHƯƠNG ÁN 1: TRIỂN KHAI 100% MIỄN PHÍ TRÊN CLOUD (RENDER.COM)
*Dành cho mục đích chạy Demo / Thử nghiệm trước khi trình Ban Giám Đốc.*

1. **Bước 1:** Đăng ký tài khoản miễn phí tại [https://render.com](https://render.com).
2. **Bước 2:** Đẩy thư mục mã nguồn này lên GitHub (hoặc tải trực tiếp).
3. **Bước 3:** Tại Dashboard của Render, chọn **"New Web Service"** -> Kết nối Repository.
   - **Environment:** `Python 3` (hoặc `Node`)
   - **Build Command:** `pip install -r requirements.txt` (hoặc để trống)
   - **Start Command:** `python3 server.py`
4. **Bước 4:** Bấm **"Deploy Web Service"**. Render sẽ tự động cấp một đường link HTTPS miễn phí (Ví dụ: `https://glms-phoenix-golf.onrender.com`).
5. **Bước 5:** Mở link trên điện thoại là nhân viên Housekeeping có thể mở Camera quét mã QR ngay lập tức!

---

## 🏢 PHƯƠNG ÁN 2: CHẠY NỘI BỘ MIỄN PHÍ VỚI CLOUDFLARE TUNNEL (ZERO TRUST)
*Chạy trực tiếp trên máy tính PC/Laptop hoặc Server nội bộ của Sân Golf, miễn phí 100% và có HTTPS chính chủ.*

1. **Bước 1:** Chạy server nội bộ trên máy tính:
   ```bash
   python3 server.py
   ```
2. **Bước 2:** Tải công cụ miễn phí `cloudflared` từ Cloudflare:
   ```bash
   # Tạo đường hầm HTTPS ra ngoài internet trong 1 lệnh duy nhất:
   cloudflared tunnel --url http://localhost:8080
   ```
3. **Bước 3:** Cloudflare sẽ sinh ra một đường link HTTPS công khai (Ví dụ: `https://phoenix-locker.trycloudflare.com`). Nhân viên trong sân mở link này trên điện thoại/PC để sử dụng.

---

## 🐳 PHƯƠNG ÁN 3: TRIỂN KHAI PRODUCTION QUA DOCKER (ON-PREMISE / SYNOLOGY NAS)
```bash
docker-compose up -d
```
Hệ thống sẽ chạy ngầm 24/7 tại cổng `8080`.
