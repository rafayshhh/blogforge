# BlogForge Packaging & Distribution Guide

BlogForge is a local-first desktop application. This document outlines how to package and distribute BlogForge for end users across desktop platforms.

---

## 1. PyInstaller Standalone Executable Build

You can bundle BlogForge into a standalone desktop executable using PyInstaller.

### 1.1 Install PyInstaller
```bash
pip install pyinstaller
```

### 1.2 Build on Windows
Run PyInstaller with the Qt/PySide6 windowed flag:
```bash
pyinstaller --noconsole --name "BlogForge" \
  --collect-all PySide6 \
  --collect-all google.genai \
  --add-data "data;data" \
  app/main.py
```

The output executable will be located in `dist/BlogForge/BlogForge.exe`.

### 1.3 Build on macOS
```bash
pyinstaller --windowed --name "BlogForge" \
  --collect-all PySide6 \
  --collect-all google.genai \
  --add-data "data:data" \
  app/main.py
```
This generates `dist/BlogForge.app`.

---

## 2. Headless / Server / CI Deployment

If running BlogForge generation pipelines or test suites in headless CI environments (e.g. GitHub Actions, Docker, Linux server), Qt requires an offscreen platform plugin:

```bash
export QT_QPA_PLATFORM=offscreen
pytest tests/
```

### Minimal Dockerfile for Headless Pipelines:
```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libegl1 libgl1 libxkbcommon-x11-0 libdbus-1-3 libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV QT_QPA_PLATFORM=offscreen

CMD ["pytest", "tests/"]
```

---

## 3. Data Backups & Migration

All user data is stored strictly in JSON files within the `data/` folder:
- Projects: `data/projects/*.json`
- Articles: `data/articles/*.json`

To back up or migrate to another workstation:
1. Copy the `data/` directory to the target machine.
2. Ensure permissions allow reading and writing.
3. Launch BlogForge. The app will immediately index existing projects and articles.
