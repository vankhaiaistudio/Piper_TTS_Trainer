import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading, subprocess, sys, os, shutil, wave, time, pathlib
from pathlib import Path


# ── FIX PYINSTALLER: sys.executable trỏ vào file .exe, không phải Python ──
# Hàm này tìm Python thật trong PATH để dùng cho venv và pip.
def _find_system_python() -> str:
    """
    Khi chạy từ file EXE (PyInstaller frozen), sys.executable là chính EXE đó.
    Gọi nó với '-m venv' sẽ mở thêm cửa sổ app mới thay vì tạo venv.
    Hàm này tìm python.exe thật trong PATH của hệ thống.
    """
    if getattr(sys, 'frozen', False):
        for candidate in ('python.exe', 'python3.exe', 'python', 'python3'):
            found = shutil.which(candidate)
            if found:
                return found
        # Fallback: thử đọc từ registry HKLM nếu PATH không có
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Python\PythonCore")
            ver, _ = winreg.EnumKey(key, 0), None
            py_key = winreg.OpenKey(key, ver + r"\InstallPath")
            install_dir, _ = winreg.QueryValueEx(py_key, "ExecutablePath")
            if Path(install_dir).exists():
                return str(install_dir)
        except Exception:
            pass
        return 'python'   # last resort — user must have Python in PATH
    # Không phải EXE → dùng Python đang chạy script này (bình thường)
    return sys.executable

# ── CONFIG FILE: lưu cạnh file EXE (hoặc cạnh .py khi dev) ──────
def _config_path() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / "piper_trainer_config.json"
    return Path(__file__).parent / "piper_trainer_config.json"

def _load_config() -> dict:
    try:
        import json
        p = _config_path()
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _save_config(data: dict):
    try:
        import json
        _config_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


# ── GIAO DIỆN LIGHT THEME CHUYÊN NGHIỆP ────────────────────────
BG     = "#e5e7eb"   # Nền chính (Xám nhạt)
PANEL  = "#f3f4f6"   # Nền các panel (Xám trắng)
CARD   = "#ffffff"   # Nền thẻ nội dung (Trắng tinh)
INPUT  = "#f8fafc"   # Ô nhập liệu (Sáng)
ACCENT = "#2563eb"   # Xanh dương đậm chuyên nghiệp
TEAL   = "#059669"   # Xanh lá cây (Thành công)
MAIN   = "#111827"   # Text chính (Đen/Xám đậm)
DIM    = "#4b5563"   # Text phụ (Xám vừa)
WARN   = "#d97706"   # Vàng/Cam cảnh báo
ERR    = "#dc2626"   # Đỏ lỗi
BORDER = "#d1d5db"   # Viền xám

# Font chữ hiện đại
FT  = ("Segoe UI", 18, "bold")
FH  = ("Segoe UI", 11, "bold")
FB  = ("Segoe UI", 10)
FS  = ("Segoe UI", 9)
FL  = ("Consolas", 10)
FN  = ("Segoe UI", 10, "bold")


def B(parent, text, cmd, color=ACCENT, w=16, **kw):
    """Nút bấm với hiệu ứng hover"""
    hover_color = "#1d4ed8" if color == ACCENT else color
    b = tk.Button(parent, text=text, command=cmd, bg=color, fg="#ffffff",
                  relief="flat", font=FN, cursor="hand2", padx=8, pady=4,
                  width=w, bd=0, activebackground=hover_color, activeforeground="#ffffff", **kw)
    b.bind("<Enter>", lambda e: b.config(bg=hover_color))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b

def E(parent, var, w=38):
    return tk.Entry(parent, textvariable=var, width=w, bg=INPUT, fg=MAIN,
                    insertbackground=MAIN, relief="flat", font=FB,
                    highlightthickness=1, highlightcolor=ACCENT,
                    highlightbackground=BORDER)

def L(parent, text, fg=MAIN, font=FS, **kw):
    if "w" in kw:
        kw["width"] = kw.pop("w")
    return tk.Label(parent, text=text, bg=CARD, fg=fg, font=font, **kw)

def sec(parent, text, bg=PANEL):
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=text, bg=bg, fg=ACCENT, font=FH).pack(side="left")
    tk.Frame(f, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=8, pady=7)
    return f

def card(parent, **kw):
    return tk.Frame(parent, bg=CARD, padx=12, pady=10, highlightthickness=1, highlightbackground=BORDER, **kw)

def row(parent, bg=CARD):
    return tk.Frame(parent, bg=bg)


