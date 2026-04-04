<div align="center">

<img src="assets/banner.png" width="800" alt="Piper TTS Trainer Banner"/>
<br><br>

<img src="assets/thumbnail.png" width="80" alt="Piper TTS Trainer Icon"/>

# 🎙️ Piper TTS Trainer

**Giao diện đồ họa huấn luyện, xuất và chạy thử giọng nói Piper TTS**<br>
Tối ưu cho tiếng Việt — Phát triển bởi **Văn Khải A.I Studio**

</div>

[![Version](https://img.shields.io/badge/version-3.0-2563eb)](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4?logo=windows)](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

### ⬇️ [Tải về bản mới nhất](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)

</div>

---

## ✨ Tính năng

| | Tính năng | Mô tả |
|---|---|---|
| 🛠️ | **Setup tự động** | Tạo venv, cài PyTorch, clone piper-train chỉ với 1 nút bấm |
| 📦 | **Quản lý Dataset** | Chọn file CSV + thư mục audio, kiểm tra dữ liệu trực quan |
| 🚀 | **Huấn luyện** | Giao diện train với log real-time, hỗ trợ checkpoint |
| 📤 | **Export ONNX** | Xuất model sang `.onnx` để dùng trực tiếp với Piper |
| 🔊 | **Chạy thử giọng** | Tổng hợp và phát audio ngay trong app |
| 🇻🇳 | **Xử lý tiếng Việt** | Tự động chuyển số, ngày tháng, tiền tệ, đơn vị → chữ |
| 🔔 | **Tự cập nhật** | App tự kiểm tra và thông báo khi có phiên bản mới |
| 💾 | **Lưu cấu hình** | Tự động lưu/nạp thiết lập khi đóng/mở app |

---

## 💻 Yêu cầu hệ thống

| | Tối thiểu | Khuyến nghị |
|---|---|---|
| **OS** | Windows 10 64-bit | Windows 11 64-bit |
| **RAM** | 8 GB | 16 GB trở lên |
| **GPU** | Không bắt buộc | NVIDIA CUDA (tăng tốc train) |
| **Python** | 3.10 – 3.12 | 3.11 |
| **Dung lượng** | 500 MB (app) | ~5 GB (app + venv + model) |

> ⚠️ **Python phải được cài sẵn và có trong PATH** trước khi chạy app.
> Tải Python tại: [python.org/downloads](https://www.python.org/downloads/)

---

## 📥 Cài đặt

### Bước 1 — Tải file installer

Vào trang **[Releases](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)** và tải file:

```
PiperTTSTrainer_vX.X_Setup.exe
```

### Bước 2 — Chạy installer

Double-click vào file `.exe` vừa tải.

> Nếu Windows hiện cảnh báo **"Windows protected your PC"** → Nhấn **More info** → **Run anyway**
> (App chưa có chữ ký số, hoàn toàn an toàn)

### Bước 3 — Làm theo wizard

| Bước | Mô tả |
|---|---|
| Chọn thư mục cài | Mặc định: `C:\Program Files\PiperTTSTrainer` |
| Tạo shortcut Desktop | Tuỳ chọn (mặc định: không tích) |
| Nhấn **Install** | Chờ khoảng 10–30 giây |
| Nhấn **Finish** | Có thể tick "Khởi chạy ngay" |

### Bước 4 — Khởi chạy lần đầu

Mở **Piper TTS Trainer** từ Desktop hoặc Start Menu.

Lần đầu chạy, app sẽ tự tải và cài các thành phần cần thiết (cần Internet). Quá trình này chỉ xảy ra **một lần duy nhất**.

---

## 📖 Hướng dẫn sử dụng

### Tab ⚙️ Setup — Chuẩn bị môi trường

Thực hiện lần lượt từ **Bước 01 → Bước 10**:

1. Tạo virtual environment Python
2. Cài PyTorch (CPU hoặc CUDA)
3. Cài piper-train và các thư viện
4. Tải pretrained checkpoint từ HuggingFace
5. Kiểm tra môi trường sẵn sàng

> 💡 Chỉ cần làm Setup **một lần**. Lần sau mở app có thể dùng ngay.

---

### Tab 📦 Dataset — Chuẩn bị dữ liệu

Cấu trúc thư mục cần có:

```
project_dir/
├── wavs/
│   ├── audio_001.wav
│   ├── audio_002.wav
│   └── ...
└── metadata.csv
```

Định dạng file `metadata.csv`:

```
audio_001|Xin chào, đây là giọng nói tổng hợp tiếng Việt.
audio_002|Piper TTS hỗ trợ huấn luyện giọng nói tùy chỉnh.
```

> File audio phải là `.wav`, **mono**, sample rate **22050 Hz** hoặc **16000 Hz**.

---

### Tab 🚀 Train — Huấn luyện

Điền các thông tin:

| Trường | Ví dụ | Mô tả |
|---|---|---|
| Voice Name | `my_voice_vi` | Tên giọng nói |
| Dataset CSV | `D:\data\metadata.csv` | File danh sách audio |
| Audio Dir | `D:\data\wavs` | Thư mục chứa file wav |
| Checkpoint | *(chọn pretrained)* | File `.ckpt` khởi điểm |
| Batch Size | `6` | Giảm nếu thiếu RAM/VRAM |
| Max Epochs | `4000` | Số vòng huấn luyện tối đa |

Nhấn **▶ Bắt đầu Train** và theo dõi log. Checkpoint được lưu tự động mỗi vài epoch.

---

### Tab 📤 Export — Xuất model

1. Chọn file `.ckpt` tốt nhất từ danh sách
2. Nhấn **Export ONNX**
3. App tự tạo 2 file: `my_voice.onnx` và `my_voice.onnx.json`
4. Chuyển sang tab **Chạy Thử** để kiểm tra kết quả

---

### Tab 🔊 Chạy Thử — Kiểm tra giọng nói

1. Chọn file `.onnx` và `.onnx.json` vừa export
2. Nhập văn bản tiếng Việt vào ô input
3. Bật **Xử lý tiếng Việt** để tự động chuẩn hóa văn bản
4. Nhấn **Tổng hợp** → App phát audio và lưu file `test_output.wav`

---

## 🇻🇳 Xử lý văn bản tiếng Việt

App tự động chuẩn hóa văn bản trước khi tổng hợp:

| Input | Output |
|---|---|
| `250.000đ` | `hai trăm năm mươi nghìn đồng` |
| `15/3/2025` | `ngày mười lăm tháng ba năm hai nghìn không trăm hai mươi lăm` |
| `8h30` | `tám giờ ba mươi phút` |
| `12%` | `mười hai phần trăm` |
| `90km/h` | `chín mươi ki-lô-mét trên giờ` |
| `0912345678` | `không chín một hai ba bốn năm sáu bảy tám` |

---

## 🔔 Cập nhật

App tự động kiểm tra phiên bản mới khi khởi động. Khi có bản cập nhật, một hộp thoại sẽ hiện ra và hỏi bạn có muốn mở trang tải về không.

Bạn cũng có thể kiểm tra thủ công tại: [Releases](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases)

---

## ❓ Câu hỏi thường gặp

**Q: App báo lỗi "Python not found"?**
> Cài Python 3.10–3.12 từ [python.org](https://www.python.org/downloads/) và đảm bảo tick **"Add Python to PATH"** khi cài.

**Q: Train rất chậm?**
> Cài PyTorch với CUDA nếu bạn có GPU NVIDIA. Chọn đúng phiên bản CUDA trong tab Setup.

**Q: Checkpoint bị lỗi khi load?**
> App đã tích hợp sẵn patch `PosixPath → WindowsPath`. Nếu vẫn lỗi, thử dùng checkpoint từ đúng phiên bản piper-train.

**Q: File wav không được nhận dạng?**
> Kiểm tra file wav phải là **mono**, không phải stereo. Dùng Audacity để convert nếu cần.

---

## 📬 Liên hệ & Hỗ trợ

- 🐛 **Báo lỗi**: [GitHub Issues](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/issues)
- 💬 **Thảo luận**: [GitHub Discussions](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/discussions)

---

## 📄 Giấy phép

Phân phối theo giấy phép **MIT**. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

> ⚠️ Source code của dự án này **không được công khai**. Vui lòng không decompile, reverse engineer hoặc phân phối lại file EXE.

---

<div align="center">
Phát triển với ❤️ bởi <b>Văn Khải A.I Studio</b>
</div>
