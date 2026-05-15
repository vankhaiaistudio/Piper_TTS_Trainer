<div align="center">

<img src="assets/banner.png" alt="Piper TTS Trainer Banner" width="100%"/>

# Piper TTS Trainer

**Ứng dụng Windows hỗ trợ cài môi trường, huấn luyện, export ONNX và chạy thử giọng nói Piper TTS.**

Tối ưu cho workflow fine-tune giọng nói tiếng Việt, đồng thời hỗ trợ train từ số 0 và tiền xử lý văn bản tiếng Việt.

[![Version](https://img.shields.io/github/v/tag/vankhaiaistudio/Piper_TTS_Trainer?label=version&color=2563eb)](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4)](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab)](https://www.python.org/downloads/)
[![Piper](https://img.shields.io/badge/Piper-OHF--voice-10b981)](https://github.com/OHF-voice/piper1-gpl)

[**Tải bản mới nhất**](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)

</div>

---

## Tổng quan

Piper TTS Trainer giúp đưa toàn bộ quy trình huấn luyện Piper TTS trên Windows vào một giao diện duy nhất:

- chuẩn bị môi trường Python;
- cài PyTorch CPU/CUDA;
- tải và cấu hình Piper;
- chọn checkpoint pretrained;
- kiểm tra dataset;
- train hoặc fine-tune;
- export model sang ONNX;
- chạy thử giọng đọc ngay trong app.

Ứng dụng phù hợp với người muốn tạo hoặc tinh chỉnh giọng nói riêng từ dữ liệu `WAV + transcript`, đặc biệt cho tiếng Việt.

## Điểm nổi bật

| Tính năng | Mô tả |
|---|---|
| Setup theo từng bước | Tạo `.venv`, cài PyTorch, clone Piper, build extension, cài eSpeak-NG |
| Pretrained linh hoạt | Chọn model base có sẵn hoặc nhập link `.ckpt` và `config.json` tùy chỉnh |
| Kiểm tra dataset | Phát hiện file WAV bị thiếu, hỗ trợ sửa CSV 3 cột về 2 cột |
| Train / fine-tune | Hỗ trợ fine-tune từ checkpoint và train từ số 0 |
| Console gọn | Rút gọn log training, tô màu epoch, phần trăm, ETA và tốc độ |
| Checkpoint thông minh | Tự chọn checkpoint mới nhất, sort đúng `version_10`, `version_11`, ... |
| Export ONNX | Xuất `.onnx` và tạo `.onnx.json` đi kèm |
| Inference tích hợp | Nhập văn bản, tổng hợp giọng đọc và lưu `test_output.wav` |
| Tiền xử lý tiếng Việt | Chuẩn hóa số, ngày tháng, tiền tệ, phần trăm, đơn vị |
| Tự kiểm tra cập nhật | So sánh version local với GitHub khi khởi động |

## Yêu cầu hệ thống

| Thành phần | Tối thiểu | Khuyến nghị |
|---|---:|---:|
| Hệ điều hành | Windows 10 64-bit | Windows 11 64-bit |
| Python | 3.10+ | Python 3.11 |
| RAM | 8 GB | 16 GB+ |
| GPU | Không bắt buộc | NVIDIA CUDA |
| Ổ đĩa | Vài GB | 10 GB+ |

Lưu ý:

- Python nên được thêm vào `PATH`.
- Cần Internet ở lần setup đầu tiên.
- Train bằng CPU vẫn chạy được nhưng chậm hơn rất nhiều so với GPU NVIDIA.

## Cài đặt

Tải installer tại:

```text
https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest
```

Tên file thường có dạng:

```text
PiperTTSTrainer_vX.X_Setup.exe
```

Sau khi cài đặt, mở **Piper TTS Trainer** từ Start Menu hoặc shortcut Desktop.

Nếu Windows SmartScreen hiển thị cảnh báo, chọn:

```text
More info -> Run anyway
```

## Quy trình sử dụng

### 1. Tạo Project Dir

Trong tab **Cài Đặt (Setup)**:

1. Chọn thư mục cha.
2. Nhập tên thư mục dự án.
3. Bấm **Tạo thư mục dự án**.

Project Dir là nơi app lưu `.venv`, repo Piper, checkpoint, ONNX và audio test.

### 2. Cài môi trường

Chạy các bước setup theo thứ tự:

| Bước | Nội dung |
|---|---|
| A | Tạo `.venv`, nâng cấp `pip`, cài công cụ nền |
| B | Cài PyTorch CPU/CUDA |
| C | Cài Visual Studio Build Tools |
| D | Clone Piper, cài `piper[train]`, build monotonic align, cài `onnxscript` |
| E | Tải model base pretrained |
| F | Cài hoặc tìm eSpeak-NG và build eSpeak bridge |

Nếu fine-tune, hãy chọn model base ở khung **Chọn Giọng Pretrained** trước khi chạy bước E.

### 3. Chuẩn bị dataset

Dataset gồm một thư mục WAV và một file metadata CSV.

```text
dataset/
|-- wavs/
|   |-- audio_001.wav
|   |-- audio_002.wav
|   `-- ...
`-- metadata.csv
```

Định dạng `metadata.csv`:

```text
audio_001|Xin chào, tôi là Khải.
audio_002|Hôm nay thời tiết rất đẹp.
```

Quy tắc quan trọng:

- Cột đầu là tên file, không cần ghi `.wav`.
- Cột thứ hai là transcript.
- Transcript phải khớp sát với audio.
- WAV nên là mono, sạch noise, cùng sample rate.
- Mỗi file nên dài khoảng 2-12 giây.

Trong app có nút **Kiểm tra Dữ Liệu** để phát hiện file WAV bị thiếu.

### 4. Huấn luyện

Trong tab **Data & Train**:

1. Chọn `Metadata CSV`.
2. Chọn `Audio Dir`.
3. Chọn ngôn ngữ eSpeak, ví dụ `Vietnamese (vi)`.
4. Chọn chế độ train.
5. Bấm **BẮT ĐẦU TRAIN**.

| Chế độ | Khi nên dùng |
|---|---|
| Fine-tune từ checkpoint | Khuyến nghị cho hầu hết trường hợp, đặc biệt khi dữ liệu chưa lớn |
| Train từ số 0 | Dành cho dataset lớn, sạch, muốn model học từ đầu |

Gợi ý dữ liệu:

- Test kỹ thuật: 30 phút đến 1 giờ audio.
- Sử dụng thực tế: vài giờ audio sạch.
- Chất lượng tốt hơn: 10 giờ+ một người nói, thu đồng nhất.

### 5. Export ONNX

Trong tab **Xuất Model (Export)**:

1. Bấm **Chọn Checkpoint Mới Nhất** hoặc chọn checkpoint trong danh sách.
2. Nhập tên model.
3. Bấm **XUẤT RA ONNX**.

Kết quả:

```text
<ten_model>.onnx
<ten_model>.onnx.json
```

### 6. Chạy thử

Trong tab **Chạy Thử (Inference)**:

1. Chọn file `.onnx`.
2. Chọn file `.onnx.json`.
3. Nhập văn bản.
4. Bật tiền xử lý tiếng Việt nếu cần.
5. Bấm **TỔNG HỢP GIỌNG ĐỌC**.

Audio test được lưu tại:

```text
Project Dir/test_output.wav
```

## Cấu trúc Project Dir

```text
Project Dir/
|-- .venv/
|-- piper1-gpl/
|   |-- pretrained-model.ckpt
|   |-- pretrained-model-cleaned.ckpt
|   `-- src/
|       `-- lightning_logs/
|           `-- version_N/
|               `-- checkpoints/
|-- <ten_model>.onnx
|-- <ten_model>.onnx.json
`-- test_output.wav
```

Checkpoint train nằm tại:

```text
Project Dir/piper1-gpl/src/lightning_logs/version_N/checkpoints/*.ckpt
```

App sort version theo số tự nhiên, nên `version_10` được xem là mới hơn `version_9`.

## Tiền xử lý tiếng Việt

`vn_text_processor.py` hỗ trợ chuẩn hóa văn bản trước khi tổng hợp.

| Input | Output ví dụ |
|---|---|
| `250.000đ` | `hai trăm năm mươi nghìn đồng` |
| `15/3/2025` | `ngày mười lăm tháng ba năm hai nghìn không trăm hai mươi lăm` |
| `8h30` | `tám giờ ba mươi phút` |
| `12%` | `mười hai phần trăm` |
| `90km/h` | `chín mươi ki-lô-mét trên giờ` |

Trong tab Inference, bấm **Xem trước chữ sau khi xử lý** để kiểm tra văn bản trước khi tạo audio.

## Sự cố thường gặp

### App báo không tìm thấy Python

Cài Python từ <https://www.python.org/downloads/> và tick **Add Python to PATH**.

### Train chậm

Cài PyTorch bản CUDA nếu máy có GPU NVIDIA. Nếu thiếu VRAM, giảm `Batch Size`.

### Không thấy checkpoint mới nhất

Vào tab Export và bấm **Làm Mới Danh Sách**. App đã xử lý đúng các thư mục `version_10`, `version_11`, ...

### WAV không khớp CSV

Tên trong CSV không cần `.wav`, nhưng file thật trong `Audio Dir` phải tồn tại và đúng tên.

### Stop train hiện lỗi multiprocessing

Khi dừng đúng lúc Python đang spawn worker, multiprocessing có thể in traceback phụ. App đã xử lý để Stop thủ công không bị coi là lỗi train thật.

## Cập nhật

App tự đọc `version.txt` local và so với `version.txt` trên GitHub khi khởi động. Nếu có bản mới, app sẽ hỏi trước khi mở trang tải.

Trang tải bản mới:

```text
https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest
```

## Ghi chú

Chất lượng giọng phụ thuộc vào dataset, transcript, sample rate, checkpoint base, cấu hình train và thời gian train.

Phát triển bởi **Văn Khải A.I Studio**.
