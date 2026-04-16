"""
=============================================================
  FORENSIC IMAGE ANNOTATOR  -  Strumento di analisi forense
  By Visi@n - Ethical Hacker            v. 0.2
=============================================================
Novita v0.2:
  - Modalita BATCH: carica tutti i frame di una directory
  - Navigazione frame con pulsanti e frecce tastiera
  - Stato annotazioni mantenuto per ogni frame
  - Salvataggio frame singolo in qualsiasi momento
  - Barra di avanzamento batch con indicatore frame
=============================================================
Requisiti:
    pip install pillow

Utilizzo:
    python image_annotator.py
=============================================================
"""

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageTk
import os
import datetime
import hashlib
import zipfile
import re

APP_VERSION   = "v. 0.2"
APP_COPYRIGHT = "By Visi@n  -  Ethical Hacker"

DEFAULT_COLOR     = "#FF0000"
DEFAULT_THICKNESS = 3
DEFAULT_ZOOM      = 3
CANVAS_MAX_W      = 1060
CANVAS_MAX_H      = 680
FONT_LABEL        = ("Segoe UI", 10)
FONT_TITLE        = ("Segoe UI", 11, "bold")
HEADER_H          = 70
HEADER_BG         = "#1e1e2e"
IMG_EXTS          = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}