# ════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Piper TTS Trainer v3.0 - by Văn Khải A.I Studio")
        self.geometry("1350x900")
        self.minsize(1200, 750)
        self.configure(bg=BG)

        # ── Biến trạng thái ──
        self.project_dir  = tk.StringVar(value=str(Path(__file__).parent))
        self.voice_name   = tk.StringVar(value="my_voice")
        self.espeak_lang  = tk.StringVar(value="vi")
        self.sample_rate  = tk.StringVar(value="22050")
        self.dataset_csv  = tk.StringVar()
        self.audio_dir    = tk.StringVar()
        self.batch_size   = tk.StringVar(value="6")
        self.max_epochs   = tk.StringVar(value="4000")
        self.ckpt_path    = tk.StringVar()
        self.export_ckpt  = tk.StringVar()
        self.export_name  = tk.StringVar(value="my_voice")
        self.infer_model  = tk.StringVar()
        self.infer_config = tk.StringVar()
        self.length_scale = tk.StringVar(value="1.0")
        self.noise_scale  = tk.StringVar(value="0.667")
        self.noise_w      = tk.StringVar(value="1.0")
        self.venv_status  = tk.StringVar(value="Chưa kiểm tra")
        self.use_vn_proc  = tk.BooleanVar(value=True)
        self._ckpt_url    = tk.StringVar(
            value="https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/hfc_male/medium/epoch%3D2785-step%3D2128064.ckpt")
        self._cfg_url     = tk.StringVar(
            value="https://huggingface.co/datasets/rhasspy/piper-checkpoints/resolve/main/en/en_US/hfc_male/medium/config.json")
        self._pkg_var     = tk.StringVar()
        self._proc        = None

        self._step_sv  = {}
        self._step_lbl = {}
        self._scroll_canvases = []   # danh sách canvas cuộn — dùng bởi _on_global_scroll

        # ── Nạp config đã lưu (nếu có) ──
        self._load_saved_config()

        self._build_ui()
        self.after(600, self._check_venv)
        self.protocol("WM_DELETE_WINDOW", self._on_close)  # lưu config khi tắt

    # ════════════════════════════════════════════════════════
    # CẤU TRÚC GIAO DIỆN CHÍNH
    # ════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── Header ──
        top = tk.Frame(self, bg=BG, pady=10)
        top.pack(fill="x", padx=16)
        
        title_frame = tk.Frame(top, bg=BG)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="PIPER TTS TRAINER", bg=BG, fg=ACCENT, font=FT).pack(side="left")
        tk.Label(title_frame, text=" v3.0", bg=BG, fg=DIM, font=FB).pack(side="left", pady=4)
        tk.Label(title_frame, text="  |  © Văn Khải A.I Studio", bg=BG, fg=TEAL, font=FH).pack(side="left", pady=4, padx=10)
        
        self._vbadge = tk.Label(top, textvariable=self.venv_status, bg=CARD, fg=WARN, font=FS, padx=8, pady=4, relief="solid", bd=1)
        self._vbadge.pack(side="right")

        # ── Tabs ──
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("P.TNotebook", background=BG, borderwidth=0)
        style.configure("P.TNotebook.Tab", background="#d1d5db", foreground=DIM, font=FN, padding=[20, 8], borderwidth=0)
        style.map("P.TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", ACCENT)])
        
        nb = ttk.Notebook(self, style="P.TNotebook")
        nb.pack(fill="both", expand=True, padx=10)

        for name, builder in [
            (" ⚙ Cài Đặt (Setup) ", self._tab_setup),
            (" 💾 Data & Train ", self._tab_data_and_train),
            (" 📦 Xuất Model (Export) ", self._tab_export),
            (" 🎙️ Chạy Thử (Inference) ", self._tab_inference),
            (" 📖 Hướng Dẫn Sử Dụng ", self._tab_help),
        ]:
            f = tk.Frame(nb, bg=PANEL)
            nb.add(f, text=name)
            builder(f)

        # ── Console ──
        cf = tk.Frame(self, bg=BG)
        cf.pack(fill="both", expand=False, padx=10, pady=(5, 10))

        ch = tk.Frame(cf, bg=BG)
        ch.pack(fill="x")
        tk.Label(ch, text="■ SYSTEM CONSOLE", bg=BG, fg=DIM, font=FN).pack(side="left")
        B(ch, "Dừng (Stop)", self._stop, color=ERR, w=12).pack(side="right", padx=2)
        B(ch, "Xóa Log", self._clear_log, color="#64748b", w=10).pack(side="right", padx=2)

        self.log_box = scrolledtext.ScrolledText(
            cf, height=14, bg="#1e293b", fg="#f8fafc", font=FL,
            relief="flat", bd=0, highlightthickness=1, highlightbackground=BORDER)
        self.log_box.pack(fill="both", expand=True, pady=(5, 0))
        for t, c in [("ok", "#34d399"), ("err", "#f87171"), ("warn", "#fbbf24"), ("info", "#60a5fa"), ("dim", "#94a3b8")]:
            self.log_box.tag_config(t, foreground=c)

        self.bind_all("<MouseWheel>", self._on_global_scroll)

        self.log("Piper TTS Trainer v3.0 - Văn Khải A.I Studio khởi động thành công.", "ok")
        self.log("▶ Chuyển sang Tab [Cài Đặt] để bắt đầu quy trình.", "info")

    # ════════════════════════════════════════════════════════
    # TAB 1: SETUP (Chia 2 cột & Cột phải rộng hơn)
    # ════════════════════════════════════════════════════════
    def _tab_setup(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal", bg=BORDER, bd=0, sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(paned, bg=PANEL)
        right = tk.Frame(paned, bg=PANEL)
        paned.add(left, minsize=650, stretch="always")
        paned.add(right, minsize=400, stretch="never")  # Đảm bảo cột phải rộng hơn

        # ====== CỘT TRÁI ======
        sec(left, "1. Thư mục lưu trữ dự án").pack(fill="x", pady=(0, 5))
        cd = card(left); cd.pack(fill="x", pady=(0, 10))
        rd = row(cd); rd.pack(fill="x")
        L(rd, "Project Dir:", w=12, anchor="e").pack(side="left")
        E(rd, self.project_dir, w=45).pack(side="left", padx=10)
        B(rd, "Chọn", lambda: self._browse_dir(self.project_dir), w=8).pack(side="left")
        rd2 = row(cd); rd2.pack(anchor="w", pady=(8, 0))
        B(rd2, "Tạo thư mục", self._mk_project_dir, w=16).pack(side="left", padx=(0, 6))
        L(cd, "Toàn bộ dữ liệu (venv, repo, model) sẽ được lưu tại đây.", fg=DIM).pack(anchor="w", pady=(8, 0))

        sec(left, "2. Quy trình Cài đặt (Chia 2 Cột)").pack(fill="x", pady=(10, 5))

        STEPS = [
            ("A", "Môi trường & Công cụ cơ bản", "Tạo .venv + nâng cấp pip, scikit-build", self._step_env_and_tools),
            ("B", "Cài PyTorch (CUDA/CPU)", "Tải ~2.5GB — bỏ qua nếu đã có", self._step_install_torch),
            ("C", "Visual Studio Build Tools", "Cần quyền Admin — mở UAC tự động", self._step_install_vs),
            ("D", "Piper + Monotonic + Onnx", "Clone repo, cài piper[train], build extension", self._step_piper_all),
            ("E", "Tải Model Base (Pretrained)", "Download checkpoint từ HuggingFace", self._step_download_ckpt),
            ("F", "Build eSpeak Bridge", "Compile espeakbridge.pyd (CMake + VS Tools)", self._step_build_espeak),
        ]

        scf = tk.Frame(left, bg=PANEL)
        scf.pack(fill="both", expand=True)
        canvas = tk.Canvas(scf, bg=PANEL, highlightthickness=0)
        vsb = ttk.Scrollbar(scf, orient="vertical", command=canvas.yview)
        
        steps_f = tk.Frame(canvas, bg=PANEL)
        steps_f.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=steps_f, anchor="nw", width=canvas.winfo_width())
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_withtag("all")[0], width=e.width))
        
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._scroll_canvases.append(canvas)

        # Khai báo lưới 2 cột
        steps_f.columnconfigure(0, weight=1, uniform="col")
        steps_f.columnconfigure(1, weight=1, uniform="col")

        for i, (sid, title, desc, fn) in enumerate(STEPS):
            r = i // 2
            c = i % 2
            sv = tk.StringVar(value="○ Chưa chạy")
            self._step_sv[sid] = sv

            sf = card(steps_f)
            sf.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

            top_f = tk.Frame(sf, bg=CARD)
            top_f.pack(fill="x", expand=True)

            tk.Label(top_f, text=sid, bg=ACCENT, fg="#fff", font=("Segoe UI", 11, "bold"), width=3, pady=2).pack(side="left", anchor="n", padx=(0, 10))
            
            info_f = tk.Frame(top_f, bg=CARD)
            info_f.pack(side="left", fill="both", expand=True)
            L(info_f, title, font=FN, fg=MAIN, anchor="w", justify="left").pack(fill="x")
            L(info_f, desc, fg=DIM, anchor="w", justify="left").pack(fill="x", pady=(2,0))

            bot_f = tk.Frame(sf, bg=CARD)
            bot_f.pack(fill="x", side="bottom", pady=(10, 0))

            lbl = L(bot_f, "", fg=DIM, anchor="w")
            lbl.config(textvariable=sv)
            lbl.pack(side="left", anchor="center")
            self._step_lbl[sid] = lbl

            B(bot_f, "▶ Chạy", lambda c=fn, s=sid: self._run_step(s, c), w=10).pack(side="right")

        # ====== CỘT PHẢI ======
        right_inner = tk.Frame(right, bg=PANEL)
        right_inner.pack(fill="both", expand=True, padx=(10, 0))

        # ── AUTO SETUP ──
        sec(right_inner, "🚀 Tự Động Cài Đặt").pack(fill="x", pady=(0, 5))
        ca = card(right_inner); ca.pack(fill="x", pady=(0, 10))
        L(ca, "Chạy tất cả các bước A→F tự động theo thứ tự.\n"
              "Bước C (VS Build Tools) sẽ hiện hộp thoại UAC — cần xác nhận thủ công.", fg=DIM, justify="left").pack(anchor="w", pady=(0, 8))
        self._auto_progress = tk.StringVar(value="")
        self._auto_lbl = tk.Label(ca, textvariable=self._auto_progress,
                                  bg=CARD, fg=TEAL, font=FN, anchor="w", justify="left")
        self._auto_lbl.pack(anchor="w", pady=(0, 6))
        auto_br = row(ca); auto_br.pack(anchor="w")
        self._btn_auto = B(auto_br, "⚡ AUTO SETUP ALL", self._auto_setup,
                           color=TEAL, w=22)
        self._btn_auto.pack(side="left", padx=(0, 6))
        B(auto_br, "Dừng", self._stop, color=ERR, w=8).pack(side="left")

        sec(right_inner, "Công cụ bổ trợ").pack(fill="x", pady=(10, 5))
        
        cv = card(right_inner); cv.pack(fill="x", pady=(0, 10))
        L(cv, "Quản lý môi trường .venv", font=FN).pack(anchor="w", pady=(0, 5))
        br = row(cv); br.pack(anchor="w")
        B(br, "Kiểm tra", self._check_venv, w=12).pack(side="left", padx=(0, 5))
        B(br, "Xóa .venv", self._delete_venv, color=ERR, w=12).pack(side="left")

        cp = card(right_inner); cp.pack(fill="x", pady=(0, 10))
        L(cp, "Cài thư viện thủ công", font=FN).pack(anchor="w", pady=(0, 5))
        pr = row(cp); pr.pack(fill="x")
        E(pr, self._pkg_var, w=22).pack(side="left", padx=(0, 5), fill="x", expand=True)
        B(pr, "Cài (pip)", self._pip_custom, w=8).pack(side="right")

        cu = card(right_inner); cu.pack(fill="x", pady=(0, 10))
        L(cu, "Cấu hình Checkpoint URL", font=FN).pack(anchor="w", pady=(0, 5))
        E(cu, self._ckpt_url, w=30).pack(fill="x", pady=2)
        E(cu, self._cfg_url, w=30).pack(fill="x", pady=2)

        cp2 = card(right_inner); cp2.pack(fill="x")
        L(cp2, "Trạng thái Model Base", font=FN).pack(anchor="w", pady=(0, 5))
        self._pre_lbl = tk.Label(cp2, text="...", bg=CARD, fg=DIM, font=FS, wraplength=280, justify="left")
        self._pre_lbl.pack(anchor="w", pady=(0, 6))
        B(cp2, "Dùng model này để Train", self._pick_pretrained, w=26).pack(anchor="w")
        
        self.after(800, self._refresh_pre_label)

    # ════════════════════════════════════════════════════════
    # TAB 2: DATA & TRAIN
    # ════════════════════════════════════════════════════════
    def _tab_data_and_train(self, parent):
        paned = tk.PanedWindow(parent, orient="horizontal", bg=BORDER, bd=0, sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(paned, bg=PANEL)
        right = tk.Frame(paned, bg=PANEL)
        paned.add(left, minsize=450, stretch="always")
        paned.add(right, minsize=550, stretch="always")

        # ===== PHẦN TRÁI: DATASET =====
        sec(left, "1. Cấu hình Dữ Liệu (Dataset)").pack(fill="x", pady=(0, 5))
        c1 = card(left); c1.pack(fill="x", pady=5)
        
        for ltext, var, tip in [
            ("Tên Giọng (Voice):", self.voice_name, ""),
            ("Ngôn ngữ (espeak):", self.espeak_lang, "vi, en..."),
            ("Sample Rate:", self.sample_rate, "22050"),
        ]:
            r = row(c1); r.pack(fill="x", pady=4)
            L(r, ltext, w=16, anchor="e").pack(side="left")
            E(r, var, w=15).pack(side="left", padx=10)
            if tip: L(r, tip, fg=DIM).pack(side="left")

        c2 = card(left); c2.pack(fill="x", pady=5)
        for ltext, var, ftypes in [
            ("Metadata CSV:", self.dataset_csv, [("CSV", "*.csv"), ("All", "*.*")]),
            ("Audio Dir:", self.audio_dir, None),
        ]:
            r = row(c2); r.pack(fill="x", pady=4)
            L(r, ltext, w=14, anchor="e").pack(side="left")
            E(r, var, w=20).pack(side="left", padx=10, fill="x", expand=True)
            if ftypes:
                B(r, "Chọn", lambda v=var, f=ftypes: self._browse_file(v, f), w=8).pack(side="right")
            else:
                B(r, "Chọn", lambda v=var: self._browse_dir(v), w=8).pack(side="right")

        br_data = row(left, bg=PANEL); br_data.pack(anchor="w", pady=5, fill="x")
        B(br_data, "Kiểm tra Dữ Liệu", self._validate, w=18).pack(side="left")
        B(br_data, "Fix CSV (3 cột -> 2 cột)", self._fix_csv, w=22).pack(side="right")
        
        tip_frame = card(left)
        tip_frame.pack(fill="x", pady=10)
        L(tip_frame, "Format CSV yêu cầu: ten_file|transcript", font=FN).pack(anchor="w")
        L(tip_frame, "Ví dụ: audio001|Xin chào tôi tên là Khải\nKhông cần ghi đuôi .wav trong file csv.", fg=DIM, justify="left").pack(anchor="w", pady=5)

        # ===== PHẦN PHẢI: TRAIN =====
        sec(right, "2. Thiết lập Huấn Luyện (Train)").pack(fill="x", pady=(0, 5), padx=(10,0))
        right_inner = tk.Frame(right, bg=PANEL)
        right_inner.pack(fill="both", expand=True, padx=(10,0))

        c3 = card(right_inner); c3.pack(fill="x", pady=5)
        L(c3, "Checkpoint đầu vào:", font=FN).pack(anchor="w", pady=(0, 5))
        r3 = row(c3); r3.pack(fill="x")
        E(r3, self.ckpt_path, w=40).pack(side="left", padx=(0, 10), fill="x", expand=True)
        B(r3, "Chọn file", lambda: self._browse_file(self.ckpt_path, [("Checkpoint", "*.ckpt")]), w=10).pack(side="right")
        
        btn_row = row(c3); btn_row.pack(anchor="w", pady=(10, 0))
        B(btn_row, "Dùng Pretrained", self._pick_pretrained, w=18, color="#64748b").pack(side="left", padx=(0, 8))
        B(btn_row, "Dùng Checkpoint Mới Nhất", self._pick_latest_ckpt, w=24, color="#64748b").pack(side="left")

        c4 = card(right_inner); c4.pack(fill="x", pady=5)
        r4a = row(c4); r4a.pack(fill="x", pady=4)
        L(r4a, "Batch Size:", w=12, anchor="e").pack(side="left")
        E(r4a, self.batch_size, w=10).pack(side="left", padx=10)
        L(r4a, "(8 cho VGA 4GB, 16 cho VGA 8GB)", fg=DIM).pack(side="left")

        r4b = row(c4); r4b.pack(fill="x", pady=4)
        L(r4b, "Max Epochs:", w=12, anchor="e").pack(side="left")
        E(r4b, self.max_epochs, w=10).pack(side="left", padx=10)
        L(r4b, "(Số vòng lặp tối đa)", fg=DIM).pack(side="left")

        c5 = card(right_inner); c5.pack(fill="both", expand=True, pady=5)
        L(c5, "Preview Lệnh:", font=FN).pack(anchor="w", pady=(0, 5))
        self._cmd_box = tk.Text(c5, height=5, bg=INPUT, fg=MAIN, font=FL, relief="flat", bd=0, wrap="word", highlightthickness=1, highlightbackground=BORDER)
        self._cmd_box.pack(fill="both", expand=True, padx=2, pady=2)
        
        br_train = row(c5); br_train.pack(anchor="e", pady=(10, 0), fill="x")
        B(br_train, "Refresh Preview", self._preview_cmd, w=16, color="#64748b").pack(side="left")
        B(br_train, "BẮT ĐẦU TRAIN", self._start_train, w=20, color=TEAL).pack(side="right")

        self.after(500, self._preview_cmd)

    # ════════════════════════════════════════════════════════
    # TAB 3: EXPORT
    # ════════════════════════════════════════════════════════
    def _tab_export(self, parent):
        left  = tk.Frame(parent, bg=PANEL)
        right = tk.Frame(parent, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        sec(left, "Chọn Checkpoint để xuất").pack(fill="x", pady=(0, 5))
        c = card(left); c.pack(fill="x", pady=5)
        r = row(c); r.pack(fill="x", pady=5)
        L(r, "File .ckpt:", w=12, anchor="e").pack(side="left")
        E(r, self.export_ckpt, w=35).pack(side="left", padx=10)
        B(r, "Chọn", lambda: self._browse_file(self.export_ckpt, [("Checkpoint", "*.ckpt")]), w=8).pack(side="left")
        
        r2 = row(c); r2.pack(fill="x", pady=5)
        L(r2, "Tên Model:", w=12, anchor="e").pack(side="left")
        E(r2, self.export_name, w=25).pack(side="left", padx=10)
        L(r2, ".onnx").pack(side="left")
        
        br = row(c); br.pack(anchor="w", pady=(10, 0))
        B(br, "Chọn Checkpoint Mới Nhất", self._pick_latest_for_export, w=24, color="#64748b").pack(side="left", padx=(0, 10))
        B(br, "XUẤT RA ONNX", self._export, color=ACCENT, w=18).pack(side="left")

        sec(left, "Danh sách Checkpoint hiện có").pack(fill="x", pady=(20, 5))
        c2 = card(left); c2.pack(fill="both", expand=True, pady=5)
        lf = tk.Frame(c2, bg=CARD); lf.pack(fill="both", expand=True)
        
        self._exp_lb = tk.Listbox(lf, bg=INPUT, fg=MAIN, font=FS, relief="flat", selectbackground=ACCENT, selectforeground="#ffffff", highlightthickness=1, highlightbackground=BORDER)
        sb3 = ttk.Scrollbar(lf, orient="vertical", command=self._exp_lb.yview)
        self._exp_lb.config(yscrollcommand=sb3.set)
        self._exp_lb.pack(side="left", fill="both", expand=True)
        sb3.pack(side="right", fill="y")
        self._exp_lb.bind("<Double-Button-1>", self._sel_exp)
        
        br2 = row(c2); br2.pack(anchor="w", pady=(10, 0))
        B(br2, "Làm Mới Danh Sách", self._refresh_export_list, w=18, color="#64748b").pack(side="left", padx=(0, 10))
        B(br2, "Dùng Checkpoint Này", self._sel_exp, w=20).pack(side="left")

        sec(right, "Thông tin Export").pack(fill="x", pady=(0, 5))
        cr = card(right); cr.pack(fill="x", pady=5)
        L(cr, "Sau khi Export thành công, bạn sẽ nhận được 2 file:\n\n"
              "  1. <tên_model>.onnx\n"
              "  2. <tên_model>.onnx.json\n\n"
              "Hai file này sẽ nằm trong thư mục Project Dir của bạn.\n"
              "Mang 2 file này sang tab [Chạy Thử] để nghe giọng nói.", justify="left", fg=ACCENT).pack(anchor="w")

        self.after(1000, self._refresh_export_list)

    # ════════════════════════════════════════════════════════
    # TAB 4: INFERENCE
    # ════════════════════════════════════════════════════════
    def _tab_inference(self, parent):
        left  = tk.Frame(parent, bg=PANEL)
        right = tk.Frame(parent, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)
        right.pack(side="left", fill="both", expand=True, padx=(5, 10), pady=10)

        sec(left, "1. Chọn Model ONNX").pack(fill="x", pady=(0, 5))
        c = card(left); c.pack(fill="x", pady=5)
        for ltext, var, ftypes in [
            ("ONNX Model:", self.infer_model, [("ONNX", "*.onnx")]),
            ("Config JSON:", self.infer_config, [("JSON", "*.json")]),
        ]:
            r = row(c); r.pack(fill="x", pady=5)
            L(r, ltext, w=12, anchor="e").pack(side="left")
            E(r, var, w=30).pack(side="left", padx=10)
            B(r, "Chọn", lambda v=var, f=ftypes: self._browse_file(v, f), w=8).pack(side="left")

        sec(left, "2. Cấu hình Giọng").pack(fill="x", pady=(15, 5))
        c2 = card(left); c2.pack(fill="x", pady=5)
        for ltext, var, tip in [
            ("Tốc độ (Length):", self.length_scale, "1.0=Bình thường, >1.0=Chậm"),
            ("Noise Scale:", self.noise_scale, "0.667=Ổn định, 1.0=Tự nhiên"),
            ("Noise W:", self.noise_w, "Thay đổi nhịp điệu (1.0)"),
        ]:
            r = row(c2); r.pack(fill="x", pady=5)
            L(r, ltext, w=14, anchor="e").pack(side="left")
            E(r, var, w=8).pack(side="left", padx=10)
            L(r, tip, fg=DIM).pack(side="left")

        c3 = card(left); c3.pack(fill="x", pady=15)
        tk.Checkbutton(c3, text=" Bật Tiền xử lý văn bản Tiếng Việt (vn_text_processor)",
                       variable=self.use_vn_proc, bg=CARD, fg=MAIN, font=FN,
                       selectcolor=INPUT, activebackground=CARD, activeforeground=ACCENT, cursor="hand2").pack(anchor="w")
        L(c3, "Tự động đọc số thành chữ: 200k -> hai trăm nghìn", fg=DIM).pack(anchor="w", padx=25, pady=(5, 0))

        sec(right, "3. Nhập Văn Bản").pack(fill="x", pady=(0, 5))
        c4 = card(right); c4.pack(fill="x", pady=5)
        self._txt_in = tk.Text(c4, height=6, bg=INPUT, fg=MAIN, font=FB, relief="flat", bd=0, wrap="word", highlightthickness=1, highlightbackground=BORDER, insertbackground=MAIN)
        self._txt_in.pack(fill="x", padx=2, pady=2)
        self._txt_in.insert("1.0", "Chào mừng bạn đến với phần mềm Piper TTS do Văn Khải A.I Studio phát triển. Sản phẩm có giá 500.000đ.")

        br2 = row(right, bg=PANEL); br2.pack(anchor="w", pady=(5, 10))
        B(br2, "TỔNG HỢP GIỌNG ĐỌC", self._run_infer, color=TEAL, w=22).pack(side="left")
        B(br2, "Phát Audio", self._play_wav, color=ACCENT, w=14).pack(side="left", padx=10)
        B(br2, "Xóa Text", lambda: self._txt_in.delete("1.0", "end"), color=ERR, w=10).pack(side="right")

        sec(right, "Kết quả tiền xử lý văn bản").pack(fill="x", pady=(10, 5))
        c5 = card(right); c5.pack(fill="x", pady=5)
        self._txt_out = tk.Text(c5, height=5, bg=INPUT, fg=ACCENT, font=FB, relief="flat", bd=0, wrap="word", highlightthickness=1, highlightbackground=BORDER, state="disabled")
        self._txt_out.pack(fill="x", padx=2, pady=2)
        B(right, "Xem trước chữ sau khi xử lý", self._preview_vn_proc, w=26, color="#64748b").pack(anchor="w", pady=5)

    # ════════════════════════════════════════════════════════
    # TAB 5: HƯỚNG DẪN SỬ DỤNG
    # ════════════════════════════════════════════════════════
    def _tab_help(self, parent):
        import webbrowser

        outer = tk.Frame(parent, bg=PANEL)
        outer.pack(fill="both", expand=True)

        # Canvas + Scrollbar để cuộn toàn bộ nội dung
        canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=PANEL)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_configure(e):
            canvas.itemconfig(win_id, width=e.width)
        inner.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        self._scroll_canvases.append(canvas)

        pad = dict(padx=22, pady=6)

        # ── Hàm tiện ích tạo block ──────────────────────────────
        def _section(icon, title, color=ACCENT):
            f = tk.Frame(inner, bg=color, pady=1)
            f.pack(fill="x", padx=18, pady=(18, 0))
            tk.Label(f, text=f"  {icon}  {title}", bg=color, fg="#ffffff",
                     font=("Segoe UI", 11, "bold"), anchor="w", pady=6).pack(fill="x", padx=6)

        def _text(txt, fg=MAIN, indent=0, bold=False):
            font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
            tk.Label(inner, text=txt, bg=PANEL, fg=fg, font=font,
                     anchor="w", justify="left", wraplength=900,
                     padx=22 + indent, pady=2).pack(fill="x")

        def _cmd_block(cmd_text, label=""):
            """Khối lệnh với nút Sao chép"""
            cf = tk.Frame(inner, bg="#1e293b", padx=12, pady=8,
                          highlightthickness=1, highlightbackground="#334155")
            cf.pack(fill="x", padx=36, pady=4)
            row_f = tk.Frame(cf, bg="#1e293b")
            row_f.pack(fill="x")
            lbl_f = tk.Frame(row_f, bg="#1e293b")
            lbl_f.pack(side="left", fill="x", expand=True)
            if label:
                tk.Label(lbl_f, text=label, bg="#1e293b", fg="#64748b",
                         font=("Segoe UI", 8), anchor="w").pack(anchor="w")
            tk.Label(lbl_f, text=cmd_text, bg="#1e293b", fg="#7dd3fc",
                     font=("Consolas", 10), anchor="w", justify="left",
                     wraplength=820).pack(anchor="w")
            def _copy():
                self.clipboard_clear()
                self.clipboard_append(cmd_text)
                btn.config(text="✓ Đã sao chép!", fg="#34d399")
                self.after(2000, lambda: btn.config(text="⧉ Sao chép", fg="#94a3b8"))
            btn = tk.Button(row_f, text="⧉ Sao chép", command=_copy,
                            bg="#334155", fg="#94a3b8", relief="flat",
                            font=("Segoe UI", 9), cursor="hand2", padx=8, pady=3,
                            activebackground="#475569", activeforeground="#e2e8f0", bd=0)
            btn.pack(side="right", anchor="n", padx=(8, 0))
            btn.bind("<Enter>", lambda e: btn.config(bg="#475569"))
            btn.bind("<Leave>", lambda e: btn.config(bg="#334155"))

        def _link(url, display=None):
            """Nhãn link — click để mở trình duyệt"""
            display = display or url
            lf = tk.Frame(inner, bg=PANEL)
            lf.pack(anchor="w", padx=36, pady=2)
            lbl = tk.Label(lf, text=f"🔗  {display}", bg=PANEL, fg="#2563eb",
                           font=("Segoe UI", 10, "underline"), cursor="hand2", anchor="w")
            lbl.pack(side="left")
            lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            lbl.bind("<Enter>", lambda e: lbl.config(fg="#1d4ed8"))
            lbl.bind("<Leave>", lambda e: lbl.config(fg="#2563eb"))

        def _divider():
            tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=22, pady=8)

        def _note(txt):
            nf = tk.Frame(inner, bg="#fef3c7", padx=10, pady=6,
                          highlightthickness=1, highlightbackground="#f59e0b")
            nf.pack(fill="x", padx=36, pady=4)
            tk.Label(nf, text=f"⚠  {txt}", bg="#fef3c7", fg="#92400e",
                     font=("Segoe UI", 10), anchor="w", justify="left",
                     wraplength=850).pack(fill="x")

        # ══════════════════════════════════════════════════
        # TIÊU ĐỀ
        # ══════════════════════════════════════════════════
        hdr = tk.Frame(inner, bg=ACCENT, pady=14)
        hdr.pack(fill="x", padx=18, pady=(18, 0))
        tk.Label(hdr, text="📖  HƯỚNG DẪN SỬ DỤNG  ─  Piper TTS Trainer v3.0",
                 bg=ACCENT, fg="#ffffff", font=("Segoe UI", 14, "bold")).pack()
        tk.Label(hdr, text="© Văn Khải A.I Studio  ·  Đọc kỹ từng bước trước khi cài đặt",
                 bg=ACCENT, fg="#bfdbfe", font=("Segoe UI", 9)).pack(pady=(2, 0))

        # ══════════════════════════════════════════════════
        # PHẦN 1: CÀI ĐẶT
        # ══════════════════════════════════════════════════
        _section("⚙", "PHẦN 1 — CÀI ĐẶT HỆ THỐNG  (Tab Cài Đặt)")

        _text("Chọn một thư mục trống làm Project Dir rồi bấm Tạo thư mục. Sau đó chạy lần lượt từng bước bên dưới. Mỗi bước sẽ tự kiểm tra xem đã cài chưa — nếu rồi sẽ bỏ qua tự động.", fg=DIM, indent=14)
        _divider()

        steps_help = [
            ("01", "Tạo Virtual Environment (.venv)",
             "Tạo môi trường Python riêng biệt, tách hoàn toàn với hệ thống.", None, None),
            ("02", "Nâng cấp pip & scikit-build",
             "Cập nhật công cụ cốt lõi. Tự động báo phiên bản hiện tại trước khi nâng.", None, None),
            ("03", "Cài PyTorch 2.8.0 + CUDA",
             "Tải khoảng 2–3 GB — cần kết nối internet ổn định. Nếu máy không có GPU NVIDIA, app sẽ tự chuyển sang cài bản CPU.", None, None),
            ("04", "Visual Studio Build Tools  ⚠ CẦN CHÚ Ý",
             "Cần bộ biên dịch C++ để build module Monotonic Align. App tự kiểm tra xem đã cài chưa. Nếu chưa, Windows sẽ hiện hộp thoại UAC xin quyền Admin — bấm Yes để tiếp tục. Cửa sổ CMD sẽ xuất hiện, KHÔNG đóng cửa sổ đó. Sau khi xong, bấm Chạy lại để xác nhận.",
             'winget install Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --quiet --wait" --accept-package-agreements --accept-source-agreements',
             "https://aka.ms/vs/17/release/vs_BuildTools.exe"),
            ("05", "Clone mã nguồn Piper",
             "Tải repo piper1-gpl từ GitHub. App tự kiểm tra nếu đã clone rồi sẽ bỏ qua. Yêu cầu có Git trong PATH.", None, None),
            ("06", "Cài đặt thư viện Piper",
             "Cài toàn bộ phụ thuộc của Piper (pip install -e .[train]). Tự bỏ qua nếu piper đã có.", None, None),
            ("07", "Build Monotonic Align",
             "Biên dịch module C/C++ cốt lõi. Tự bỏ qua nếu file .pyd/.so đã tồn tại. Bước 04 phải hoàn tất trước.", None, None),
            ("08", "Cài Onnxscript",
             "Cần để xuất model ra định dạng .onnx. Tự bỏ qua nếu đã cài.", None, None),
            ("09", "Tải Model Base (Pretrained)",
             "Tải checkpoint có sẵn để làm điểm khởi đầu — giúp giảm đáng kể số epoch cần thiết để ra giọng tốt.", None, None),
        ]

        for num, title, desc, cmd, link_url in steps_help:
            sf = tk.Frame(inner, bg=CARD, padx=16, pady=10,
                          highlightthickness=1, highlightbackground=BORDER)
            sf.pack(fill="x", padx=24, pady=5)
            hf = tk.Frame(sf, bg=CARD); hf.pack(fill="x")
            tk.Label(hf, text=num, bg=ACCENT, fg="#fff",
                     font=("Segoe UI", 10, "bold"), width=3, pady=2).pack(side="left", anchor="n")
            tf = tk.Frame(hf, bg=CARD); tf.pack(side="left", fill="x", expand=True, padx=(10, 0))
            tk.Label(tf, text=title, bg=CARD, fg=MAIN,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
            tk.Label(tf, text=desc, bg=CARD, fg=DIM,
                     font=("Segoe UI", 9), anchor="w", justify="left",
                     wraplength=850).pack(fill="x", pady=(3, 0))
            if cmd:
                cf2 = tk.Frame(sf, bg="#1e293b", padx=10, pady=6); cf2.pack(fill="x", pady=(8, 0))
                rf2 = tk.Frame(cf2, bg="#1e293b"); rf2.pack(fill="x")
                tk.Label(rf2, text=cmd, bg="#1e293b", fg="#7dd3fc",
                         font=("Consolas", 9), anchor="w", justify="left",
                         wraplength=820).pack(side="left", fill="x", expand=True)
                def _mk_copy(c):
                    def _copy_fn():
                        self.clipboard_clear(); self.clipboard_append(c)
                        cb.config(text="✓ Đã sao chép!", fg="#34d399")
                        self.after(2000, lambda: cb.config(text="⧉ Sao chép", fg="#94a3b8"))
                    return _copy_fn
                cb = tk.Button(rf2, text="⧉ Sao chép", command=_mk_copy(cmd),
                               bg="#334155", fg="#94a3b8", relief="flat",
                               font=("Segoe UI", 9), cursor="hand2", padx=8, pady=2,
                               activebackground="#475569", bd=0)
                cb.pack(side="right", anchor="n", padx=(8, 0))
                cb.bind("<Enter>", lambda e, b=cb: b.config(bg="#475569"))
                cb.bind("<Leave>", lambda e, b=cb: b.config(bg="#334155"))
            if link_url:
                lf2 = tk.Frame(sf, bg=CARD); lf2.pack(anchor="w", pady=(6, 0))
                lnk = tk.Label(lf2, text=f"🔗  Tải trực tiếp: {link_url}",
                               bg=CARD, fg="#2563eb",
                               font=("Segoe UI", 9, "underline"), cursor="hand2")
                lnk.pack(side="left")
                lnk.bind("<Button-1>", lambda e, u=link_url: webbrowser.open(u))
                lnk.bind("<Enter>", lambda e, lb=lnk: lb.config(fg="#1d4ed8"))
                lnk.bind("<Leave>", lambda e, lb=lnk: lb.config(fg="#2563eb"))

        # ══════════════════════════════════════════════════
        # PHẦN 2: DATA & TRAIN
        # ══════════════════════════════════════════════════
        _section("💾", "PHẦN 2 — CHUẨN BỊ DỮ LIỆU & HUẤN LUYỆN  (Tab Data & Train)", color=TEAL)

        _text("Format CSV chuẩn: tên_file|nội dung văn bản (không có đuôi .wav)", indent=14, bold=True)
        _cmd_block("audio001|Xin chào tôi tên là Khải\naudio002|Hôm nay trời đẹp quá", label="Ví dụ file metadata.csv")
        _text("• File Audio: định dạng .wav, 22050 Hz, Mono (1 kênh).", fg=DIM, indent=14)
        _text("• Chọn Checkpoint: nên dùng Pretrained (Bước 09) để train nhanh hơn nhiều.", fg=DIM, indent=14)
        _text("• Bấm Bắt Đầu Train. Model tự động lưu vào thư mục lightning_logs.", fg=DIM, indent=14)
        _note("Nếu CSV có 3 cột (kiểu LJSpeech), dùng nút Fix CSV (3 cột → 2 cột) để chuyển đổi tự động.")

        # ══════════════════════════════════════════════════
        # PHẦN 3: EXPORT & INFERENCE
        # ══════════════════════════════════════════════════
        _section("📦", "PHẦN 3 — XUẤT MODEL & CHẠY THỬ  (Tab Export & Inference)")

        _text("Sau khi train xong:", indent=14, bold=True)
        _text("1.  Sang tab Xuất Model → chọn file .ckpt mới nhất → bấm Xuất ra ONNX.", fg=DIM, indent=22)
        _text("2.  Kết quả: 2 file được tạo ra trong Project Dir của bạn:", fg=DIM, indent=22)
        _cmd_block("<tên_model>.onnx\n<tên_model>.onnx.json", label="Hai file đầu ra")
        _text("3.  Sang tab Chạy Thử → nạp 2 file vừa xuất → nhập văn bản → bấm Tổng hợp giọng đọc.", fg=DIM, indent=22)

        # ══════════════════════════════════════════════════
        # PHẦN 4: CẤU HÌNH TỰ ĐỘNG
        # ══════════════════════════════════════════════════
        _section("💾", "PHẦN 4 — LƯU CẤU HÌNH TỰ ĐỘNG", color="#64748b")

        _text("Toàn bộ thiết lập (thư mục, tên giọng, batch size, v.v.) được tự động lưu vào file:", fg=DIM, indent=14)
        _cmd_block("piper_trainer_config.json", label="File lưu cấu hình (cùng thư mục với app)")
        _text("Lần sau mở app, tất cả thiết lập sẽ được khôi phục lại tự động.", fg=DIM, indent=14)

        # ══════════════════════════════════════════════════
        # PHẦN 5: TÀI NGUYÊN HỮU ÍCH
        # ══════════════════════════════════════════════════
        _section("🌐", "PHẦN 5 — TÀI NGUYÊN HỮU ÍCH", color="#7c3aed")

        resources = [
            ("Repo Piper chính thức (OHF Voice)", "https://github.com/OHF-voice/piper1-gpl"),
            ("Checkpoints Piper trên Hugging Face", "https://huggingface.co/datasets/rhasspy/piper-checkpoints"),
            ("Tải Git cho Windows", "https://git-scm.com/download/win"),
            ("Tải Visual Studio Build Tools", "https://aka.ms/vs/17/release/vs_BuildTools.exe"),
            ("Tài liệu PyTorch", "https://pytorch.org/get-started/locally/"),
        ]
        for label, url in resources:
            lf3 = tk.Frame(inner, bg=PANEL); lf3.pack(anchor="w", padx=36, pady=2)
            lnk3 = tk.Label(lf3, text=f"🔗  {label}  —  {url}",
                            bg=PANEL, fg="#2563eb",
                            font=("Segoe UI", 10, "underline"), cursor="hand2", anchor="w")
            lnk3.pack(side="left")
            lnk3.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
            lnk3.bind("<Enter>", lambda e, lb=lnk3: lb.config(fg="#1d4ed8"))
            lnk3.bind("<Leave>", lambda e, lb=lnk3: lb.config(fg="#2563eb"))

        # Padding cuối trang
        tk.Frame(inner, bg=PANEL, height=30).pack()

    # ════════════════════════════════════════════════════════
    # LƯU / NẠP CẤU HÌNH
    # ════════════════════════════════════════════════════════
    _CONFIG_KEYS = [
        ("project_dir",  "str"),
        ("voice_name",   "str"),
        ("espeak_lang",  "str"),
        ("sample_rate",  "str"),
        ("dataset_csv",  "str"),
        ("audio_dir",    "str"),
        ("batch_size",   "str"),
        ("max_epochs",   "str"),
        ("ckpt_path",    "str"),
        ("export_ckpt",  "str"),
        ("export_name",  "str"),
        ("infer_model",  "str"),
        ("infer_config", "str"),
        ("length_scale", "str"),
        ("noise_scale",  "str"),
        ("noise_w",      "str"),
        ("use_vn_proc",  "bool"),
        ("_ckpt_url",    "str"),
        ("_cfg_url",     "str"),
    ]

    def _load_saved_config(self):
        data = _load_config()
        if not data:
            return
        for key, kind in self._CONFIG_KEYS:
            var = getattr(self, key, None)
            if var is None or key not in data:
                continue
            try:
                if kind == "bool":
                    var.set(bool(data[key]))
                else:
                    var.set(str(data[key]))
            except Exception:
                pass

    def _save_current_config(self):
        data = {}
        for key, kind in self._CONFIG_KEYS:
            var = getattr(self, key, None)
            if var is None:
                continue
            try:
                data[key] = var.get()
            except Exception:
                pass
        _save_config(data)

    def _on_close(self):
        self._save_current_config()
        self.destroy()

    # ════════════════════════════════════════════════════════
    # HÀM LOGIC & CHẠY LỆNH NỀN
    # ════════════════════════════════════════════════════════
    def _run_step(self, sid, fn):
        self._set_step(sid, "running", "⏳ Đang chạy...")
        def _w():
            try:
                fn(sid)
            except Exception as e:
                self.after(0, self._set_step, sid, "error", f"✗ Lỗi: {e}")
                self.after(0, self.log, f"Step {sid} lỗi: {e}", "err")
        threading.Thread(target=_w, daemon=True).start()

    def _set_step(self, sid, status, text):
        sv  = self._step_sv.get(sid)
        lbl = self._step_lbl.get(sid)
        if sv:  sv.set(text)
        if lbl:
            c = {"ok": TEAL, "error": ERR, "running": WARN}.get(status, DIM)
            lbl.config(fg=c)

    def _run_blocking(self, cmd, cwd=None, env=None):
        _env = env or os.environ.copy()
        vs = Path(self.project_dir.get()) / ".venv" / "Scripts"
        if vs.exists():
            _env["PATH"] = str(vs) + os.pathsep + _env.get("PATH", "")
            _env["VIRTUAL_ENV"] = str(Path(self.project_dir.get()) / ".venv")
        self.after(0, self.log, "$ " + " ".join(str(x) for x in cmd), "info")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd, env=_env,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        for ln in (r.stdout + r.stderr).strip().split("\n"):
            if ln.strip():
                tag = "err" if any(k in ln.lower() for k in ("error", "exception", "failed")) else ""
                self.after(0, self.log, ln, tag)
        return r.returncode

    def _step_create_venv(self, sid):
        vd = Path(self.project_dir.get()) / ".venv"
        if vd.exists():
            self.after(0, self._set_step, sid, "ok", "✓ Đã có .venv")
            self.after(0, self._check_venv)
            return
        rc = self._run_blocking([_find_system_python(), "-m", "venv", str(vd)])
        if rc == 0:
            self.after(0, self._set_step, sid, "ok", "✓ Tạo .venv xong")
            self.after(0, self._check_venv)
        else:
            self.after(0, self._set_step, sid, "error", "✗ Tạo .venv thất bại")

    def _step_upgrade_pip(self, sid):
        # Kiểm tra phiên bản pip hiện tại
        r = subprocess.run([self._use_py(), "-m", "pip", "--version"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        self.after(0, self.log, f"pip hiện tại: {r.stdout.strip()}", "dim")
        pkgs = ["--upgrade", "pip", "setuptools", "wheel", "scikit-build"]
        rc = self._run_blocking([self._use_py(), "-m", "pip", "install"] + pkgs)
        if rc == 0: self.after(0, self._set_step, sid, "ok", "✓ pip + scikit-build OK")
        else: self.after(0, self._set_step, sid, "error", "✗ Thất bại")

    # ── BƯỚC A: Môi trường & Công cụ (gộp venv + pip) ───────────────────────
    def _step_env_and_tools(self, sid):
        """Tạo .venv rồi nâng cấp pip + scikit-build trong một bước."""
        vd = Path(self.project_dir.get()) / ".venv"
        if vd.exists():
            self.after(0, self.log, ".venv đã tồn tại — bỏ qua tạo mới.", "ok")
        else:
            self.after(0, self.log, "Đang tạo Virtual Environment...", "info")
            rc = self._run_blocking([_find_system_python(), "-m", "venv", str(vd)])
            if rc != 0:
                self.after(0, self._set_step, sid, "error", "✗ Tạo .venv thất bại")
                return
            self.after(0, self._check_venv)
        r = subprocess.run([self._use_py(), "-m", "pip", "--version"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        self.after(0, self.log, f"pip: {r.stdout.strip()}", "dim")
        rc2 = self._run_blocking([self._use_py(), "-m", "pip", "install",
                                   "--upgrade", "pip", "setuptools", "wheel", "scikit-build"])
        if rc2 == 0:
            self.after(0, self._set_step, sid, "ok", "✓ .venv + pip OK")
        else:
            self.after(0, self._set_step, sid, "error", "✗ Nâng cấp pip thất bại")

    # ── BƯỚC D: Piper + Monotonic Align + Onnxscript (gộp 05+06+07+08) ──────
    def _step_piper_all(self, sid):
        """Clone piper1-gpl → cài piper[train] → build monotonic → cài onnxscript."""
        wd = Path(self.project_dir.get())
        dest = wd / "piper1-gpl"
        # 05: Clone
        if dest.exists():
            self.after(0, self.log, "Repo piper1-gpl đã tồn tại — bỏ qua clone.", "ok")
        else:
            git_exe = shutil.which("git")
            if not git_exe:
                self.after(0, self._set_step, sid, "error", "✗ Chưa có git trong PATH")
                self.after(0, self.log, "Cài Git tại https://git-scm.com/ rồi thử lại.", "err")
                return
            self.after(0, self.log, "Đang clone piper1-gpl từ GitHub...", "info")
            rc = self._run_blocking(
                ["git", "clone", "https://github.com/OHF-voice/piper1-gpl.git", str(dest)],
                cwd=str(wd))
            if rc != 0:
                self.after(0, self._set_step, sid, "error", "✗ Clone thất bại")
                return
        # 06: Cài piper[train]
        r = subprocess.run([self._use_py(), "-c", "import piper; print('ok')"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode == 0:
            self.after(0, self.log, "piper đã cài sẵn — bỏ qua.", "ok")
        else:
            self.after(0, self.log, "Đang cài piper[train]...", "info")
            rc = self._run_blocking(
                [self._use_py(), "-m", "pip", "install", "-e", ".[train]"],
                cwd=str(dest))
            if rc != 0:
                self.after(0, self._set_step, sid, "error", "✗ Cài piper[train] thất bại")
                return
        # 07: Build Monotonic Align
        ma_dir = self._src_dir() / "piper" / "train" / "vits" / "monotonic_align"
        ms = ma_dir / "setup.py"
        existing = list(ma_dir.glob("*.pyd")) + list(ma_dir.glob("*.so"))
        sub_dir = ma_dir / "monotonic_align"
        if sub_dir.exists():
            existing += list(sub_dir.glob("*.pyd")) + list(sub_dir.glob("*.so"))
        if existing:
            self.after(0, self.log, f"Monotonic Align đã build ({existing[0].name}) — bỏ qua.", "ok")
        elif ms.exists():
            self.after(0, self.log, "Đang build Monotonic Align...", "info")
            rc = self._run_blocking(
                [self._use_py(), str(ms), "build_ext", "--inplace",
                 "--build-lib", str(self._src_dir()),
                 "--build-temp", str(self._src_dir() / "build")],
                cwd=str(self._src_dir()))
            pyd_files = list(ma_dir.glob("*.pyd")) + list(ma_dir.glob("*.so"))
            if pyd_files:
                target_dir = ma_dir / "monotonic_align"
                target_dir.mkdir(exist_ok=True)
                for pyd in pyd_files:
                    shutil.copy2(str(pyd), str(target_dir / pyd.name))
            if rc != 0:
                self.after(0, self._set_step, sid, "error", "✗ Build Monotonic thất bại")
                return
        # 08: Cài onnxscript
        r2 = subprocess.run(
            [self._use_py(), "-c", "import onnxscript; print(onnxscript.__version__)"],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if r2.returncode == 0 and r2.stdout.strip():
            self.after(0, self.log, f"onnxscript {r2.stdout.strip()} đã có — bỏ qua.", "ok")
        else:
            self.after(0, self.log, "Đang cài onnxscript...", "info")
            rc = self._run_blocking([self._use_py(), "-m", "pip", "install", "onnxscript"])
            if rc != 0:
                self.after(0, self._set_step, sid, "error", "✗ Cài onnxscript thất bại")
                return
        self.after(0, self._set_step, sid, "ok", "✓ Piper + Monotonic + Onnx OK")

    # ── AUTO SETUP: Chạy A→F tuần tự ────────────────────────────────────────
    def _auto_setup(self):
        """Chạy tất cả 6 bước A→F trong một luồng nền, tuần tự."""
        if getattr(self, "_auto_running", False):
            return
        self._auto_running = True
        self._btn_auto.config(state="disabled", text="⏳ Đang chạy...")
        AUTO_STEPS = [
            ("A", "Môi trường & Công cụ",    self._step_env_and_tools),
            ("B", "PyTorch",                  self._step_install_torch),
            ("C", "VS Build Tools",           self._step_install_vs),
            ("D", "Piper + Monotonic + Onnx", self._step_piper_all),
            ("E", "Tải Model Pretrained",     self._step_download_ckpt),
            ("F", "Build eSpeak Bridge",      self._step_build_espeak),
        ]
        def _run_all():
            for sid, label, fn in AUTO_STEPS:
                self.after(0, self._auto_progress.set, f"▶ Bước {sid}: {label}...")
                self.after(0, self._set_step, sid, "running", "⏳ Đang chạy...")
                self.after(0, self.log, f"[AUTO] ── Bắt đầu Bước {sid}: {label}", "info")
                try:
                    fn(sid)
                except Exception as e:
                    self.after(0, self.log, f"[AUTO] Bước {sid} lỗi: {e}", "err")
                    self.after(0, self._set_step, sid, "error", f"✗ {e}")
                    self.after(0, self._auto_progress.set, f"✗ Dừng tại bước {sid}: {e}")
                    break
                sv = self._step_sv.get(sid)
                if sv and sv.get().startswith("✗"):
                    self.after(0, self.log,
                        f"[AUTO] Bước {sid} thất bại — dừng auto setup.", "err")
                    self.after(0, self._auto_progress.set,
                        f"✗ Dừng tại bước {sid} — xem log để biết chi tiết.")
                    break
            else:
                self.after(0, self._auto_progress.set, "✅ Hoàn thành tất cả các bước!")
                self.after(0, self.log,
                    "[AUTO] ✅ Setup hoàn tất! Bạn có thể bắt đầu Train.", "ok")
            self._auto_running = False
            self.after(0, self._btn_auto.config,
                       {"state": "normal", "text": "⚡ AUTO SETUP ALL"})
        threading.Thread(target=_run_all, daemon=True).start()

    def _step_install_torch(self, sid):
        # Kiểm tra đã có torch chưa
        r = subprocess.run([self._use_py(), "-c", "import torch; print(torch.__version__)"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode == 0 and r.stdout.strip():
            ver = r.stdout.strip()
            self.after(0, self.log, f"PyTorch đã cài sẵn: {ver} — bỏ qua bước này.", "ok")
            self.after(0, self._set_step, sid, "ok", f"✓ Đã có PyTorch {ver}")
            return
        rc = self._run_blocking([self._use_py(), "-m", "pip", "install", "torch==2.8.0", "torchvision==0.23.0", "torchaudio==2.8.0", "--index-url", "https://download.pytorch.org/whl/cu126"])
        if rc == 0: self.after(0, self._set_step, sid, "ok", "✓ PyTorch CUDA OK")
        else:
            self.after(0, self.log, "Cài CUDA thất bại, thử cài CPU...", "warn")
            rc2 = self._run_blocking([self._use_py(), "-m", "pip", "install", "torch==2.8.0", "torchvision==0.23.0", "torchaudio==2.8.0"])
            if rc2 == 0: self.after(0, self._set_step, sid, "ok", "✓ PyTorch CPU")
            else: self.after(0, self._set_step, sid, "error", "✗ Thất bại")

    def _step_install_vs(self, sid):
        import ctypes

        # ── Lệnh cài đặt (hiển thị rõ trong log để user copy nếu cần) ──
        WINGET_CMD = (
            'winget install Microsoft.VisualStudio.2022.BuildTools '
            '--override "--add Microsoft.VisualStudio.Workload.VCTools '
            '--includeRecommended --quiet --wait" --accept-package-agreements '
            '--accept-source-agreements'
        )
        MANUAL_MSG = (
            "Lệnh thủ công (chạy CMD với quyền Admin):\n"
            f"  {WINGET_CMD}\n"
            "Hoặc tải trực tiếp: https://aka.ms/vs/17/release/vs_BuildTools.exe"
        )

        # ── Kiểm tra đã cài chưa (tìm cl.exe qua vswhere) ──
        VSWHERE = (
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
        )
        def _is_vs_installed():
            try:
                r = subprocess.run(
                    [VSWHERE, "-products", "*", "-requires",
                     "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                     "-property", "installationPath"],
                    capture_output=True, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                return bool(r.stdout.strip())
            except Exception:
                pass
            # Fallback: tìm cl.exe trong các đường dẫn thông dụng
            import glob
            patterns = [
                r"C:\Program Files (x86)\Microsoft Visual Studio\*\BuildTools\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
                r"C:\Program Files\Microsoft Visual Studio\*\BuildTools\VC\Tools\MSVC\*\bin\Hostx64\x64\cl.exe",
            ]
            for pat in patterns:
                if glob.glob(pat):
                    return True
            return False

        if _is_vs_installed():
            self.after(0, self._set_step, sid, "ok", "✓ VS BuildTools đã cài")
            self.after(0, self.log, "Visual Studio Build Tools đã được cài đặt sẵn.", "ok")
            return

        self.after(0, self.log, "Đang yêu cầu quyền Admin để cài VS BuildTools...", "warn")
        self.after(0, self.log, MANUAL_MSG, "info")

        # ── Thử tự động cài qua winget với UAC elevation ──
        # ShellExecuteW verb="runas" sẽ hiện hộp thoại UAC của Windows
        try:
            import tempfile, textwrap
            # Tạo script .bat tạm để chạy winget với quyền admin
            bat_content = textwrap.dedent(f"""\
                @echo off
                echo Dang cai Visual Studio Build Tools...
                {WINGET_CMD}
                if %errorlevel% == 0 (
                    echo THANH CONG
                ) else (
                    echo LOI: Cai dat that bai, vui long chay thu cong.
                    echo {MANUAL_MSG}
                )
                pause
            """)
            tmp_bat = Path(tempfile.gettempdir()) / "install_vs_buildtools.bat"
            tmp_bat.write_text(bat_content, encoding="ascii", errors="replace")

            # ShellExecuteW với runas = tự hiện hộp thoại UAC
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", "cmd.exe",
                f'/c "{str(tmp_bat)}"',
                None, 1  # SW_SHOWNORMAL — hiện cửa sổ CMD để user thấy tiến trình
            )

            if ret > 32:  # > 32 = thành công khởi chạy (không phải = cài xong)
                self.after(0, self._set_step, sid, "ok",
                           "✓ Đang cài (xem cửa sổ mới)")
                self.after(0, self.log,
                           "Cửa sổ cài đặt đã mở. Chờ hoàn tất rồi bấm [Chạy] lại để xác nhận.", "warn")
            else:
                self.after(0, self._set_step, sid, "error",
                           "✗ Không thể mở UAC — chạy thủ công")
                self.after(0, self.log,
                           "Không thể tự động nâng quyền. Hãy chạy thủ công lệnh ở trên.", "err")

        except Exception as e:
            self.after(0, self._set_step, sid, "error", f"✗ Lỗi: {e}")
            self.after(0, self.log, f"Lỗi khi cài VS BuildTools: {e}", "err")

    def _step_clone_piper(self, sid):
        wd = Path(self.project_dir.get())
        dest = wd / "piper1-gpl"
        if dest.exists():
            self.after(0, self._set_step, sid, "ok", "✓ Đã có repo")
            self.after(0, self.log, "Repo piper1-gpl đã tồn tại — bỏ qua clone.", "ok")
            return
        # Kiểm tra git có trong PATH không
        git_exe = shutil.which("git")
        if not git_exe:
            self.after(0, self._set_step, sid, "error", "✗ Chưa có git trong PATH")
            self.after(0, self.log, "Không tìm thấy git. Hãy cài Git từ https://git-scm.com/ rồi thử lại.", "err")
            return
        rc = self._run_blocking(["git", "clone", "https://github.com/OHF-voice/piper1-gpl.git", str(dest)], cwd=str(wd))
        if rc == 0: self.after(0, self._set_step, sid, "ok", "✓ Clone xong")
        else: self.after(0, self._set_step, sid, "error", "✗ Clone lỗi")

    def _step_install_piper(self, sid):
        pd = self._piper_dir()
        if not pd.exists(): return self.after(0, self._set_step, sid, "error", "✗ Chưa có piper repo")
        # Kiểm tra piper đã cài chưa
        r = subprocess.run([self._use_py(), "-c", "import piper; print('ok')"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode == 0:
            self.after(0, self.log, "Thư viện piper đã được cài — bỏ qua bước này.", "ok")
            self.after(0, self._set_step, sid, "ok", "✓ piper đã có sẵn")
            return
        rc = self._run_blocking([self._use_py(), "-m", "pip", "install", "-e", ".[train]"], cwd=str(pd))
        if rc == 0: self.after(0, self._set_step, sid, "ok", "✓ piper[train] OK")
        else: self.after(0, self._set_step, sid, "error", "✗ Thất bại")

    def _step_build_monotonic(self, sid):
        ms = self._src_dir() / "piper" / "train" / "vits" / "monotonic_align" / "setup.py"
        if not ms.exists(): return self.after(0, self._set_step, sid, "error", "✗ Không có setup.py")
        # Kiểm tra đã build chưa (tìm .pyd hoặc .so)
        ma_dir = self._src_dir() / "piper" / "train" / "vits" / "monotonic_align"
        existing = list(ma_dir.glob("*.pyd")) + list(ma_dir.glob("*.so"))
        sub_dir = ma_dir / "monotonic_align"
        if sub_dir.exists():
            existing += list(sub_dir.glob("*.pyd")) + list(sub_dir.glob("*.so"))
        if existing:
            self.after(0, self.log, f"Monotonic Align đã được build ({existing[0].name}) — bỏ qua.", "ok")
            self.after(0, self._set_step, sid, "ok", "✓ Đã build sẵn")
            return
        rc = self._run_blocking([self._use_py(), str(ms), "build_ext", "--inplace", "--build-lib", str(self._src_dir()), "--build-temp", str(self._src_dir() / "build")], cwd=str(self._src_dir()))
        pyd_files = list(ma_dir.glob("*.pyd")) + list(ma_dir.glob("*.so"))
        if pyd_files:
            target_dir = ma_dir / "monotonic_align"
            target_dir.mkdir(exist_ok=True)
            for pyd in pyd_files: shutil.copy2(str(pyd), str(target_dir / pyd.name))
            self.after(0, self._set_step, sid, "ok", "✓ Build + Copy OK")
        else:
            if rc == 0: self.after(0, self._set_step, sid, "ok", "✓ Build xong (Ko có pyd)")
            else: self.after(0, self._set_step, sid, "error", "✗ Build lỗi")

    def _step_install_onnx(self, sid):
        # Kiểm tra onnxscript đã cài chưa
        r = subprocess.run([self._use_py(), "-c", "import onnxscript; print(onnxscript.__version__)"],
                           capture_output=True, text=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        if r.returncode == 0 and r.stdout.strip():
            ver = r.stdout.strip()
            self.after(0, self.log, f"onnxscript đã cài sẵn: {ver} — bỏ qua bước này.", "ok")
            self.after(0, self._set_step, sid, "ok", f"✓ onnxscript {ver}")
            return
        rc = self._run_blocking([self._use_py(), "-m", "pip", "install", "onnxscript"])
        if rc == 0: self.after(0, self._set_step, sid, "ok", "✓ onnxscript OK")
        else: self.after(0, self._set_step, sid, "error", "✗ Thất bại")

    def _gen_espeak_devfiles(self, espeak_install_dir: Path) -> Path:
        """
        Tạo development files cho eSpeak-NG trong thư mục project (không cần Admin):
          <project_dir>/espeak-ng-dev/
            include/espeak-ng/speak_lib.h   ← tải từ GitHub
            include/espeak-ng/espeak_ng.h   ← tải từ GitHub
            lib/espeak-ng.lib               ← tạo từ libespeak-ng.dll
            lib/libespeak-ng.dll            ← copy từ install dir (linker cần)

        Trả về đường dẫn tới thư mục dev (dùng làm ESPEAK_NG_DIR).
        """
        import urllib.request, tempfile, re, shutil as _shutil

        # ── Thư mục dev nằm trong project (luôn có quyền ghi) ──
        dev_dir = Path(self.project_dir.get()) / "espeak-ng-dev"
        dev_dir.mkdir(parents=True, exist_ok=True)

        HEADER_BASE = (
            "https://raw.githubusercontent.com/espeak-ng/espeak-ng"
            "/master/src/include/espeak-ng/"
        )
        HEADERS = ["speak_lib.h", "espeak_ng.h"]

        # ── 1. Tải headers ──
        inc_dir = dev_dir / "include" / "espeak-ng"
        inc_dir.mkdir(parents=True, exist_ok=True)
        for h in HEADERS:
            dst = inc_dir / h
            if not dst.exists():
                self.after(0, self.log, f"Đang tải header: {h} ...", "info")
                urllib.request.urlretrieve(HEADER_BASE + h, str(dst))
                self.after(0, self.log, f"Đã lưu: {dst}", "ok")
            else:
                self.after(0, self.log, f"Header {h} đã có sẵn.", "dim")

        # ── 2. Copy DLL vào dev dir (linker cần tìm thấy DLL) ──
        lib_dir = dev_dir / "lib"
        lib_dir.mkdir(exist_ok=True)
        src_dll = espeak_install_dir / "libespeak-ng.dll"
        dst_dll = lib_dir / "libespeak-ng.dll"
        if src_dll.exists() and not dst_dll.exists():
            _shutil.copy2(str(src_dll), str(dst_dll))
            self.after(0, self.log, "Đã copy libespeak-ng.dll vào dev dir.", "ok")

        # ── 3. Tạo import .lib từ .dll (dùng VS dumpbin + lib.exe) ──
        lib_file = lib_dir / "espeak-ng.lib"
        if lib_file.exists():
            self.after(0, self.log, "Import lib đã có sẵn — bỏ qua.", "dim")
            return dev_dir

        dll_path = dst_dll if dst_dll.exists() else src_dll
        if not dll_path.exists():
            raise FileNotFoundError(f"Không tìm thấy {dll_path}")

        # Tìm VS tools
        vswhere = Path(
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
        )
        if not vswhere.exists():
            raise RuntimeError("vswhere.exe không tìm thấy — hãy chạy Step 04 trước.")

        r = subprocess.run(
            [str(vswhere), "-products", "*", "-requires",
             "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
             "-property", "installationPath"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        vs_path = (r.stdout.strip().splitlines() or [""])[0]
        if not vs_path:
            raise RuntimeError("VS Build Tools chưa cài — hãy chạy Step 04 trước.")

        def _find_vs_tool(name):
            for p in Path(vs_path).rglob(name):
                s = str(p)
                if "Hostx64" in s and r"\x64\\" in s:
                    return s
            for p in Path(vs_path).rglob(name):
                return str(p)
            return None

        dumpbin_exe = _find_vs_tool("dumpbin.exe")
        lib_exe     = _find_vs_tool("lib.exe")
        if not dumpbin_exe or not lib_exe:
            raise RuntimeError("Không tìm thấy dumpbin.exe hoặc lib.exe trong VS.")

        # Lấy exports từ DLL
        self.after(0, self.log, "Đang đọc exports từ libespeak-ng.dll ...", "info")
        dump = subprocess.run(
            [dumpbin_exe, "/exports", str(dll_path)],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        exports = []
        in_table = False
        for line in dump.stdout.splitlines():
            stripped = line.strip()
            if re.match(r"ordinal\s+hint\s+RVA\s+name", stripped, re.I):
                in_table = True
                continue
            if in_table:
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) >= 4 and re.match(r"[0-9A-Fa-f]+", parts[0]):
                    exports.append(parts[-1])

        if not exports:
            raise RuntimeError("Không đọc được exports từ DLL.")

        self.after(0, self.log, f"Tìm thấy {len(exports)} exports — đang tạo .lib ...", "ok")

        tmp_def = Path(tempfile.gettempdir()) / "espeak-ng.def"
        tmp_def.write_text(
            "LIBRARY libespeak-ng\nEXPORTS\n" +
            "\n".join(f"    {e}" for e in exports),
            encoding="ascii", errors="replace"
        )

        r2 = subprocess.run(
            [lib_exe, f"/def:{tmp_def}", f"/out:{lib_file}", "/machine:x64"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if not lib_file.exists():
            raise RuntimeError(f"lib.exe thất bại:\n{r2.stdout}\n{r2.stderr}")

        self.after(0, self.log, f"Đã tạo: {lib_file}", "ok")
        return dev_dir

    def _step_build_espeak(self, sid):
        """
        Build Cython extension 'espeakbridge'.
        - Tự động tải headers từ GitHub nếu thiếu.
        - Tự động tạo import .lib từ libespeak-ng.dll nếu thiếu.
        - Rebuild piper với ESPEAK_NG_DIR đã set.
        """
        src = self._src_dir()

        # ── 1. Kiểm tra đã import được chưa (thử editable path + site-packages) ──
        for _import_cmd in [
            f"import sys; sys.path.insert(0,r'{src}'); from piper import espeakbridge; print('ok')",
            "from piper import espeakbridge; print('ok')",
        ]:
            check = subprocess.run(
                [self._use_py(), "-c", _import_cmd],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if check.returncode == 0 and "ok" in check.stdout:
                self.after(0, self._set_step, sid, "ok", "✓ espeakbridge OK")
                self.after(0, self.log, "espeakbridge đã có sẵn — bỏ qua.", "ok")
                return

        # ── 2. Tìm thư mục cài eSpeak-NG ──
        espeak_candidates = [
            Path(r"C:\Program Files\eSpeak NG"),
            Path(r"C:\Program Files (x86)\eSpeak NG"),
        ]
        espeak_dir = None
        for d in espeak_candidates:
            if d.exists():
                espeak_dir = d
                break

        if not espeak_dir:
            self.after(0, self._set_step, sid, "error", "✗ Chưa cài eSpeak-NG")
            self.after(0, self.log,
                "Chưa tìm thấy eSpeak-NG!\n"
                "Tải installer tại: https://github.com/espeak-ng/espeak-ng/releases\n"
                "  → Chọn file .msi bản x64, cài xong bấm [▶ Chạy] lại.", "err")
            return

        self.after(0, self.log, f"Tìm thấy eSpeak-NG: {espeak_dir}", "ok")

        # ── 3. Tự động tạo headers + .lib trong project dir (không cần Admin) ──
        try:
            dev_dir = self._gen_espeak_devfiles(espeak_dir)
        except Exception as e:
            self.after(0, self._set_step, sid, "error", "✗ Lỗi tạo dev files")
            self.after(0, self.log, f"Lỗi khi chuẩn bị dev files: {e}", "err")
            return

        # ── 4. Build extension theo đúng cách notebook Colab dùng ─────────────────
        # Notebook gốc: python3 setup.py build_ext --inplace -v
        # → Compile trực tiếp espeakbridge*.pyd vào src/piper/ (không cần extract wheel).
        # Cần cmake + ninja + ESPEAK_NG_DIR + LIB/INCLUDE đã set đúng.
        # ─────────────────────────────────────────────────────────────────────────────
        env = os.environ.copy()
        env["ESPEAK_NG_DIR"] = str(dev_dir)

        lib_dir = dev_dir / "lib"
        inc_dir = dev_dir / "include"
        env["LIB"]     = str(lib_dir) + os.pathsep + env.get("LIB", "")
        env["INCLUDE"] = str(inc_dir) + os.pathsep + env.get("INCLUDE", "")
        env["PATH"]    = str(lib_dir) + os.pathsep + env.get("PATH", "")

        # Luôn thêm venv/Scripts vào PATH (cmake.exe pip-cài sẽ ở đây)
        venv_scripts = Path(self.project_dir.get()) / ".venv" / "Scripts"
        if venv_scripts.exists():
            env["PATH"] = str(venv_scripts) + os.pathsep + env["PATH"]

        # ── 4a. Đảm bảo cmake + ninja có sẵn ──
        try:
            cmake_ok = subprocess.run(
                ["cmake", "--version"], capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            ).returncode == 0
        except FileNotFoundError:
            cmake_ok = False

        if not cmake_ok:
            self.after(0, self.log,
                "CMake chưa có — đang cài cmake + ninja qua pip ...", "warn")
            rc_cmake = self._run_blocking(
                [self._use_py(), "-m", "pip", "install", "cmake", "ninja"],
                env=env
            )
            if rc_cmake != 0:
                self.after(0, self._set_step, sid, "error", "✗ Không cài được cmake")
                self.after(0, self.log,
                    "Không cài được cmake. Thử thủ công: pip install cmake ninja", "err")
                return
            self.after(0, self.log, "Đã cài cmake + ninja.", "ok")
        else:
            self.after(0, self.log, "cmake đã có sẵn.", "dim")

        # ── 4b. setup.py build_ext --inplace (đúng như Colab notebook) ──
        # Compile espeakbridge*.pyd trực tiếp vào src/piper/
        setup_py = self._piper_dir() / "setup.py"
        if not setup_py.exists():
            self.after(0, self._set_step, sid, "error", "✗ Không tìm thấy setup.py")
            self.after(0, self.log,
                f"Không có setup.py trong {self._piper_dir()}\n"
                "Thử clone lại repo: Xóa thư mục piper1-gpl rồi chạy Step 05.", "err")
            return

        self.after(0, self.log,
            f"Đang chạy: setup.py build_ext --inplace với ESPEAK_NG_DIR={dev_dir} ...", "info")
        rc = self._run_blocking(
            [self._use_py(), "setup.py", "build_ext", "--inplace", "-v"],
            cwd=str(self._piper_dir()), env=env
        )

        if rc != 0:
            self.after(0, self._set_step, sid, "error", "✗ build_ext thất bại")
            self.after(0, self.log,
                "build_ext --inplace thất bại. Nguyên nhân thường gặp:\n"
                "  • cmake/ninja chưa có trong PATH\n"
                "  • VS Build Tools chưa cài (Step 04)\n"
                "  • espeak-ng-dev/lib/espeak-ng.lib chưa có\n"
                "  • espeak-ng-dev/include/espeak-ng/*.h thiếu header", "err")
            return

        # ── 5. Tìm .pyd vừa build (đã nằm trong src/piper/ hoặc build/) ──
        piper_src_dir = src / "piper"
        extracted_pyd = None

        # Ưu tiên: file vừa build_ext --inplace đặt thẳng vào src/piper/
        for pyd in piper_src_dir.glob("espeakbridge*.pyd"):
            extracted_pyd = pyd
            self.after(0, self.log, f"Tìm thấy {pyd.name} trong src/piper/", "ok")
            break

        # Fallback: tìm trong build/ rồi copy về
        if not extracted_pyd:
            for pyd in self._piper_dir().rglob("espeakbridge*.pyd"):
                if pyd.parent == piper_src_dir:
                    continue
                dst = piper_src_dir / pyd.name
                shutil.copy2(str(pyd), str(dst))
                extracted_pyd = dst
                self.after(0, self.log,
                    f"Đã copy {pyd.name} từ build/ → src/piper/", "ok")
                break

        if not extracted_pyd:
            self.after(0, self._set_step, sid, "error", "✗ Không tìm thấy .pyd sau build")
            self.after(0, self.log,
                "build_ext báo thành công nhưng không tìm thấy espeakbridge*.pyd.\n"
                f"Kiểm tra thư mục: {piper_src_dir}", "err")
            return

        # Đảm bảo libespeak-ng.dll có cạnh .pyd để Windows load được
        espeak_dll_src = dev_dir / "lib" / "libespeak-ng.dll"
        espeak_dll_dst = piper_src_dir / "libespeak-ng.dll"
        if espeak_dll_src.exists() and not espeak_dll_dst.exists():
            shutil.copy2(str(espeak_dll_src), str(espeak_dll_dst))
            self.after(0, self.log, "Đã copy libespeak-ng.dll → src/piper/ (DLL runtime)", "ok")

        # ── 6. Verify import ────────────────────────────────────────────────────
        verify = subprocess.run(
            [self._use_py(), "-c",
             f"import sys, os; sys.path.insert(0,r'{src}'); "
             f"os.add_dll_directory(r'{lib_dir}'); "
             f"from piper import espeakbridge; print('ok')"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if verify.returncode == 0 and "ok" in verify.stdout:
            self.after(0, self._set_step, sid, "ok", "✓ espeakbridge OK")
            self.after(0, self.log,
                "Build espeakbridge thành công! Bạn có thể chuyển sang Train.", "ok")
        else:
            err_lines = (verify.stderr or verify.stdout or "").strip().splitlines()
            self.after(0, self._set_step, sid, "error", "✗ DLL load lỗi")
            self.after(0, self.log,
                "espeakbridge.pyd đã có nhưng import vẫn lỗi (thường là thiếu DLL):\n" +
                "\n".join(err_lines[-6:]) +
                f"\nĐã copy libespeak-ng.dll vào src/piper/ — thử bấm [▶ Chạy] lại một lần nữa.", "err")

    def _step_download_ckpt(self, sid):
        import urllib.request
        pd = self._piper_dir()
        pd.mkdir(parents=True, exist_ok=True)
        ckpt_out = pd / "pretrained-model.ckpt"
        cfg_out  = pd / "config.json"
        cleaned  = pd / "pretrained-model-cleaned.ckpt"

        if cleaned.exists():
            self.after(0, self._set_step, sid, "ok", "✓ Đã có pretrained")
            self.after(0, self._refresh_pre_label)
            return
        try:
            urllib.request.urlretrieve(self._ckpt_url.get(), str(ckpt_out))
            urllib.request.urlretrieve(self._cfg_url.get(), str(cfg_out))
            self._clean_ckpt_sync(str(ckpt_out), str(cleaned))
            self.after(0, self._set_step, sid, "ok", "✓ Tải và Clean xong")
            self.after(0, self._refresh_pre_label)
        except Exception as e:
            self.after(0, self._set_step, sid, "error", "✗ Lỗi tải")

    # ── Utils Paths ──
    def _venv_py(self): return Path(self.project_dir.get()) / ".venv" / "Scripts" / "python.exe"
    def _piper_dir(self): return Path(self.project_dir.get()) / "piper1-gpl"
    def _src_dir(self): return self._piper_dir() / "src"
    def _lightning_dir(self): return self._src_dir() / "lightning_logs"
    def _use_py(self): vp = self._venv_py(); return str(vp) if vp.exists() else _find_system_python()

    def _on_global_scroll(self, event):
        """
        Handler MouseWheel duy nhất cho toàn app.
        Kiểm tra vị trí chuột → cuộn đúng canvas đang được hover.
        Tránh xung đột khi nhiều canvas cùng dùng bind_all.
        """
        mx, my = event.x_root, event.y_root
        for c in self._scroll_canvases:
            try:
                cx = c.winfo_rootx()
                cy = c.winfo_rooty()
                cw = c.winfo_width()
                ch = c.winfo_height()
                if cx <= mx <= cx + cw and cy <= my <= cy + ch:
                    c.yview_scroll(int(-1 * (event.delta / 120)), "units")
                    return "break"
            except Exception:
                pass

    def _browse_dir(self, var):
        d = filedialog.askdirectory()
        if d: var.set(d); self._preview_cmd()
    def _browse_file(self, var, ftypes):
        f = filedialog.askopenfilename(filetypes=ftypes)
        if f: var.set(f); self._preview_cmd()
    def _clear_log(self): self.log_box.delete("1.0", "end")
    def log(self, msg, tag=""):
        ts = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
    def _stop(self):
        if self._proc:
            try: self._proc.terminate(); self.log("Process đã dừng.", "warn")
            except: pass

    def _run(self, cmd, cwd=None, env=None, callback=None):
        _sys_py = _find_system_python()
        if isinstance(cmd, list) and cmd and cmd[0] in (sys.executable, _sys_py): cmd = [self._use_py()] + cmd[1:]
        def _w():
            self.after(0, self.log, "$ " + " ".join(str(x) for x in cmd), "info")
            _env = env or os.environ.copy()
            vs = Path(self.project_dir.get()) / ".venv" / "Scripts"
            if vs.exists():
                _env["PATH"] = str(vs) + os.pathsep + _env.get("PATH", "")
                _env["VIRTUAL_ENV"] = str(Path(self.project_dir.get()) / ".venv")
            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", cwd=cwd, env=_env, shell=isinstance(cmd, str),
                                     creationflags=subprocess.CREATE_NO_WINDOW)
                self._proc = p
                for line in p.stdout:
                    if line.rstrip(): self.after(0, self.log, line.rstrip(), "")
                p.wait()
                self._proc = None
                if p.returncode == 0:
                    self.after(0, self.log, "Hoàn thành lệnh!", "ok")
                    if callback: self.after(300, callback)
                else: self.after(0, self.log, f"Lỗi Exit Code: {p.returncode}", "err")
            except Exception as e: self.after(0, self.log, f"Lỗi: {e}", "err")
        threading.Thread(target=_w, daemon=True).start()

    def _pip_custom(self):
        pkg = self._pkg_var.get().strip()
        if pkg: self._run([self._use_py(), "-m", "pip", "install"] + pkg.split()); self._pkg_var.set("")

    def _mk_project_dir(self): Path(self.project_dir.get()).mkdir(parents=True, exist_ok=True); self.log(f"Đã tạo: {self.project_dir.get()}", "ok")
    def _check_venv(self):
        vp = self._venv_py()
        if not vp.exists():
            self.venv_status.set("Chưa có .venv")
            self._vbadge.config(fg=WARN)
            return
        def _w():
            try:
                r = subprocess.run([str(vp), "--version"], capture_output=True, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                self.after(0, self.venv_status.set, f"VENV OK: {(r.stdout+r.stderr).strip()}")
                self.after(0, self._vbadge.config, {"fg": TEAL})
            except: pass
        threading.Thread(target=_w, daemon=True).start()

    def _delete_venv(self):
        vd = Path(self.project_dir.get()) / ".venv"
        if vd.exists() and messagebox.askyesno("Xác nhận", f"Xóa .venv tại:\n{vd}"):
            shutil.rmtree(str(vd)); self.venv_status.set("Chưa có .venv"); self._vbadge.config(fg=WARN)

    def _clean_ckpt_sync(self, inp, out):
        """
        Dọn dẹp checkpoint bằng cách chạy script Python nhỏ qua venv python.
        KHÔNG import torch trực tiếp trong EXE — torch không được đóng gói vào EXE.
        Thay vào đó dùng subprocess gọi venv python (đã có torch thật).
        """
        import textwrap, tempfile

        # Script nhỏ tự chứa — chạy trong venv python (có torch đầy đủ)
        _CLEAN_SCRIPT = textwrap.dedent("""\
            import sys, pathlib, inspect

            inp  = sys.argv[1]
            out  = sys.argv[2]
            src  = sys.argv[3]

            import torch
            pathlib.PosixPath = pathlib.WindowsPath

            def conv(d):
                if isinstance(d, dict): return {k: conv(v) for k, v in d.items()}
                if isinstance(d, list): return [conv(i) for i in d]
                if isinstance(d, pathlib.PurePath): return str(d)
                return d

            ckpt = torch.load(inp, map_location="cpu", weights_only=False)
            ckpt = conv(ckpt)

            if src not in sys.path:
                sys.path.insert(0, src)
            try:
                from piper.train.vits.lightning import VitsModel
                valid   = set(inspect.signature(VitsModel.__init__).parameters.keys())
                invalid = set(ckpt.get("hyper_parameters", {}).keys()) - valid
                for p in invalid:
                    del ckpt["hyper_parameters"][p]
            except Exception:
                for p in ["channels", "sample_bytes", "dataset"]:
                    if "hyper_parameters" in ckpt and p in ckpt["hyper_parameters"]:
                        del ckpt["hyper_parameters"][p]

            torch.save(ckpt, out)
            print("OK")
        """)

        try:
            tmp = Path(tempfile.gettempdir()) / "_piper_clean_ckpt.py"
            tmp.write_text(_CLEAN_SCRIPT, encoding="utf-8")

            py  = self._use_py()
            src = str(self._src_dir())

            r = subprocess.run(
                [py, str(tmp), inp, out, src],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if r.returncode == 0 and "OK" in r.stdout:
                self.after(0, self.ckpt_path.set, out)
            else:
                err_msg = (r.stderr or r.stdout or "Không rõ lỗi").strip().splitlines()[-1]
                self.after(0, self.log, f"Lỗi dọn dẹp Checkpoint: {err_msg}", "err")
        except Exception as e:
            self.after(0, self.log, f"Lỗi dọn dẹp Checkpoint: {e}", "err")

    def _refresh_pre_label(self):
        pre = self._piper_dir() / "pretrained-model-cleaned.ckpt"
        if pre.exists(): self._pre_lbl.config(text=str(pre), fg=TEAL)
        else: self._pre_lbl.config(text="Chưa có model (Chạy step 09)", fg=WARN)

    def _validate(self):
        csv_p, aud_d = self.dataset_csv.get(), self.audio_dir.get()
        if not csv_p or not aud_d: return self.log("Chưa chọn đủ CSV và Audio Dir.", "err")
        def _w():
            try:
                lines = Path(csv_p).read_text(encoding="utf-8").strip().split("\n")
                missing = []
                for ln in lines:
                    parts = ln.strip().split("|")
                    if len(parts) < 2: continue
                    fname = parts[0].strip()
                    if fname.lower().endswith(".wav"): fname = fname[:-4]
                    if not (Path(aud_d) / f"{fname}.wav").exists(): missing.append(f"{fname}.wav")
                if missing: self.after(0, self.log, f"Thiếu {len(missing)} file WAV (VD: {missing[0]})", "warn")
                else: self.after(0, self.log, f"Tuyệt vời! {len(lines)} file hợp lệ.", "ok")
            except Exception as e: self.after(0, self.log, f"Lỗi: {e}", "err")
        threading.Thread(target=_w, daemon=True).start()

    def _fix_csv(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not f: return
        def _w():
            try:
                lines = Path(f).read_text(encoding="utf-8").strip().split("\n")
                out = []
                for ln in lines:
                    parts = ln.strip().split("|")
                    fname = parts[0].strip()
                    if fname.lower().endswith(".wav"): fname = fname[:-4]
                    if len(parts) >= 3: out.append(f"{fname}|{parts[2].strip()}")
                    elif len(parts) == 2: out.append(f"{fname}|{parts[1].strip()}")
                out_path = Path(f).parent / (Path(f).stem + "_fixed.csv")
                out_path.write_text("\n".join(out), encoding="utf-8")
                self.after(0, self.dataset_csv.set, str(out_path)); self.after(0, self._preview_cmd)
                self.after(0, self.log, f"Đã Fix xong: {out_path}", "ok")
            except Exception as e: self.after(0, self.log, f"Lỗi Fix CSV: {e}", "err")
        threading.Thread(target=_w, daemon=True).start()

    def _get_all_ckpts(self):
        ll, ckpts = self._lightning_dir(), []
        if ll.exists():
            for v in sorted(ll.iterdir()):
                ck = v / "checkpoints"
                if ck.exists():
                    for f in sorted(ck.glob("*.ckpt")): ckpts.append(f)
        return ckpts

    def _refresh_export_list(self):
        self._exp_lb.delete(0, "end")
        ckpts = list(reversed(self._get_all_ckpts()))
        pre = self._piper_dir() / "pretrained-model-cleaned.ckpt"
        if pre.exists(): ckpts.append(pre)
        if not ckpts: self._exp_lb.insert("end", "(Chưa có checkpoint nào)")
        else:
            for c in ckpts: self._exp_lb.insert("end", str(c))

    def _sel_exp(self, event=None):
        sel = self._exp_lb.curselection()
        if sel:
            v = self._exp_lb.get(sel[0])
            if v.endswith(".ckpt"): self.export_ckpt.set(v); self.log(f"Chọn để Export: {v}", "ok")

    def _pick_pretrained(self):
        pre = self._piper_dir() / "pretrained-model-cleaned.ckpt"
        if pre.exists(): self.ckpt_path.set(str(pre)); self._preview_cmd()
        else: self.log("Chưa có Pretrained, hãy tải ở Tab Setup Bước 09.", "warn")

    def _pick_latest_ckpt(self):
        ckpts = self._get_all_ckpts()
        if ckpts: self.ckpt_path.set(str(ckpts[-1])); self._preview_cmd()
        else: self.log("Chưa có checkpoint nào được sinh ra từ Train.", "warn")

    def _pick_latest_for_export(self):
        ckpts = self._get_all_ckpts()
        if ckpts: self.export_ckpt.set(str(ckpts[-1])); self.log(f"Đã chọn: {ckpts[-1]}", "ok")
        else: self.log("Không tìm thấy checkpoint.", "warn")

    def _preview_cmd(self):
        pd = self._piper_dir()
        self._cmd_box.delete("1.0", "end")
        self._cmd_box.insert("1.0",
            f"python -m piper.train fit \\\n"
            f"  --data.voice_name \"{self.voice_name.get()}\" \\\n"
            f"  --data.csv_path \"{self.dataset_csv.get()}\" \\\n"
            f"  --data.audio_dir \"{self.audio_dir.get()}\" \\\n"
            f"  --model.sample_rate {self.sample_rate.get()} \\\n"
            f"  --data.espeak_voice \"{self.espeak_lang.get()}\" \\\n"
            f"  --data.cache_dir \"{pd / 'cache'}\" \\\n"
            f"  --data.config_path \"{pd / 'config.json'}\" \\\n"
            f"  --data.batch_size {self.batch_size.get()} \\\n"
            f"  --ckpt_path \"{self.ckpt_path.get()}\" \\\n"
            f"  --trainer.max_epochs {self.max_epochs.get()}")

    def _patch_main(self):
        mp = self._src_dir() / "piper" / "train" / "__main__.py"
        if not mp.exists(): return
        patch = ("import torch\nimport pathlib\npathlib.PosixPath = pathlib.WindowsPath\n"
                 "torch.serialization.add_safe_globals([pathlib.PosixPath, pathlib.WindowsPath, pathlib.Path])\n")
        content = mp.read_text(encoding="utf-8")
        if "PosixPath = pathlib.WindowsPath" not in content:
            mp.write_text(patch + content, encoding="utf-8")

    def _start_train(self):
        if not Path(self.ckpt_path.get()).exists() or not self.dataset_csv.get() or not self.audio_dir.get():
            return self.log("Cấu hình Dataset hoặc Checkpoint chưa hợp lệ!", "err")
        self._patch_main()
        pd = self._piper_dir()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self._src_dir()) + os.pathsep + env.get("PYTHONPATH", "")
        self._run([self._use_py(), "-m", "piper.train", "fit",
            "--data.voice_name", self.voice_name.get(),
            "--data.csv_path", self.dataset_csv.get(),
            "--data.audio_dir", self.audio_dir.get(),
            "--model.sample_rate", self.sample_rate.get(),
            "--data.espeak_voice", self.espeak_lang.get(),
            "--data.cache_dir", str(pd / "cache"),
            "--data.config_path", str(pd / "config.json"),
            "--data.batch_size", self.batch_size.get(),
            "--ckpt_path", self.ckpt_path.get(),
            "--trainer.max_epochs", self.max_epochs.get()], cwd=str(self._src_dir()), env=env)

    def _export(self):
        ckpt = self.export_ckpt.get()
        if not ckpt or not Path(ckpt).exists(): return self.log("Chưa chọn file .ckpt để xuất.", "err")
        wd, name = Path(self.project_dir.get()), self.export_name.get() or "my_voice"
        onnx_out, cfg_src, cfg_out = wd / f"{name}.onnx", self._piper_dir() / "config.json", wd / f"{name}.onnx.json"
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self._src_dir()) + os.pathsep + env.get("PYTHONPATH", "")
        def _after():
            if cfg_src.exists():
                shutil.copy(str(cfg_src), str(cfg_out))
                self.infer_model.set(str(onnx_out))
                self.infer_config.set(str(cfg_out))
                self.log(f"Đã xuất cấu hình JSON thành công! Chuyển sang tab Chạy Thử.", "ok")
        self._run([self._use_py(), "-m", "piper.train.export_onnx", "--checkpoint", ckpt, "--output-file", str(onnx_out)], cwd=str(self._src_dir()), env=env, callback=_after)

    def _get_vn_proc(self):
        try:
            vn_path = Path(__file__).parent / "vn_text_processor.py"
            if vn_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("vn_text_processor", vn_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.process
            else:
                import vn_text_processor
                return vn_text_processor.process
        except: return None

    def _preview_vn_proc(self):
        txt = self._txt_in.get("1.0", "end").strip()
        if not txt: return
        proc = self._get_vn_proc()
        if proc:
            try:
                self._txt_out.config(state="normal")
                self._txt_out.delete("1.0", "end")
                self._txt_out.insert("1.0", proc(txt))
                self._txt_out.config(state="disabled")
            except Exception as e: self.log(f"Lỗi: {e}", "err")

    def _run_infer(self):
        import io, re
        mdl, cfg, raw = self.infer_model.get(), self.infer_config.get(), self._txt_in.get("1.0", "end").strip()
        if not mdl or not cfg or not raw: return self.log("Thiếu Model, Config hoặc Văn bản.", "err")
        
        txt = raw
        if self.use_vn_proc.get():
            proc = self._get_vn_proc()
            if proc:
                try: txt = proc(raw)
                except: pass
        out = Path(self.project_dir.get()) / "test_output.wav"
        src = str(self._src_dir())

        def _w():
            try:
                if src not in sys.path: sys.path.insert(0, src)
                vsite = Path(self.project_dir.get()) / ".venv" / "Lib" / "site-packages"
                if vsite.exists() and str(vsite) not in sys.path: sys.path.insert(0, str(vsite))
                self.after(0, self.log, "Đang tổng hợp giọng nói...", "info")
                from piper import PiperVoice, SynthesisConfig
                voice = PiperVoice.load(model_path=mdl, config_path=cfg, use_cuda=False)
                sc = SynthesisConfig(volume=1.0, length_scale=float(self.length_scale.get()), noise_scale=float(self.noise_scale.get()), noise_w_scale=float(self.noise_w.get()), normalize_audio=False)
                sr, combined_pcm = voice.config.sample_rate, bytearray()
                parts = re.split(r"([.,!?;:\n]+)", txt)
                for i in range(0, len(parts), 2):
                    phrase = parts[i].strip()
                    punct = parts[i + 1] if i + 1 < len(parts) else ""
                    if phrase:
                        buf = io.BytesIO()
                        with wave.open(buf, "wb") as temp_wf: voice.synthesize_wav(phrase, temp_wf, syn_config=sc)
                        buf.seek(0)
                        with wave.open(buf, "rb") as read_wf: combined_pcm.extend(read_wf.readframes(read_wf.getnframes()))
                    pause = 0.6 if any(p in punct for p in [".", "!", "?", "\n"]) else (0.25 if any(p in punct for p in [",", ";", ":"]) else 0.0)
                    if pause > 0: combined_pcm.extend(b"\x00" * int(pause * sr) * 2)
                with wave.open(str(out), "wb") as final_wf:
                    final_wf.setnchannels(1); final_wf.setsampwidth(2); final_wf.setframerate(sr); final_wf.writeframes(combined_pcm)
                self.after(0, self.log, f"Đã lưu Audio thành công tại: {out}", "ok")
                self.after(0, self._play_wav)
            except Exception as e: self.after(0, self.log, f"Lỗi Infer: {e}", "err")
        threading.Thread(target=_w, daemon=True).start()

    def _play_wav(self):
        out = Path(self.project_dir.get()) / "test_output.wav"
        if out.exists(): os.startfile(str(out))

# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # freeze_support() bắt buộc khi dùng multiprocessing trong PyInstaller EXE.
    # Nếu không có dòng này, mỗi subprocess sẽ mở thêm 1 cửa sổ app mới.
    import multiprocessing
    multiprocessing.freeze_support()
    App().mainloop()