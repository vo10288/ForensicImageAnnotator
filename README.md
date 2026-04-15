# 🔍 Forensic Image Annotator — v. 0.1

> **By Visi@n — Ethical Hacker**  
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
**© 2026 Visi@n — Ethical Hacker. Tutti i diritti riservati.**  
Non distribuire senza autorizzazione scritta dell'autore.
