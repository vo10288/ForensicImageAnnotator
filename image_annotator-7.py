"""
=============================================================
  FORENSIC IMAGE ANNOTATOR  –  Strumento di analisi forense
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

APP_VERSION   = "v. 0.1"
APP_COPYRIGHT = "By Visi@n  – https://www.broi.it"
APP_TITLE     = f"Forensic Image Annotator {APP_VERSION}  │  {APP_COPYRIGHT}" 


# ──────────────────────────────────────────────────────────
#  Costanti di default
# ──────────────────────────────────────────────────────────
DEFAULT_COLOR     = "#FF0000"
DEFAULT_THICKNESS = 3
DEFAULT_ZOOM      = 3
CANVAS_MAX_W      = 1100
CANVAS_MAX_H      = 750
FONT_LABEL        = ("Segoe UI", 10)
FONT_TITLE        = ("Segoe UI", 12, "bold")
HEADER_H          = 70
HEADER_BG         = "#1e1e2e"


# ──────────────────────────────────────────────────────────
#  Helper: carica font robusto (Pillow 10+ compatibile)
# ──────────────────────────────────────────────────────────
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "arial.ttf", "Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)   # Pillow >= 10
    except TypeError:
        return ImageFont.load_default()


# ──────────────────────────────────────────────────────────
#  Helper: textbbox compatibile Pillow 9 e 10+
# ──────────────────────────────────────────────────────────
def _textbbox(draw: ImageDraw.ImageDraw, xy, text, font):
    try:
        return draw.textbbox(xy, text, font=font)
    except AttributeError:
        w, h = draw.textsize(text, font=font)
        return (xy[0], xy[1], xy[0] + w, xy[1] + h)


# ──────────────────────────────────────────────────────────
#  Classe principale
# ──────────────────────────────────────────────────────────
class ForensicAnnotator:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Forensic Image Annotator {APP_VERSION}  │  {APP_COPYRIGHT}")
        self.root.configure(bg="#1e1e2e")
        self.root.resizable(True, True)

        self.orig_image:  Image.Image | None = None
        self.work_image:  Image.Image | None = None
        self.display_img: ImageTk.PhotoImage | None = None
        self.scale_factor: float = 1.0

        self.annotations: list[dict] = []
        self.start_x = self.start_y = 0
        self.rect_id = None

        self.ann_color   = tk.StringVar(value=DEFAULT_COLOR)
        self.thickness   = tk.IntVar(value=DEFAULT_THICKNESS)
        self.zoom_factor = tk.IntVar(value=DEFAULT_ZOOM)
        self.case_number = tk.StringVar(value="")
        self.operator    = tk.StringVar(value="")
        self.note_text   = tk.StringVar(value="")
        self.draw_mode   = tk.StringVar(value="rect")

        self._build_ui()

    # ════════════════════════════════════════════════════════
    #  Interfaccia
    # ════════════════════════════════════════════════════════
    def _build_ui(self):
        top = tk.Frame(self.root, bg="#181825", pady=6, padx=8)
        top.pack(side=tk.TOP, fill=tk.X)

        tk.Label(top, text=f"FORENSIC IMAGE ANNOTATOR  {APP_VERSION}",
                 font=("Segoe UI", 14, "bold"),
                 fg="#cba6f7", bg="#181825").pack(side=tk.LEFT, padx=6)

        tk.Label(top, text=APP_COPYRIGHT,
                 font=("Segoe UI", 9, "italic"),
                 fg="#6c7086", bg="#181825").pack(side=tk.RIGHT, padx=10)

        for txt, cmd, bg, fg in [
            ("Apri immagine",  self._open_image, "#313244", "white"),
            ("Salva tutto",    self._save_all,   "#a6e3a1", "#1e1e2e"),
            ("Annulla ultima", self._undo,        "#f38ba8", "#1e1e2e"),
            ("Reset",          self._reset,       "#45475a", "white"),
        ]:
            tk.Button(top, text=txt, command=cmd, bg=bg, fg=fg,
                      font=FONT_LABEL, relief=tk.FLAT, padx=10
                      ).pack(side=tk.LEFT, padx=4)

        main = tk.Frame(self.root, bg="#1e1e2e")
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        left = tk.Frame(main, bg="#1e1e2e")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(left, cursor="crosshair",
                                bg="#11111b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._canvas_bind()

        self.status_var = tk.StringVar(value="Aprire un'immagine per iniziare.")
        tk.Label(left, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg="#a6adc8", bg="#1e1e2e", anchor="w").pack(fill=tk.X, pady=2)

        right = tk.Frame(main, bg="#181825", width=260)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 0))
        right.pack_propagate(False)
        self._build_controls(right)

    def _build_controls(self, parent):
        def section(text):
            tk.Label(parent, text=text, font=FONT_TITLE,
                     fg="#cba6f7", bg="#181825").pack(anchor="w", padx=10, pady=(12, 2))

        section("Dati del verbale")
        for label, var in [("N. caso / procedimento:", self.case_number),
                            ("Operatore / P.G.:",       self.operator)]:
            tk.Label(parent, text=label, font=FONT_LABEL,
                     fg="#cdd6f4", bg="#181825").pack(anchor="w", padx=12)
            tk.Entry(parent, textvariable=var, font=FONT_LABEL,
                     bg="#313244", fg="white", insertbackground="white",
                     relief=tk.FLAT, width=28).pack(padx=12, pady=2)

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
                 relief=tk.FLAT, width=28).pack(padx=12, pady=2)

        section("Colore annotazione")
        color_frame = tk.Frame(parent, bg="#181825")
        color_frame.pack(padx=12, fill=tk.X)
        self.color_btn = tk.Button(color_frame, bg=self.ann_color.get(),
                                   width=3, relief=tk.FLAT, command=self._pick_color)
        self.color_btn.pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(color_frame, textvariable=self.ann_color, font=FONT_LABEL,
                 fg="#cdd6f4", bg="#181825").pack(side=tk.LEFT)

        preset_frame = tk.Frame(parent, bg="#181825")
        preset_frame.pack(padx=12, pady=4, fill=tk.X)
        for col in ["#FF0000", "#FF8C00", "#FFFF00", "#00FF7F", "#00BFFF", "#FF69B4"]:
            tk.Button(preset_frame, bg=col, width=2, relief=tk.FLAT,
                      command=lambda c=col: self._set_color(c)).pack(side=tk.LEFT, padx=1)

        section("Spessore bordo")
        tk.Scale(parent, from_=1, to=10, orient=tk.HORIZONTAL,
                 variable=self.thickness, font=FONT_LABEL,
                 bg="#181825", fg="#cdd6f4", troughcolor="#313244",
                 highlightthickness=0, length=200).pack(padx=12)

        section("Zoom ritaglio (x)")
        tk.Scale(parent, from_=2, to=8, orient=tk.HORIZONTAL,
                 variable=self.zoom_factor, font=FONT_LABEL,
                 bg="#181825", fg="#cdd6f4", troughcolor="#313244",
                 highlightthickness=0, length=200).pack(padx=12)

        section("Annotazioni effettuate")
        list_frame = tk.Frame(parent, bg="#181825")
        list_frame.pack(padx=12, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(list_frame, bg="#313244")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ann_list = tk.Listbox(list_frame, font=("Segoe UI", 8),
                                   bg="#313244", fg="#cdd6f4",
                                   selectbackground="#cba6f7",
                                   yscrollcommand=scrollbar.set,
                                   relief=tk.FLAT, height=8)
        self.ann_list.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.ann_list.yview)

    # ════════════════════════════════════════════════════════
    #  Apertura immagine
    # ════════════════════════════════════════════════════════
    def _open_image(self):
        path = filedialog.askopenfilename(
            title="Seleziona immagine",
            filetypes=[("Immagini", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp"),
                       ("Tutti i file", "*.*")])
        if not path:
            return
        self.orig_image = Image.open(path).convert("RGB")
        self.work_image = self.orig_image.copy()
        self.annotations = []
        self.ann_list.delete(0, tk.END)
        self._fit_canvas()
        self._refresh_canvas()
        self.status_var.set(
            f"Aperta: {os.path.basename(path)}  "
            f"({self.orig_image.width}x{self.orig_image.height} px)")

    # ════════════════════════════════════════════════════════
    #  Canvas helpers
    # ════════════════════════════════════════════════════════
    def _fit_canvas(self):
        if not self.orig_image:
            return
        w, h = self.orig_image.size
        scale = min(CANVAS_MAX_W / w, CANVAS_MAX_H / h, 1.0)
        self.scale_factor = scale
        self.canvas.config(width=int(w * scale), height=int(h * scale))

    def _refresh_canvas(self):
        if not self.work_image:
            return
        w = int(self.work_image.width  * self.scale_factor)
        h = int(self.work_image.height * self.scale_factor)
        display = self.work_image.resize((w, h), Image.LANCZOS)
        self.display_img = ImageTk.PhotoImage(display)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.display_img)

    def _canvas_bind(self):
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _canvas_to_image(self, cx, cy):
        return int(cx / self.scale_factor), int(cy / self.scale_factor)

    # ════════════════════════════════════════════════════════
    #  Gestione mouse
    # ════════════════════════════════════════════════════════
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
                fill=color, width=3, arrow=tk.LAST)
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

        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return

        idx  = len(self.annotations) + 1
        note = self.note_text.get().strip()
        ann  = dict(
            idx=idx, mode=self.draw_mode.get(),
            x1=x1, y1=y1, x2=x2, y2=y2,
            color=self.ann_color.get(),
            thickness=self.thickness.get(),
            note=note,
            ts=datetime.datetime.now().strftime("%H:%M:%S"),
            zoom=self.zoom_factor.get(),
        )
        self.annotations.append(ann)
        self._draw_annotation(self.work_image, ann)

        label = f"[{idx}] {ann['mode'].upper()} ({x1},{y1})->({x2},{y2})  {ann['ts']}"
        if note:
            label += f'  "{note}"'
        self.ann_list.insert(tk.END, label)
        self.ann_list.see(tk.END)
        self._refresh_canvas()
        self.status_var.set(f"Annotazione {idx} aggiunta.")

    # ════════════════════════════════════════════════════════
    #  Disegno annotazione sull'immagine PIL
    # ════════════════════════════════════════════════════════
    def _draw_annotation(self, img: Image.Image, ann: dict):
        draw  = ImageDraw.Draw(img)
        color = ann["color"]
        thick = ann["thickness"]
        x1, y1, x2, y2 = ann["x1"], ann["y1"], ann["x2"], ann["y2"]
        mode  = ann["mode"]
        note  = ann.get("note", "")
        idx   = ann["idx"]

        if mode == "rect":
            draw.rectangle([x1, y1, x2, y2], outline=color, width=thick)
            s = max(8, thick * 3)
            for cx, cy in [(x1, y1), (x2, y1), (x1, y2), (x2, y2)]:
                draw.rectangle([cx - s//2, cy - s//2, cx + s//2, cy + s//2],
                                fill=color)

        elif mode == "arrow":
            draw.line([x1, y1, x2, y2], fill=color, width=thick)
            dx, dy = x2 - x1, y2 - y1
            length = max((dx**2 + dy**2) ** 0.5, 1)
            ux, uy = dx / length, dy / length
            px, py = -uy, ux
            head = 18
            p1 = (int(x2 - head*ux + head*0.4*px), int(y2 - head*uy + head*0.4*py))
            p2 = (int(x2 - head*ux - head*0.4*px), int(y2 - head*uy - head*0.4*py))
            draw.polygon([(x2, y2), p1, p2], fill=color)

        elif mode == "text":
            draw.rectangle([x1, y1, x2, y2], outline=color, width=thick)
            if note:
                font_size = max(14, min(thick * 6, (y2 - y1) // 2, 48))
                font = _load_font(font_size)
                bb   = _textbbox(draw, (0, 0), note, font)
                tw, th = bb[2] - bb[0], bb[3] - bb[1]
                tx = x1 + max(0, ((x2 - x1) - tw) // 2)
                ty = y1 + max(0, ((y2 - y1) - th) // 2)
                # ombra leggera
                draw.text((tx + 2, ty + 2), note, fill="#000000", font=font)
                draw.text((tx, ty), note, fill=color, font=font)

        # ── etichetta numero ──
        font_size = max(14, thick * 5)
        font = _load_font(font_size)
        lbl  = f" {idx} "
        if note and mode != "text":
            lbl += f" {note}"
        tx = x1
        ty = max(0, y1 - font_size - 4)
        bb = _textbbox(draw, (tx, ty), lbl, font)
        draw.rectangle(bb, fill=color)
        draw.text((tx, ty), lbl, fill="white", font=font)

    # ════════════════════════════════════════════════════════
    #  Helper: intestazione forense
    # ════════════════════════════════════════════════════════
    def _make_header(self, width: int, ann: dict) -> Image.Image:
        header = Image.new("RGB", (width, HEADER_H), HEADER_BG)
        dh = ImageDraw.Draw(header)
        fh = _load_font(13)
        fs = _load_font(11)

        line1 = (f"Annotazione #{ann['idx']}  |  "
                 f"Caso: {self.case_number.get() or '---'}  |  "
                 f"Op: {self.operator.get() or '---'}  |  {ann['ts']}")
        line2 = (f"Coord.: ({ann['x1']},{ann['y1']}) -> ({ann['x2']},{ann['y2']})"
                 f"  |  Zoom: x{ann['zoom']}  |  Tipo: {ann['mode'].upper()}")
        line3 = f"Nota: {ann['note']}" if ann.get("note") else ""

        dh.text((10,  6), line1, fill="#cba6f7", font=fh)
        dh.text((10, 26), line2, fill="#a6adc8", font=fs)
        if line3:
            dh.text((10, 46), line3, fill="#f38ba8", font=fs)
        # copyright in basso a destra
        copy_txt = f"Forensic Image Annotator {APP_VERSION}  |  {APP_COPYRIGHT}"
        try:
            bb = dh.textbbox((0, 0), copy_txt, font=fs)
            tw = bb[2] - bb[0]
        except Exception:
            tw = len(copy_txt) * 6
        dh.text((max(0, width - tw - 6), 52), copy_txt, fill="#45475a", font=fs)
        return header

    # ════════════════════════════════════════════════════════
    #  Helper: immagine composita  (scena annotata | ritaglio)
    # ════════════════════════════════════════════════════════
    def _make_composite(self, ann: dict,
                         scene: Image.Image,
                         zoomed_crop: Image.Image) -> Image.Image:
        """
        Composita forense stile Amped:
          - Scena completa con riquadro di selezione a sinistra
          - Pannello zoomato a destra
          - 2 linee trapezoidali + riempimento semitrasparente che
            collegano i lati destri del riquadro ai lati sinistri del pannello zoom
        """
        color = ann["color"]
        thick = max(2, ann["thickness"])

        # scala la scena a un'altezza ragionevole
        MAX_H = 700
        ratio = min(MAX_H / scene.height, 1.0)
        sw    = max(1, int(scene.width  * ratio))
        sh    = max(1, int(scene.height * ratio))
        scene_rs = scene.resize((sw, sh), Image.LANCZOS)

        # coordinate rettangolo scalate
        rx1 = int(ann["x1"] * ratio)
        ry1 = int(ann["y1"] * ratio)
        rx2 = int(ann["x2"] * ratio)
        ry2 = int(ann["y2"] * ratio)

        # scala il ritaglio zoom se troppo alto
        max_zoom_h = sh - 20
        if zoomed_crop.height > max_zoom_h:
            zr = max_zoom_h / zoomed_crop.height
            zoomed_crop = zoomed_crop.resize(
                (max(1, int(zoomed_crop.width * zr)),
                 max(1, int(zoomed_crop.height * zr))), Image.LANCZOS)

        zw, zh = zoomed_crop.size
        gap    = 30

        divider_h = 4
        body_h    = max(sh, zh)
        total_w   = sw + gap + zw
        total_h   = HEADER_H + divider_h + body_h

        composite = Image.new("RGB", (total_w, total_h), HEADER_BG)

        # intestazione
        header = self._make_header(total_w, ann)
        composite.paste(header, (0, 0))

        # barra colorata sotto intestazione
        dc = ImageDraw.Draw(composite)
        dc.rectangle([0, HEADER_H, total_w, HEADER_H + divider_h], fill=color)

        # incolla scena
        scene_y = HEADER_H + divider_h + (body_h - sh) // 2
        composite.paste(scene_rs, (0, scene_y))

        # ridisegna rettangolo di selezione
        abs_rx1 = rx1
        abs_ry1 = scene_y + ry1
        abs_rx2 = rx2
        abs_ry2 = scene_y + ry2
        dc.rectangle([abs_rx1, abs_ry1, abs_rx2, abs_ry2],
                     outline=color, width=thick + 1)

        # incolla pannello zoom centrato verticalmente
        zoom_x = sw + gap
        zoom_y = HEADER_H + divider_h + (body_h - zh) // 2
        composite.paste(zoomed_crop, (zoom_x, zoom_y))

        # bordo pannello zoom
        dc.rectangle([zoom_x, zoom_y, zoom_x + zw - 1, zoom_y + zh - 1],
                     outline=color, width=thick + 1)

        # linee trapezoidali di collegamento
        sel_tr = (abs_rx2, abs_ry1)
        sel_br = (abs_rx2, abs_ry2)
        pan_tl = (zoom_x,  zoom_y)
        pan_bl = (zoom_x,  zoom_y + zh)

        # riempimento semitrasparente del trapezio
        overlay = Image.new("RGBA", composite.size, (0, 0, 0, 0))
        do      = ImageDraw.Draw(overlay)
        r, g, b = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        do.polygon([sel_tr, sel_br, pan_bl, pan_tl], fill=(r, g, b, 45))
        composite = Image.alpha_composite(composite.convert("RGBA"), overlay)
        composite = composite.convert("RGB")

        # linee solide del trapezio
        dc2 = ImageDraw.Draw(composite)
        dc2.line([sel_tr, pan_tl], fill=color, width=thick)
        dc2.line([sel_br, pan_bl], fill=color, width=thick)

        # etichette
        fl = _load_font(13)
        dc2.text((8, scene_y + sh - 22), "SCENA COMPLETA", fill=color, font=fl)
        dc2.text((zoom_x + 6, zoom_y + 5), f"DETTAGLIO  x{ann['zoom']}", fill=color, font=fl)

        return composite

    # ════════════════════════════════════════════════════════
    #  Salvataggio
    # ════════════════════════════════════════════════════════
    def _save_all(self):
        if not self.orig_image or not self.annotations:
            messagebox.showinfo("Nessuna annotazione",
                                "Aprire un'immagine e creare almeno un'annotazione.")
            return

        import re
        def _sanitize(s):
            s = re.sub(r'[\\/:*?"<>|]', '', s)
            s = re.sub(r'\s+', '_', s.strip())
            return s or 'SENZA_NOME'

        case = _sanitize(self.case_number.get())
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # ── scelta cartella base ──
        base = filedialog.askdirectory(title="Scegli la cartella di destinazione")
        if not base:
            return

        # struttura:  <base> / <CASO> / <CASO_YYYYMMDD_HHMMSS> /
        case_dir    = os.path.join(base, case)
        session_dir = os.path.join(case_dir, f"{case}_{ts}")
        os.makedirs(session_dir, exist_ok=True)

        # da qui in poi tutti i file vanno in session_dir
        folder = session_dir
        saved  = []

        # ── 1. Scena completa annotata ──
        full_path = os.path.join(folder, f"{case}_{ts}_ANNOTATA.jpg")
        self.work_image.save(full_path, quality=95)
        saved.append(f"Scena annotata:  {os.path.basename(full_path)}")

        for ann in self.annotations:
            x1, y1, x2, y2 = ann["x1"], ann["y1"], ann["x2"], ann["y2"]

            # ritaglio originale zoomato
            crop   = self.orig_image.crop((x1, y1, x2, y2))
            zf     = ann["zoom"]
            zoomed = crop.resize((crop.width * zf, crop.height * zf), Image.LANCZOS)
            dz     = ImageDraw.Draw(zoomed)
            dz.rectangle([0, 0, zoomed.width - 1, zoomed.height - 1],
                          outline=ann["color"], width=ann["thickness"] + 2)

            # ── 2. Ritaglio zoomato + intestazione ──
            header       = self._make_header(zoomed.width, ann)
            crop_out     = Image.new("RGB", (zoomed.width, HEADER_H + zoomed.height), HEADER_BG)
            crop_out.paste(header, (0, 0))
            crop_out.paste(zoomed, (0, HEADER_H))
            crop_name    = f"{case}_{ts}_RITAGLIO_{ann['idx']:02d}.jpg"
            crop_path    = os.path.join(folder, crop_name)
            crop_out.save(crop_path, quality=95)
            saved.append(f"Ritaglio #{ann['idx']:02d}:     {crop_name}")

            # ── 3. Composita (scena + ritaglio affiancati) ──
            composite    = self._make_composite(ann, self.work_image.copy(), zoomed)
            comp_name    = f"{case}_{ts}_COMPOSITA_{ann['idx']:02d}.jpg"
            comp_path    = os.path.join(folder, comp_name)
            composite.save(comp_path, quality=95)
            saved.append(f"Composita #{ann['idx']:02d}:    {comp_name}")

        # ── 4. Report testuale ──
        report_path = os.path.join(folder, f"{case}_{ts}_REPORT.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("  REPORT ANNOTAZIONI FORENSI\n")
            f.write("=" * 60 + "\n")
            f.write(f"Data/Ora:       {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"N. caso:        {self.case_number.get() or '---'}\n")
            f.write(f"Operatore P.G.: {self.operator.get() or '---'}\n")
            f.write(f"Dim. immagine:  {self.orig_image.width}x{self.orig_image.height} px\n")
            f.write("-" * 60 + "\n")
            for ann in self.annotations:
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
        saved.append(f"Report testuale: {os.path.basename(report_path)}")

        # ── 5. Manifest SHA-256 per catena di custodia ──
        manifest_path = os.path.join(folder, f"{case}_{ts}_CHAIN_OF_CUSTODY.txt")
        all_files = [p for p in [full_path, report_path]
                     if os.path.isfile(p)]
        # aggiungi tutti i ritagli e composite presenti nella sessione
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if fpath not in all_files and os.path.isfile(fpath):
                all_files.append(fpath)

        with open(manifest_path, "w", encoding="utf-8") as mf:
            mf.write("=" * 72 + "\n")
            mf.write("  CHAIN OF CUSTODY  –  MANIFEST HASH SHA-256\n")
            mf.write(f"  Forensic Image Annotator {APP_VERSION}  |  {APP_COPYRIGHT}\n")
            mf.write("=" * 72 + "\n")
            mf.write(f"Data/Ora:       {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            mf.write(f"N. caso:        {self.case_number.get() or '---'}\n")
            mf.write(f"Operatore P.G.: {self.operator.get() or '---'}\n")
            mf.write(f"Sessione:       {session_dir}\n")
            mf.write("-" * 72 + "\n")
            mf.write(f"{'FILE':<45} {'SHA-256'}\n")
            mf.write("-" * 72 + "\n")
            for fpath in sorted(all_files):
                h = hashlib.sha256()
                with open(fpath, "rb") as bf:
                    for chunk in iter(lambda: bf.read(65536), b""):
                        h.update(chunk)
                mf.write(f"{os.path.basename(fpath):<45} {h.hexdigest()}\n")
            mf.write("=" * 72 + "\n")
            mf.write("  Il presente manifest garantisce l’integrità dei file\n")
            mf.write("  ai sensi della normativa sulla catena di custodia digitale.\n")
            mf.write("=" * 72 + "\n")
        saved.append(f"Chain of custody: {os.path.basename(manifest_path)}")

        # ── 6. Archivio ZIP compresso della sessione ──
        zip_path = os.path.join(case_dir, f"{case}_{ts}_ARCHIVIO.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for fpath in sorted(all_files) + [manifest_path]:
                if os.path.isfile(fpath):
                    zf.write(fpath, arcname=os.path.basename(fpath))
        saved.append(f"Archivio ZIP:     {os.path.basename(zip_path)}")

        msg = "File salvati correttamente in:\n" + session_dir + "\n\n" + "\n".join(saved)
        messagebox.showinfo("Salvataggio completato", msg)
        self.status_var.set(f"Sessione salvata: {session_dir}")

    # ════════════════════════════════════════════════════════
    #  Undo / Reset
    # ════════════════════════════════════════════════════════
    def _undo(self):
        if not self.annotations:
            return
        self.annotations.pop()
        self.ann_list.delete(tk.END)
        self.work_image = self.orig_image.copy()
        for ann in self.annotations:
            self._draw_annotation(self.work_image, ann)
        self._refresh_canvas()
        self.status_var.set("Ultima annotazione annullata.")

    def _reset(self):
        if not self.orig_image:
            return
        if messagebox.askyesno("Conferma reset", "Rimuovere tutte le annotazioni?"):
            self.annotations = []
            self.ann_list.delete(0, tk.END)
            self.work_image = self.orig_image.copy()
            self._refresh_canvas()
            self.status_var.set("Tutte le annotazioni rimosse.")

    # ════════════════════════════════════════════════════════
    #  Colore
    # ════════════════════════════════════════════════════════
    def _pick_color(self):
        color = colorchooser.askcolor(
            color=self.ann_color.get(), title="Scegli colore annotazione")[1]
        if color:
            self._set_color(color)

    def _set_color(self, color: str):
        self.ann_color.set(color)
        self.color_btn.configure(bg=color)


# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    ForensicAnnotator(root)
    root.mainloop()