def _load_font(size):
    for path in ["arial.ttf", "Arial.ttf",
                 "C:/Windows/Fonts/arial.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                 "/System/Library/Fonts/Helvetica.ttc"]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _textbbox(draw, xy, text, font):
    try:
        return draw.textbbox(xy, text, font=font)
    except AttributeError:
        w, h = draw.textsize(text, font=font)
        return (xy[0], xy[1], xy[0] + w, xy[1] + h)


def _sanitize(s):
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    s = re.sub(r'\s+', '_', s.strip())
    return s or 'SENZA_NOME'


class ForensicAnnotator:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Forensic Image Annotator {APP_VERSION}  |  {APP_COPYRIGHT}")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        self.orig_image   = None
        self.work_image   = None
        self.display_img  = None
        self.scale_factor = 1.0
        self.current_path = ""

        self.annotations = []
        self.start_x = self.start_y = 0
        self.rect_id = None

        # batch state
        self.batch_files       = []
        self.batch_index       = -1
        self.batch_annotations = {}   # path -> list of ann dicts
        self.batch_saved       = {}   # path -> bool

        self.ann_color   = tk.StringVar(value=DEFAULT_COLOR)
        self.thickness   = tk.IntVar(value=DEFAULT_THICKNESS)
        self.zoom_factor = tk.IntVar(value=DEFAULT_ZOOM)
        self.case_number = tk.StringVar(value="")
        self.operator    = tk.StringVar(value="")
        self.note_text   = tk.StringVar(value="")
        self.draw_mode   = tk.StringVar(value="rect")

        self._build_ui()
        self._bind_keys()

    # ════════════════════════════════════
    #  UI
    # ════════════════════════════════════
    def _build_ui(self):
        top = tk.Frame(self.root, bg="#181825", pady=5, padx=8)
        top.pack(side=tk.TOP, fill=tk.X)

        tk.Label(top, text=f"FORENSIC IMAGE ANNOTATOR  {APP_VERSION}",
                 font=("Segoe UI", 13, "bold"),
                 fg="#cba6f7", bg="#181825").pack(side=tk.LEFT, padx=6)

        tk.Label(top, text=APP_COPYRIGHT,
                 font=("Segoe UI", 9, "italic"),
                 fg="#6c7086", bg="#181825").pack(side=tk.RIGHT, padx=10)

        for txt, cmd, bg, fg in [
            ("Singola",      self._open_image,   "#313244", "white"),
            ("Cartella",     self._open_folder,  "#45475a", "#cba6f7"),
            ("Salva frame",  self._save_current, "#89b4fa", "#1e1e2e"),
            ("Salva tutto",  self._save_all,     "#a6e3a1", "#1e1e2e"),
            ("Annulla",      self._undo,         "#f38ba8", "#1e1e2e"),
            ("Reset",        self._reset,        "#585b70", "white"),
        ]:
            tk.Button(top, text=txt, command=cmd, bg=bg, fg=fg,
                      font=FONT_LABEL, relief=tk.FLAT, padx=9
                      ).pack(side=tk.LEFT, padx=3)

        main = tk.Frame(self.root, bg="#1e1e2e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        left = tk.Frame(main, bg="#1e1e2e")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left, cursor="crosshair",
                                bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas_bind()

        self._build_nav_bar(left)

        self.status_var = tk.StringVar(value="Aprire un'immagine o una cartella per iniziare.")
        tk.Label(left, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg="#a6adc8", bg="#1e1e2e", anchor="w").pack(fill=tk.X, pady=2)

        right = tk.Frame(main, bg="#181825", width=255)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        right.pack_propagate(False)
        self._build_controls(right)

    def _build_nav_bar(self, parent):
        nav = tk.Frame(parent, bg="#181825", pady=4)
        nav.pack(fill=tk.X, pady=(4, 0))

        for txt, cmd in [("<<", self._go_first), ("<", self._go_prev),
                         (">",  self._go_next),  (">>", self._go_last)]:
            tk.Button(nav, text=txt, command=cmd, bg="#313244", fg="white",
                      font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
                      width=3).pack(side=tk.LEFT, padx=2)

        self.frame_counter_var = tk.StringVar(value="---")
        tk.Label(nav, textvariable=self.frame_counter_var,
                 font=("Segoe UI", 10, "bold"),
                 fg="#cdd6f4", bg="#181825", width=16).pack(side=tk.LEFT, padx=8)

        self.frame_name_var = tk.StringVar(value="")
        tk.Label(nav, textvariable=self.frame_name_var,
                 font=("Segoe UI", 9), fg="#a6adc8", bg="#181825",
                 anchor="w").pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        self.saved_indicator = tk.Label(nav, text="", font=("Segoe UI", 9, "bold"),
                                        bg="#181825", width=14)
        self.saved_indicator.pack(side=tk.RIGHT, padx=8)

        self.progress_canvas = tk.Canvas(parent, height=6, bg="#313244",
                                          highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(2, 0))

    def _build_controls(self, parent):
        def section(text):
            tk.Label(parent, text=text, font=FONT_TITLE,
                     fg="#cba6f7", bg="#181825").pack(anchor="w", padx=10, pady=(10, 2))

        section("Dati del verbale")
        for label, var in [("N. caso / procedimento:", self.case_number),
                            ("Operatore / P.G.:",       self.operator)]:
            tk.Label(parent, text=label, font=FONT_LABEL,
                     fg="#cdd6f4", bg="#181825").pack(anchor="w", padx=12)
            tk.Entry(parent, textvariable=var, font=FONT_LABEL,
                     bg="#313244", fg="white", insertbackground="white",
                     relief=tk.FLAT, width=27).pack(padx=12, pady=2)

        section("Strumento")
        for label, val in [("Rettangolo", "rect"),
                            ("Freccia",    "arrow"),
                            ("Testo",      "text")]:
            tk.Radiobutton(parent, text=label, variable=self.draw_mode,
                           value=val, font=FONT_LABEL, fg="#cdd6f4", bg="#181825",
                           selectcolor="#313244", activebackground="#181825",
                           activeforeground="white").pack(anchor="w", padx=14)

        tk.Label(parent, text="Testo annotazione:", font=FONT_LABEL,
                 fg="#cdd6f4", bg="#181825").pack(anchor="w", padx=12, pady=(6, 0))
        tk.Entry(parent, textvariable=self.note_text, font=FONT_LABEL,
                 bg="#313244", fg="white", insertbackground="white",
                 relief=tk.FLAT, width=27).pack(padx=12, pady=2)

        section("Colore")
        cf = tk.Frame(parent, bg="#181825")
        cf.pack(padx=12, fill=tk.X)
        self.color_btn = tk.Button(cf, bg=self.ann_color.get(),
                                   width=3, relief=tk.FLAT, command=self._pick_color)
        self.color_btn.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(cf, textvariable=self.ann_color, font=FONT_LABEL,
                 fg="#cdd6f4", bg="#181825").pack(side=tk.LEFT)
        pf = tk.Frame(parent, bg="#181825")
        pf.pack(padx=12, pady=3, fill=tk.X)
        for col in ["#FF0000", "#FF8C00", "#FFFF00", "#00FF7F", "#00BFFF", "#FF69B4"]:
            tk.Button(pf, bg=col, width=2, relief=tk.FLAT,
                      command=lambda c=col: self._set_color(c)).pack(side=tk.LEFT, padx=1)

        section("Spessore bordo")
        tk.Scale(parent, from_=1, to=10, orient=tk.HORIZONTAL,
                 variable=self.thickness, font=FONT_LABEL,
                 bg="#181825", fg="#cdd6f4", troughcolor="#313244",
                 highlightthickness=0, length=195).pack(padx=12)

        section("Zoom ritaglio (x)")
        tk.Scale(parent, from_=2, to=8, orient=tk.HORIZONTAL,
                 variable=self.zoom_factor, font=FONT_LABEL,
                 bg="#181825", fg="#cdd6f4", troughcolor="#313244",
                 highlightthickness=0, length=195).pack(padx=12)

        section("Annotazioni frame corrente")
        lf = tk.Frame(parent, bg="#181825")
        lf.pack(padx=12, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(lf, bg="#313244")
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ann_list = tk.Listbox(lf, font=("Segoe UI", 8),
                                   bg="#313244", fg="#cdd6f4",
                                   selectbackground="#cba6f7",
                                   yscrollcommand=sb.set,
                                   relief=tk.FLAT, height=6)
        self.ann_list.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.ann_list.yview)

        section("Riepilogo batch")
        self.batch_summary_var = tk.StringVar(value="Nessuna cartella aperta.")
        tk.Label(parent, textvariable=self.batch_summary_var,
                 font=("Segoe UI", 8), fg="#a6adc8", bg="#181825",
                 justify=tk.LEFT, wraplength=230).pack(padx=12, anchor="w")

    # ════════════════════════════════════
    #  KEYBINDINGS
    # ════════════════════════════════════
    def _bind_keys(self):
        self.root.bind("<Left>",       lambda e: self._go_prev())
        self.root.bind("<Right>",      lambda e: self._go_next())
        self.root.bind("<Home>",       lambda e: self._go_first())
        self.root.bind("<End>",        lambda e: self._go_last())
        self.root.bind("<Control-s>",  lambda e: self._save_current())
        self.root.bind("<Control-z>",  lambda e: self._undo())

    # ════════════════════════════════════
    #  APERTURA
    # ════════════════════════════════════
    def _open_image(self):
        path = filedialog.askopenfilename(
            title="Seleziona immagine",
            filetypes=[("Immagini", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                       ("Tutti i file", "*.*")])
        if not path:
            return
        self.batch_files       = [path]
        self.batch_index       = 0
        self.batch_annotations = {}
        self.batch_saved       = {}
        self._load_frame(0)
        self._update_batch_summary()

    def _open_folder(self):
        folder = filedialog.askdirectory(title="Seleziona cartella con i frame")
        if not folder:
            return
        files = sorted([
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.splitext(f)[1].lower() in IMG_EXTS
        ])
        if not files:
            messagebox.showwarning("Cartella vuota",
                                   "Nessuna immagine trovata nella cartella selezionata.")
            return
        self.batch_files       = files
        self.batch_index       = 0
        self.batch_annotations = {}
        self.batch_saved       = {}
        self._load_frame(0)
        self._update_batch_summary()
        self.status_var.set(
            f"Batch caricata: {len(files)} frame da '{os.path.basename(folder)}'  "
            f"--  usa < > o frecce tastiera per navigare")

    # ════════════════════════════════════
    #  CARICAMENTO FRAME
    # ════════════════════════════════════
    def _load_frame(self, index):
        if self.current_path and self.batch_files:
            self.batch_annotations[self.current_path] = list(self.annotations)

        self.batch_index  = index
        path              = self.batch_files[index]
        self.current_path = path

        self.orig_image  = Image.open(path).convert("RGB")
        self.work_image  = self.orig_image.copy()
        self.annotations = list(self.batch_annotations.get(path, []))

        for ann in self.annotations:
            self._draw_annotation(self.work_image, ann)

        self.ann_list.delete(0, tk.END)
        for ann in self.annotations:
            self._list_insert(ann)

        self._fit_canvas()
        self._refresh_canvas()
        self._update_nav()

    # ════════════════════════════════════
    #  NAVIGAZIONE
    # ════════════════════════════════════
    def _go_next(self):
        if self.batch_files and self.batch_index < len(self.batch_files) - 1:
            self._load_frame(self.batch_index + 1)

    def _go_prev(self):
        if self.batch_files and self.batch_index > 0:
            self._load_frame(self.batch_index - 1)

    def _go_first(self):
        if self.batch_files:
            self._load_frame(0)

    def _go_last(self):
        if self.batch_files:
            self._load_frame(len(self.batch_files) - 1)

    def _update_nav(self):
        if not self.batch_files:
            self.frame_counter_var.set("---")
            self.frame_name_var.set("")
            self.saved_indicator.config(text="", bg="#181825")
            return

        n   = len(self.batch_files)
        idx = self.batch_index
        self.frame_counter_var.set(f"Frame  {idx+1}  /  {n}")
        self.frame_name_var.set(os.path.basename(self.current_path))

        if self.batch_saved.get(self.current_path):
            self.saved_indicator.config(text="OK  Salvato",
                                        fg="#a6e3a1", bg="#181825")
        elif self.batch_annotations.get(self.current_path):
            self.saved_indicator.config(text="!  Non salvato",
                                        fg="#f38ba8", bg="#181825")
        else:
            self.saved_indicator.config(text="o  Nessuna ann.",
                                        fg="#6c7086", bg="#181825")

        self.progress_canvas.update_idletasks()
        pw = self.progress_canvas.winfo_width() or 800
        fw = int(pw * (idx + 1) / n)
        self.progress_canvas.delete("all")
        self.progress_canvas.create_rectangle(0, 0, fw, 6, fill="#cba6f7", outline="")

        anns = self.batch_annotations.get(self.current_path, self.annotations)
        self.status_var.set(
            f"[{idx+1}/{n}]  {os.path.basename(self.current_path)}  "
            f"--  {self.orig_image.width}x{self.orig_image.height} px  "
            f"--  {len(anns)} annotazioni")

    def _update_batch_summary(self):
        if not self.batch_files:
            self.batch_summary_var.set("Nessuna cartella aperta.")
            return
        n       = len(self.batch_files)
        done    = sum(1 for p in self.batch_files if self.batch_saved.get(p))
        ann_tot = sum(len(v) for v in self.batch_annotations.values())
        self.batch_summary_var.set(
            f"Frame totali:    {n}\n"
            f"Frame salvati:   {done}\n"
            f"Annotazioni tot: {ann_tot}")

    # ════════════════════════════════════
    #  CANVAS
    # ════════════════════════════════════
    def _fit_canvas(self):
        if not self.orig_image:
            return
        w, h  = self.orig_image.size
        scale = min(CANVAS_MAX_W / w, CANVAS_MAX_H / h, 1.0)
        self.scale_factor = scale
        self.canvas.config(width=int(w * scale), height=int(h * scale))

    def _refresh_canvas(self):
        if not self.work_image:
            return
        w = int(self.work_image.width  * self.scale_factor)
        h = int(self.work_image.height * self.scale_factor)
        display          = self.work_image.resize((w, h), Image.LANCZOS)
        self.display_img = ImageTk.PhotoImage(display)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_img)

    def _canvas_bind(self):
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _canvas_to_image(self, cx, cy):
        return int(cx / self.scale_factor), int(cy / self.scale_factor)

    # ════════════════════════════════════
    #  MOUSE
    # ════════════════════════════════════
    def _on_press(self, event):
        if not self.orig_image:
            return
        self.start_x, self.start_y = event.x, event.y
        self.rect_id = None

    def _on_drag(self, event):
        if not self.orig_image:
            return
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        color = self.ann_color.get()
        if self.draw_mode.get() == "arrow":
            self.rect_id = self.canvas.create_line(
                self.start_x, self.start_y, event.x, event.y,
                fill=color, width=2, arrow=tk.LAST)
        else:
            self.rect_id = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y,
                outline=color, width=2, dash=(4, 2))

    def _on_release(self, event):
        if not self.orig_image:
            return
        if self.rect_id:
            self.canvas.delete(self.rect_id)
            self.rect_id = None
        x1, y1 = self._canvas_to_image(self.start_x, self.start_y)
        x2, y2 = self._canvas_to_image(event.x, event.y)
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        if abs(x2-x1) < 5 or abs(y2-y1) < 5:
            return
        ann = dict(
            idx=len(self.annotations)+1,
            mode=self.draw_mode.get(),
            x1=x1, y1=y1, x2=x2, y2=y2,
            color=self.ann_color.get(),
            thickness=self.thickness.get(),
            note=self.note_text.get(),
            ts=datetime.datetime.now().strftime("%H:%M:%S"),
            zoom=self.zoom_factor.get(),
        )
        self.annotations.append(ann)
        self.batch_annotations[self.current_path] = list(self.annotations)
        self.batch_saved[self.current_path] = False
        self._draw_annotation(self.work_image, ann)
        self._list_insert(ann)
        self._refresh_canvas()
        self._update_nav()
        self._update_batch_summary()

    def _list_insert(self, ann):
        label = f"[{ann['idx']}] {ann['mode'].upper()} ({ann['x1']},{ann['y1']})->({ann['x2']},{ann['y2']})  {ann['ts']}"
        if ann.get("note"):
            label += f'  "{ann["note"]}"'
        self.ann_list.insert(tk.END, label)
        self.ann_list.see(tk.END)

    # ════════════════════════════════════
    #  DISEGNO
    # ════════════════════════════════════
    def _draw_annotation(self, img, ann):
        draw  = ImageDraw.Draw(img)
        color = ann["color"]
        thick = ann["thickness"]
        x1, y1, x2, y2 = ann["x1"], ann["y1"], ann["x2"], ann["y2"]
        mode  = ann["mode"]
        note  = ann.get("note", "")
        idx   = ann["idx"]

        if mode == "rect":
            draw.rectangle([x1, y1, x2, y2], outline=color, width=thick)
            s = max(8, thick*3)
            for cx, cy in [(x1,y1),(x2,y1),(x1,y2),(x2,y2)]:
                draw.rectangle([cx-s//2, cy-s//2, cx+s//2, cy+s//2], fill=color)

        elif mode == "arrow":
            draw.line([x1, y1, x2, y2], fill=color, width=thick)
            dx, dy = x2-x1, y2-y1
            length = max((dx**2+dy**2)**0.5, 1)
            ux, uy = dx/length, dy/length
            px, py = -uy, ux
            h = 18
            p1 = (int(x2-h*ux+h*0.4*px), int(y2-h*uy+h*0.4*py))
            p2 = (int(x2-h*ux-h*0.4*px), int(y2-h*uy-h*0.4*py))
            draw.polygon([(x2,y2), p1, p2], fill=color)

        elif mode == "text":
            draw.rectangle([x1, y1, x2, y2], outline=color, width=thick)
            if note:
                fs   = max(14, min(thick*6, (y2-y1)//2, 48))
                font = _load_font(fs)
                bb   = _textbbox(draw, (0,0), note, font)
                tw, th = bb[2]-bb[0], bb[3]-bb[1]
                tx = x1+max(0, ((x2-x1)-tw)//2)
                ty = y1+max(0, ((y2-y1)-th)//2)
                draw.text((tx+2, ty+2), note, fill="#000000", font=font)
                draw.text((tx,   ty),   note, fill=color,     font=font)

        fs   = max(14, thick*5)
        font = _load_font(fs)
        lbl  = f" {idx} "
        if note and mode != "text":
            lbl += f" {note}"
        tx = x1
        ty = max(0, y1-fs-4)
        bb = _textbbox(draw, (tx,ty), lbl, font)
        draw.rectangle(bb, fill=color)
        draw.text((tx, ty), lbl, fill="white", font=font)

    # ════════════════════════════════════
    #  HEADER FORENSE
    # ════════════════════════════════════
    def _make_header(self, width, ann):
        header = Image.new("RGB", (width, HEADER_H), HEADER_BG)
        dh = ImageDraw.Draw(header)
        fh = _load_font(13)
        fs = _load_font(11)
        line1 = (f"Ann. #{ann['idx']}  |  Caso: {self.case_number.get() or '---'}  |  "
                 f"Op: {self.operator.get() or '---'}  |  {ann['ts']}")
        line2 = (f"Coord.: ({ann['x1']},{ann['y1']}) -> ({ann['x2']},{ann['y2']})"
                 f"  |  Zoom: x{ann['zoom']}  |  {ann['mode'].upper()}")
        line3 = f"File: {os.path.basename(self.current_path)}"
        if ann.get("note"):
            line3 += f"  |  Nota: {ann['note']}"
        dh.text((10,  5), line1, fill="#cba6f7", font=fh)
        dh.text((10, 24), line2, fill="#a6adc8", font=fs)
        dh.text((10, 44), line3, fill="#f38ba8", font=fs)
        copy_txt = f"Forensic Image Annotator {APP_VERSION}  |  {APP_COPYRIGHT}"
        try:
            bb = dh.textbbox((0,0), copy_txt, font=fs)
            tw = bb[2]-bb[0]
        except Exception:
            tw = len(copy_txt)*6
        dh.text((max(0, width-tw-6), 56), copy_txt, fill="#45475a", font=fs)
        return header

    # ════════════════════════════════════
    #  COMPOSITA FORENSE
    # ════════════════════════════════════
    def _make_composite(self, ann, scene, zoomed_crop):
        color = ann["color"]
        thick = max(2, ann["thickness"])
        ratio = min(700 / scene.height, 1.0)
        sw    = max(1, int(scene.width*ratio))
        sh    = max(1, int(scene.height*ratio))
        scene_rs = scene.resize((sw, sh), Image.LANCZOS)
        rx1 = int(ann["x1"]*ratio)
        ry1 = int(ann["y1"]*ratio)
        rx2 = int(ann["x2"]*ratio)
        ry2 = int(ann["y2"]*ratio)
        mzh = sh-20
        if zoomed_crop.height > mzh:
            zr = mzh/zoomed_crop.height
            zoomed_crop = zoomed_crop.resize(
                (max(1, int(zoomed_crop.width*zr)),
                 max(1, int(zoomed_crop.height*zr))), Image.LANCZOS)
        zw, zh    = zoomed_crop.size
        gap       = 30
        divider_h = 4
        body_h    = max(sh, zh)
        total_w   = sw+gap+zw
        total_h   = HEADER_H+divider_h+body_h
        composite = Image.new("RGB", (total_w, total_h), HEADER_BG)
        composite.paste(self._make_header(total_w, ann), (0, 0))
        dc = ImageDraw.Draw(composite)
        dc.rectangle([0, HEADER_H, total_w, HEADER_H+divider_h], fill=color)
        sy = HEADER_H+divider_h+(body_h-sh)//2
        composite.paste(scene_rs, (0, sy))
        ax1, ay1, ax2, ay2 = rx1, sy+ry1, rx2, sy+ry2
        dc.rectangle([ax1, ay1, ax2, ay2], outline=color, width=thick+1)
        zx = sw+gap
        zy = HEADER_H+divider_h+(body_h-zh)//2
        composite.paste(zoomed_crop, (zx, zy))
        dc.rectangle([zx, zy, zx+zw-1, zy+zh-1], outline=color, width=thick+1)
        sel_tr, sel_br = (ax2, ay1), (ax2, ay2)
        pan_tl, pan_bl = (zx, zy),   (zx, zy+zh)
        overlay = Image.new("RGBA", composite.size, (0,0,0,0))
        do = ImageDraw.Draw(overlay)
        r,g,b = tuple(int(color.lstrip("#")[i:i+2],16) for i in (0,2,4))
        do.polygon([sel_tr, sel_br, pan_bl, pan_tl], fill=(r,g,b,45))
        composite = Image.alpha_composite(composite.convert("RGBA"), overlay).convert("RGB")
        dc2 = ImageDraw.Draw(composite)
        dc2.line([sel_tr, pan_tl], fill=color, width=thick)
        dc2.line([sel_br, pan_bl], fill=color, width=thick)
        fl = _load_font(13)
        dc2.text((8, sy+sh-22),       "SCENA COMPLETA",          fill=color, font=fl)
        dc2.text((zx+6, zy+5),        f"DETTAGLIO  x{ann['zoom']}", fill=color, font=fl)
        return composite

    # ════════════════════════════════════
    #  SALVATAGGIO FRAME SINGOLO
    # ════════════════════════════════════
    def _save_current(self):
        if not self.orig_image:
            messagebox.showinfo("Nessuna immagine", "Nessun frame aperto.")
            return
        if not self.annotations:
            if not messagebox.askyesno("Nessuna annotazione",
                                       "Il frame corrente non ha annotazioni.\nSalvare comunque?"):
                return
        base = filedialog.askdirectory(title="Scegli la cartella di destinazione")
        if not base:
            return
        self._do_save_frame(self.current_path, self.orig_image,
                            self.work_image, self.annotations, base, show_msg=True)
        self.batch_saved[self.current_path] = True
        self._update_nav()
        self._update_batch_summary()

    # ════════════════════════════════════
    #  SALVATAGGIO TUTTI
    # ════════════════════════════════════
    def _save_all(self):
        if self.current_path:
            self.batch_annotations[self.current_path] = list(self.annotations)
        annotated = [(p, anns) for p, anns in self.batch_annotations.items() if anns]
        if not annotated:
            messagebox.showinfo("Nessuna annotazione",
                                "Nessun frame ha annotazioni da salvare.")
            return
        base = filedialog.askdirectory(title="Scegli la cartella di destinazione")
        if not base:
            return
        errors = []
        for path, anns in annotated:
            try:
                orig = Image.open(path).convert("RGB")
                work = orig.copy()
                for ann in anns:
                    self._draw_annotation(work, ann)
                self._do_save_frame(path, orig, work, anns, base, show_msg=False)
                self.batch_saved[path] = True
            except Exception as ex:
                errors.append(f"{os.path.basename(path)}: {ex}")
        self._update_nav()
        self._update_batch_summary()
        msg = f"Salvati {len(annotated)} frame annotati.\n\nCartella base: {base}"
        if errors:
            msg += "\n\nErrori:\n" + "\n".join(errors)
        messagebox.showinfo("Salvataggio completato", msg)

    # ════════════════════════════════════
    #  NUCLEO SALVATAGGIO
    # ════════════════════════════════════
    def _do_save_frame(self, path, orig, work, annotations, base, show_msg=False):
        case       = _sanitize(self.case_number.get())
        ts         = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stem       = os.path.splitext(os.path.basename(path))[0]
        case_dir   = os.path.join(base, case)
        sess_dir   = os.path.join(case_dir, f"{stem}_{ts}")
        os.makedirs(sess_dir, exist_ok=True)
        saved = []

        # 1. Scena annotata
        fp = os.path.join(sess_dir, f"{stem}_{ts}_ANNOTATA.jpg")
        work.save(fp, quality=95)
        saved.append(fp)

        for ann in annotations:
            x1,y1,x2,y2 = ann["x1"],ann["y1"],ann["x2"],ann["y2"]
            crop   = orig.crop((x1,y1,x2,y2))
            zf     = ann["zoom"]
            zoomed = crop.resize((crop.width*zf, crop.height*zf), Image.LANCZOS)
            dz     = ImageDraw.Draw(zoomed)
            dz.rectangle([0,0,zoomed.width-1,zoomed.height-1],
                          outline=ann["color"], width=ann["thickness"]+2)

            # 2. Ritaglio zoomato
            hdr  = self._make_header(zoomed.width, ann)
            cout = Image.new("RGB", (zoomed.width, HEADER_H+zoomed.height), HEADER_BG)
            cout.paste(hdr,    (0, 0))
            cout.paste(zoomed, (0, HEADER_H))
            cp = os.path.join(sess_dir, f"{stem}_{ts}_RITAGLIO_{ann['idx']:02d}.jpg")
            cout.save(cp, quality=95)
            saved.append(cp)

            # 3. Composita
            comp = self._make_composite(ann, work.copy(), zoomed)
            cpp  = os.path.join(sess_dir, f"{stem}_{ts}_COMPOSITA_{ann['idx']:02d}.jpg")
            comp.save(cpp, quality=95)
            saved.append(cpp)

        # 4. Report
        rp = os.path.join(sess_dir, f"{stem}_{ts}_REPORT.txt")
        with open(rp, "w", encoding="utf-8") as f:
            f.write("="*64+"\n")
            f.write(f"  REPORT ANNOTAZIONI FORENSI  -  {APP_VERSION}\n")
            f.write("="*64+"\n")
            f.write(f"Data/Ora:       {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"N. caso:        {self.case_number.get() or '---'}\n")
            f.write(f"Operatore P.G.: {self.operator.get() or '---'}\n")
            f.write(f"File origine:   {os.path.basename(path)}\n")
            f.write(f"Dimensione:     {orig.width}x{orig.height} px\n")
            f.write("-"*64+"\n")
            for ann in annotations:
                f.write(f"\nAnnotazione #{ann['idx']}\n")
                f.write(f"  Tipo:       {ann['mode'].upper()}\n")
                f.write(f"  Coord. TL:  ({ann['x1']}, {ann['y1']})\n")
                f.write(f"  Coord. BR:  ({ann['x2']}, {ann['y2']})\n")
                f.write(f"  Area (px):  {ann['x2']-ann['x1']} x {ann['y2']-ann['y1']}\n")
                f.write(f"  Colore:     {ann['color']}\n")
                f.write(f"  Zoom:       x{ann['zoom']}\n")
                f.write(f"  Orario:     {ann['ts']}\n")
                if ann.get("note"):
                    f.write(f"  Nota:       {ann['note']}\n")
        saved.append(rp)

        # 5. Chain of Custody SHA-256
        mp = os.path.join(sess_dir, f"{stem}_{ts}_CHAIN_OF_CUSTODY.txt")
        with open(mp, "w", encoding="utf-8") as mf:
            mf.write("="*72+"\n")
            mf.write(f"  CHAIN OF CUSTODY  -  MANIFEST SHA-256\n")
            mf.write(f"  Forensic Image Annotator {APP_VERSION}  |  {APP_COPYRIGHT}\n")
            mf.write("="*72+"\n")
            mf.write(f"Data/Ora:       {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            mf.write(f"N. caso:        {self.case_number.get() or '---'}\n")
            mf.write(f"Operatore P.G.: {self.operator.get() or '---'}\n")
            mf.write(f"Sessione:       {sess_dir}\n")
            mf.write("-"*72+"\n")
            mf.write(f"{'FILE':<45} {'SHA-256'}\n")
            mf.write("-"*72+"\n")
            for fp2 in sorted(saved):
                h = hashlib.sha256()
                with open(fp2, "rb") as bf:
                    for chunk in iter(lambda: bf.read(65536), b""):
                        h.update(chunk)
                mf.write(f"{os.path.basename(fp2):<45} {h.hexdigest()}\n")
            mf.write("="*72+"\n")
            mf.write("  Documento valido per la catena di custodia digitale.\n")
            mf.write("="*72+"\n")
        saved.append(mp)

        # 6. ZIP
        zp = os.path.join(case_dir, f"{stem}_{ts}_ARCHIVIO.zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for fp2 in saved:
                if os.path.isfile(fp2):
                    zf.write(fp2, arcname=os.path.basename(fp2))

        if show_msg:
            messagebox.showinfo("Frame salvato",
                                f"Salvato correttamente:\n\n{sess_dir}\n\n"
                                f"{len(saved)} file + archivio ZIP")

    # ════════════════════════════════════
    #  UNDO / RESET
    # ════════════════════════════════════
    def _undo(self):
        if not self.annotations:
            return
        self.annotations.pop()
        self.ann_list.delete(tk.END)
        self.batch_annotations[self.current_path] = list(self.annotations)
        self.work_image = self.orig_image.copy()
        for ann in self.annotations:
            self._draw_annotation(self.work_image, ann)
        self._refresh_canvas()
        self._update_nav()
        self._update_batch_summary()

    def _reset(self):
        if not self.orig_image:
            return
        if messagebox.askyesno("Conferma reset",
                               "Rimuovere tutte le annotazioni del frame corrente?"):
            self.annotations = []
            self.ann_list.delete(0, tk.END)
            self.batch_annotations[self.current_path] = []
            self.batch_saved[self.current_path] = False
            self.work_image = self.orig_image.copy()
            self._refresh_canvas()
            self._update_nav()
            self._update_batch_summary()

    # ════════════════════════════════════
    #  COLORE
    # ════════════════════════════════════
    def _pick_color(self):
        color = colorchooser.askcolor(
            color=self.ann_color.get(), title="Scegli colore annotazione")[1]
        if color:
            self._set_color(color)

    def _set_color(self, color):
        self.ann_color.set(color)
        self.color_btn.configure(bg=color)


if __name__ == "__main__":
    root = tk.Tk()
    ForensicAnnotator(root)
    root.mainloop()
