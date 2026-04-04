# 🎙️ Piper TTS Trainer v3.0

> **Giao diện đồ họa (GUI) giúp huấn luyện, xuất và chạy thử giọng nói Piper TTS — dành riêng cho tiếng Việt.**
> Phát triển bởi **Văn Khải A.I Studio**

---

## ✨ Tính năng nổi bật

| Tính năng | Mô tả |
|---|---|
| 🛠️ Setup tự động | Tạo venv, cài PyTorch, clone piper-train chỉ với 1 nút |
| 📦 Quản lý Dataset | Chọn file CSV, thư mục audio, kiểm tra dữ liệu |
| 🚀 Huấn luyện | Giao diện train trực quan, xem log real-time |
| 📤 Export ONNX | Xuất model sang định dạng `.onnx` để dùng với Piper |
| 🔊 Chạy thử giọng | Tổng hợp và phát audio ngay trong app |
| 🇻🇳 Xử lý tiếng Việt | Module `vn_text_processor` chuyển số, ngày tháng, tiền tệ → chữ |
| 💾 Lưu cấu hình | Tự động lưu/nạp các thiết lập khi đóng/mở app |

---

## 📋 Yêu cầu hệ thống

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.10 – 3.12 (cài sẵn trong PATH)
- **RAM**: tối thiểu 8 GB (khuyến nghị 16 GB+)
- **GPU**: NVIDIA CUDA (tuỳ chọn, tăng tốc độ train)
- **Dung lượng**: ~5 GB cho môi trường venv + model

---

## 🚀 Cài đặt nhanh

### Cách 1 — Dùng file Installer (khuyến nghị)

1. Tải file `PiperTTSTrainer_v3.0_Setup.exe` từ tab [Releases](../../releases)
2. Chạy installer và làm theo hướng dẫn
3. Khởi chạy **Piper TTS Trainer** từ Desktop hoặc Start Menu

### Cách 2 — Chạy từ mã nguồn

```bash
# 1. Clone repo
git clone https://github.com/your-username/piper-tts-trainer.git
cd piper-tts-trainer

# 2. Cài thư viện (chỉ cần tkinter — có sẵn trong Python)
python piper_train_app.py
```

> **Lưu ý**: Khi chạy lần đầu, app sẽ tự tạo virtual environment (`.venv`) và cài các gói cần thiết. Cần kết nối Internet.

---

## 📖 Hướng dẫn sử dụng

### Bước 1 — Setup môi trường

Vào tab **⚙️ Setup**, thực hiện lần lượt từ Bước 01 đến Bước 10:

- Tạo venv Python
- Cài PyTorch + piper-train
- Tải pretrained checkpoint từ HuggingFace

### Bước 2 — Chuẩn bị Dataset

```
project_dir/
├── wavs/               ← Thư mục chứa file audio (.wav)
│   ├── audio_001.wav
│   ├── audio_002.wav
│   └── ...
└── metadata.csv        ← File CSV: audio_id|transcript
```

Định dạng CSV:
```
audio_001|Xin chào, đây là giọng nói tổng hợp.
audio_002|Piper TTS hỗ trợ tiếng Việt rất tốt.
```

### Bước 3 — Huấn luyện

Vào tab **🚀 Train**, điền thông tin:
- **Voice Name**: Tên giọng nói (vd: `my_voice_vi`)
- **Dataset CSV**: Đường dẫn file metadata
- **Audio Dir**: Thư mục chứa file wav
- **Checkpoint**: File `.ckpt` pretrained

Nhấn **▶ Bắt đầu Train** và theo dõi log.

### Bước 4 — Export & Chạy thử

1. Tab **📤 Export**: Chọn checkpoint tốt nhất → Export sang `.onnx`
2. Tab **🔊 Chạy Thử**: Nhập văn bản → Tổng hợp và nghe kết quả

---

## 🇻🇳 Module xử lý tiếng Việt (`vn_text_processor.py`)

Module này tự động chuẩn hóa văn bản trước khi đưa vào Piper:

```python
from vn_text_processor import process

print(process("Giá là 250.000đ, giảm 15%."))
# → "Giá là hai trăm năm mươi nghìn đồng, giảm mười lăm phần trăm."

print(process("Cuộc họp lúc 8h30 ngày 15/3/2025."))
# → "Cuộc họp lúc tám giờ ba mươi phút ngày mười lăm tháng ba năm hai nghìn không trăm hai mươi lăm."
```

**Hỗ trợ:**
- Số → chữ (`250` → `hai trăm năm mươi`)
- Ngày tháng (`15/3/2025` → `ngày mười lăm tháng ba...`)
- Giờ (`8h30`, `08:30`)
- Tiền tệ (`250.000đ`, `$100`)
- Phần trăm (`12%`, `3,5%`)
- Đơn vị đo (`5km`, `37°C`, `90km/h`)
- Số điện thoại (đọc từng số)
- Phiên âm tiếng Anh (`love` → `lớp`)
- Dọn emoji, URL, email

---

## 🏗️ Build từ mã nguồn

### Yêu cầu build
- Python 3.10+
- PyInstaller: `pip install pyinstaller`
- Inno Setup 6+: [jrsoftware.org](https://jrsoftware.org/isinfo.php)

### Build EXE

```bash
pyinstaller --noconfirm --onedir --windowed --name PiperTrainer ^
    --add-data "vn_text_processor.py;." ^
    piper_train_app.py
```

### Đóng gói Installer

Mở `PiperTrainer_Setup.iss` bằng **Inno Setup Compiler** → **Build → Compile**

File installer sẽ xuất hiện tại `Output\PiperTTSTrainer_v3.0_Setup.exe`

---

## 📁 Cấu trúc thư mục

```
piper-tts-trainer/
├── piper_train_app.py          ← App chính (GUI Tkinter)
├── vn_text_processor.py        ← Module xử lý văn bản tiếng Việt
├── PiperTrainer_Setup.iss      ← Script Inno Setup để build installer
├── README.md
└── dist/                       ← Thư mục output của PyInstaller
    └── PiperTrainer/
        └── PiperTrainer.exe
```

---

## 🤝 Đóng góp

Pull requests và issues luôn được chào đón!

1. Fork repo này
2. Tạo branch mới: `git checkout -b feat/ten-tinh-nang`
3. Commit thay đổi: `git commit -m "feat: thêm tính năng X"`
4. Push lên branch: `git push origin feat/ten-tinh-nang`
5. Tạo Pull Request

---

## 📄 Giấy phép

Dự án này được phân phối theo giấy phép **MIT**. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

<div align="center">
  <b>Phát triển với ❤️ bởi Văn Khải A.I Studio</b>
</div>
