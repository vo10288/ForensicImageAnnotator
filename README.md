# 🔍 Forensic Image Annotator — v. 0.1


> **By Visi@n **  
> Professional tool for forensic annotation of digital images,  
> designed for investigative use and the preparation of judicial reports.

---

## 📋 Description

**Forensic Image Annotator** allows Law Enforcement Officers and forensic consultants to:

- Open any image (CCTV frame, screenshot, crime scene photo, etc.)
- Draw annotations using rectangles, arrows and text labels
- Automatically generate a **zoomed crop** of the highlighted detail
- Produce a **forensic composite image** (full scene + zoom panel connected by trapezoid lines)
- Save all materials in a folder structure organised by case number
- Generate a **SHA-256 manifest** for digital chain of custody
- Create a **compressed ZIP archive** of the session, ready to attach to official reports

---

## 🖥️ System Requirements

| Component | Minimum version |
|---|---|
| Python | 3.10 or higher |
| Pillow | 10.0.0 or higher |
| Operating System | Windows 10/11, Linux, macOS |
| tkinter | included in the standard Python distribution |

---

## ⚙️ Installation

### 1. Clone or download the repository

```bash
git clone https://github.com/yourusername/forensic-image-annotator.git
cd forensic-image-annotator
```

Or simply download `image_annotator.py` directly.

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch the application

```bash
python image_annotator.py
```

---

## 🎯 Usage

### Opening an image
Click **📂 Open image** and select a file (JPG, PNG, BMP, TIFF, WEBP).

### Annotation tools

| Tool | Usage |
|---|---|
| **Rectangle** | Drag to highlight an area of interest |
| **Arrow →** | Drag to point to a specific detail |
| **Text** | Rectangle with a centred text label |

To draw: hold the left mouse button and drag from the **top-left** corner to the **bottom-right** corner of the area of interest.

### Customisation
- **Colour**: full colour picker + 6 quick presets
- **Border thickness**: 1 to 10 pixels
- **Crop zoom**: ×2 to ×8

### Report metadata
Before saving, fill in the following fields:
- **Case / Proceeding number** — used as the folder name on disk
- **Officer / Investigator** — printed on every output image and in the report

### Saving
Click **💾 Save all**, then choose the **base destination folder**.  
The application automatically creates the following structure:

```
📁 <chosen destination>
 └── 📁 <case_number>                        ← case folder
      ├── 📁 <case_number>_YYYYMMDD_HHMMSS   ← session 1
      │    ├── *_ANNOTATED.jpg               → full scene with annotations
      │    ├── *_CROP_01.jpg                 → zoomed crop with forensic header
      │    ├── *_COMPOSITE_01.jpg            → scene + zoom with trapezoid lines
      │    ├── *_REPORT.txt                  → text report with pixel coordinates
      │    └── *_CHAIN_OF_CUSTODY.txt        → SHA-256 manifest
      └── *_ARCHIVE.zip                      → compressed session archive
```

Each save operation creates a **new timestamped subfolder** — files are never overwritten.

---

## 🔐 Digital Chain of Custody

The `_CHAIN_OF_CUSTODY.txt` file contains:
- **SHA-256 hash** of every file in the session
- Date, time, case number and investigating officer
- Full session path
- Legal note on digital material integrity

This document can be attached to the official report to certify that files have not been altered after saving.

To verify integrity at a later date:

```bash
# Windows (PowerShell)
Get-FileHash .\*_ANNOTATED.jpg -Algorithm SHA256

# Linux / macOS
sha256sum *_ANNOTATED.jpg
```

Compare the output value with the hash recorded in the manifest.

---

## 📦 Project Structure

```
forensic-image-annotator/
├── image_annotator.py      # main source file
├── requirements.txt        # Python dependencies
├── icon.ico                # application icon
└── README.md               # this file
```

---

## 🛠️ Building a standalone executable (.exe)

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Single folder build

```bash
pyinstaller --onedir --windowed --name "ForensicAnnotator" image_annotator.py
```

The executable will be located at `dist\ForensicAnnotator\ForensicAnnotator.exe`.

### 3. Single file build (recommended for distribution)

```bash
pyinstaller --onefile --windowed --name "ForensicAnnotator" image_annotator.py
```

A single `dist\ForensicAnnotator.exe` file will be produced — no Python installation required on the target machine.

### 4. Full recommended build command (with icon)

```bash
pyinstaller --onefile --windowed ^
  --icon=icon.ico ^
  --name "ForensicAnnotator_v01" ^
  --hidden-import PIL._tkinter_finder ^
  image_annotator.py
```

### 5. Post-build cleanup

```bash
rmdir /s /q build
del ForensicAnnotator.spec
```

### ⚠️ Windows notes

