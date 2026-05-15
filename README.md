<div align="center">

<img src="assets/banner.png" alt="Piper TTS Trainer Banner" width="100%"/>

# Piper TTS Trainer

GUI Windows để cài môi trường, train, export ONNX và chạy thử giọng nói Piper TTS.

Tối ưu cho fine-tune giọng nói tiếng Việt, có hỗ trợ train từ số 0 và tiền xử lý văn bản tiếng Việt.

[![Version](https://img.shields.io/github/v/tag/vankhaiaistudio/Piper_TTS_Trainer?label=version&color=2563eb)](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078d4)](https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab)](https://www.python.org/downloads/)
[![Piper](https://img.shields.io/badge/Piper-OHF--voice-10b981)](https://github.com/OHF-voice/piper1-gpl)

**Tải bản mới nhất:**  
<https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest>

</div>

---

## Giới thiệu

Piper TTS Trainer là công cụ đồ họa giúp đơn giản hóa workflow train giọng nói với Piper TTS trên Windows. App gom các bước thường phải làm thủ công như tạo môi trường Python, cài PyTorch, clone Piper, tải checkpoint pretrained, kiểm tra dataset, train, export ONNX và chạy thử audio vào một giao diện duy nhất.

Ứng dụng phù hợp cho người muốn fine-tune một giọng nói riêng từ dữ liệu WAV + transcript, đặc biệt với tiếng Việt.

## Tính năng

| Nhóm | Nội dung |
|---|---|
| Setup tự động | Tạo `.venv`, cài PyTorch CPU/CUDA, clone `piper1-gpl`, cài `piper[train]`, build extension |
| Pretrained model | Chọn model base có sẵn hoặc nhập link `.ckpt` và `config.json` tùy chỉnh |
| Dataset | Chọn CSV + audio dir, kiểm tra file WAV bị thiếu, sửa CSV 3 cột về 2 cột |
| Training | Fine-tune từ checkpoint hoặc train từ số 0 |
| Console | Log training realtime, rút gọn progress bar, tô màu epoch/phần trăm/ETA/tốc độ |
| Checkpoint | Tự tìm checkpoint mới nhất, sort đúng `version_10`, `version_11`, ... |
| Export | Xuất checkpoint sang `.onnx` và tạo file `.onnx.json` đi kèm |
| Inference | Chạy thử giọng đọc trong app và lưu `test_output.wav` |
| Tiếng Việt | Chuẩn hóa số, ngày tháng, tiền tệ, phần trăm, đơn vị... trước khi synthesize |
| Cập nhật | Tự kiểm tra phiên bản mới khi khởi động |

## Yêu cầu hệ thống

| Thành phần | Tối thiểu | Khuyến nghị |
|---|---:|---:|
| Hệ điều hành | Windows 10 64-bit | Windows 11 64-bit |
| Python | 3.10+ | Python 3.11 |
| RAM | 8 GB | 16 GB+ |
| GPU | Không bắt buộc | NVIDIA CUDA để train nhanh hơn |
| Ổ đĩa | Vài GB | 10 GB+ nếu train nhiều version |

Lưu ý:

- Python nên được thêm vào `PATH`.
- Cần Internet để tải PyTorch, Piper, checkpoint, eSpeak-NG và Visual Studio Build Tools.
- Train bằng CPU vẫn chạy được nhưng rất chậm so với GPU NVIDIA.

## Cài đặt

1. Vào trang Releases:

```text
https://github.com/vankhaiaistudio/Piper_TTS_Trainer/releases/latest
```

2. Tải file installer:

```text
PiperTTSTrainer_vX.X_Setup.exe
```

3. Chạy installer và làm theo hướng dẫn.

4. Nếu Windows SmartScreen hiện cảnh báo, chọn:

```text
More info -> Run anyway
```

5. Mở `Piper TTS Trainer` từ Start Menu hoặc shortcut Desktop.

## Hướng dẫn nhanh

### 1. Tạo project

Trong tab `Cài Đặt (Setup)`:

1. Chọn thư mục cha.
2. Nhập tên thư mục dự án.
3. Bấm `Tạo thư mục dự án`.

App sẽ tạo `Project Dir` để chứa `.venv`, repo Piper, checkpoint, ONNX và file test audio.

### 2. Cài môi trường

Trong tab `Cài Đặt (Setup)`, chạy lần lượt:

| Bước | Nội dung |
|---|---|
| A | Tạo `.venv`, nâng cấp `pip`, cài công cụ nền |
| B | Cài PyTorch CPU/CUDA |
| C | Cài Visual Studio Build Tools |
| D | Clone Piper, cài `piper[train]`, build monotonic align, cài `onnxscript` |
| E | Tải model base pretrained |
| F | Cài/tìm eSpeak-NG và build eSpeak bridge |

Nếu muốn fine-tune, hãy chọn giọng ở khung `Chọn Giọng Pretrained` trước khi chạy bước E.

### 3. Chuẩn bị dataset

Dataset cần một thư mục WAV và một file CSV.

Ví dụ:

```text
dataset/
|-- wavs/
|   |-- audio_001.wav
|   |-- audio_002.wav
|   `-- ...
`-- metadata.csv
```

File `metadata.csv`:

```text
audio_001|Xin chào, tôi là Khải.
audio_002|Hôm nay thời tiết rất đẹp.
```

Quy tắc:

- Cột đầu là tên file, không cần ghi `.wav`.
- Cột thứ hai là transcript.
- Transcript nên khớp chính xác với audio.
- WAV nên là mono, sạch noise, cùng sample rate.
- Mỗi file nên dài khoảng 2-12 giây.

Trong app có nút `Kiểm tra Dữ Liệu` để tìm file WAV bị thiếu.

### 4. Train

Trong tab `Data & Train`:

1. Chọn `Metadata CSV`.
2. Chọn `Audio Dir`.
3. Chọn ngôn ngữ eSpeak, ví dụ `Vietnamese (vi)`.
4. Chọn chế độ train.
5. Bấm `BẮT ĐẦU TRAIN`.

Có 2 chế độ:

| Chế độ | Khi nào dùng |
|---|---|
| Fine-tune từ checkpoint | Nên dùng cho hầu hết trường hợp, đặc biệt khi dataset chưa lớn |
| Train từ số 0 | Dùng khi có dataset lớn, sạch, muốn model học từ đầu |

Gợi ý dữ liệu:

- Test kỹ thuật: 30 phút đến 1 giờ audio.
- Dùng thực tế: vài giờ audio sạch.
- Tốt hơn: 10 giờ+ một người nói, thu đồng nhất.

### 5. Export ONNX

Trong tab `Xuất Model (Export)`:

1. Bấm `Chọn Checkpoint Mới Nhất` hoặc chọn checkpoint trong danh sách.
2. Nhập tên model.
3. Bấm `XUẤT RA ONNX`.

App tạo 2 file trong `Project Dir`:

```text
<ten_model>.onnx
<ten_model>.onnx.json
```

### 6. Chạy thử

Trong tab `Chạy Thử (Inference)`:

1. Chọn file `.onnx`.
2. Chọn file `.onnx.json`.
3. Nhập văn bản.
4. Bật tiền xử lý tiếng Việt nếu cần.
5. Bấm `TỔNG HỢP GIỌNG ĐỌC`.

File audio test được lưu tại:

```text
Project Dir/test_output.wav
```

## Cấu trúc project do app tạo

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

Checkpoint train nằm trong:

```text
Project Dir/piper1-gpl/src/lightning_logs/version_N/checkpoints/*.ckpt
```

App sort version theo số tự nhiên, nên `version_10` mới hơn `version_9`.

## Tiền xử lý tiếng Việt

File `vn_text_processor.py` hỗ trợ chuẩn hóa văn bản trước khi tổng hợp.

| Input | Output ví dụ |
|---|---|
| `250.000đ` | `hai trăm năm mươi nghìn đồng` |
| `15/3/2025` | `ngày mười lăm tháng ba năm hai nghìn không trăm hai mươi lăm` |
| `8h30` | `tám giờ ba mươi phút` |
| `12%` | `mười hai phần trăm` |
| `90km/h` | `chín mươi ki-lô-mét trên giờ` |

Bấm `Xem trước chữ sau khi xử lý` trong tab Inference để kiểm tra text trước khi tạo audio.

## Sự cố thường gặp

### App báo không tìm thấy Python

Cài Python từ <https://www.python.org/downloads/> và tick `Add Python to PATH`.

### Train chậm

Cài PyTorch bản CUDA nếu máy có GPU NVIDIA. Nếu bị thiếu VRAM, giảm `Batch Size`.

### Không thấy checkpoint mới nhất

Vào tab Export và bấm `Làm Mới Danh Sách`. App đã xử lý đúng các thư mục `version_10`, `version_11`, ...

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

Piper TTS Trainer là công cụ hỗ trợ workflow huấn luyện Piper. Chất lượng giọng phụ thuộc vào dataset, transcript, sample rate, checkpoint base, cấu hình train và thời gian train.

Phát triển bởi Văn Khải A.I Studio.