| Issue | Solution |
|---|---|
| Antivirus blocks the exe | Add an exclusion for the `dist\` folder — common false positive with PyInstaller |
| Black console window appears | Always use `--windowed` flag |
| Pillow not found inside exe | Add `--hidden-import PIL` if needed |
| Slow first launch with `--onefile` | Normal: the exe self-extracts to `%TEMP%` on first run; use `--onedir` if speed matters |

---

## 📄 License

For internal investigative and forensic use only.  
**© 2026 Visi@n . All rights reserved.**  
Do not distribute without the author's written permission.


# 🔍 Forensic Image Annotator — v. 0.1

> **By Visi@n  **  
> Strumento professionale per l'annotazione forense di immagini digitali,  
> progettato per l'utilizzo in ambito investigativo e per la redazione di verbali giudiziari.

---

## 📋 Descrizione

**Forensic Image Annotator** permette agli operatori di Polizia Giudiziaria e ai consulenti forensi di:

- Aprire un'immagine (fotogramma da videosorveglianza, screenshot, foto di scena del crimine, ecc.)
- Disegnare annotazioni con rettangoli, frecce e testo
- Generare automaticamente un **ritaglio zoomato** del particolare evidenziato
- Produrre un'**immagine composita stile forense** (scena + zoom collegati da linee trapezoidali)
- Salvare tutti i materiali in una struttura di cartelle organizzata per procedimento
- Generare un **manifest SHA-256** per la catena di custodia digitale
- Creare un **archivio ZIP compresso** della sessione pronto per l'allegazione ai verbali

---

## 🖥️ Requisiti di sistema

| Componente | Versione minima |
|---|---|
| Python | 3.10 o superiore |
| Pillow | 10.0.0 o superiore |
| Sistema operativo | Windows 10/11, Linux, macOS |
| tkinter | incluso nella distribuzione standard di Python |

---

## ⚙️ Installazione

### 1. Clona o scarica il repository

```bash
git clone https://github.com/tuouser/forensic-image-annotator.git
cd forensic-image-annotator
```

Oppure scarica direttamente `image_annotator.py`.

### 2. Crea un ambiente virtuale (consigliato)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 4. Avvia il programma

```bash
python image_annotator.py
```

---

## 🎯 Utilizzo

### Apertura immagine
Clicca **📂 Apri immagine** e seleziona il file (JPG, PNG, BMP, TIFF, WEBP).

### Strumenti di annotazione

| Strumento | Utilizzo |
|---|---|
| **Rettangolo** | Trascina per evidenziare una zona |
| **Freccia →** | Trascina per indicare un punto specifico |
| **Testo** | Rettangolo con etichetta testuale al centro |

Per disegnare: tieni premuto il tasto sinistro del mouse dall'angolo **in alto a sinistra** verso quello **in basso a destra** della zona di interesse.

### Personalizzazione
- **Colore**: selettore completo + 6 preset rapidi
- **Spessore bordo**: da 1 a 10 pixel
- **Zoom ritaglio**: da ×2 a ×8

### Metadati verbale
Prima di salvare, compila i campi:
- **N° caso / procedimento** — viene usato come nome delle cartelle
- **Operatore / P.G.** — stampato su ogni immagine e nel report

### Salvataggio
Clicca **💾 Salva tutto**, scegli la **cartella di destinazione base**.  
Il programma crea automaticamente:

```
📁 <destinazione scelta>
 └── 📁 <N_caso>                          ← cartella del procedimento
      ├── 📁 <N_caso>_YYYYMMDD_HHMMSS     ← sessione 1
      │    ├── *_ANNOTATA.jpg             → scena completa con annotazioni
      │    ├── *_RITAGLIO_01.jpg          → ritaglio zoomato con intestazione
      │    ├── *_COMPOSITA_01.jpg         → scena + zoom con linee trapezoidali
      │    ├── *_REPORT.txt               → verbale testuale con coordinate
      │    └── *_CHAIN_OF_CUSTODY.txt     → manifest SHA-256 per catena di custodia
      └── *_ARCHIVIO.zip                  → ZIP compresso della sessione
```

Ogni sessione di salvataggio produce una **nuova sottocartella timestampata**: i file non vengono mai sovrascritti.

---

## 🔐 Catena di custodia digitale

Il file `_CHAIN_OF_CUSTODY.txt` contiene:
- Hash **SHA-256** di ogni file della sessione
- Data, ora, n° caso e operatore P.G.
- Percorso completo della sessione
- Nota legale sulla integrità dei materiali

Questo documento può essere allegato al verbale per attestare che i file non sono stati alterati dopo il salvataggio.

Per verificare l'integrità in un secondo momento:

```bash
# Windows (PowerShell)
Get-FileHash .\*_ANNOTATA.jpg -Algorithm SHA256

# Linux / macOS
sha256sum *_ANNOTATA.jpg
```

Confronta il valore ottenuto con quello riportato nel manifest.

---

## 📦 Struttura del progetto

```
forensic-image-annotator/
├── image_annotator.py      # sorgente principale
├── requirements.txt        # dipendenze Python
└── README.md               # questo file
```

---

## 🛠️ Compilazione in eseguibile (.exe)

Vedi la sezione dedicata più avanti nel documento.

---

## 📄 Licenza

Uso interno per scopi investigativi e forensi.  
**© 2026 Visi@n . Tutti i diritti riservati.**  
Non distribuire senza autorizzazione scritta dell'autore.
