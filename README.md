# ProyectoSoglia

Hand tracking interactivo con gestos y pixelación.

## Requisitos

- Python 3.11 (importante: **no** 3.12, MediaPipe aún no lo soporta bien)
- Cámara web

## Instalación en Windows

1. Descarga Python 3.11 desde https://www.python.org/downloads/
   - ⚠️ Marca la casilla **"Add Python to PATH"** durante la instalación
2. Abre **PowerShell** o **CMD** en la carpeta del proyecto
3. Crea el entorno virtual:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
4. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
5. Ejecuta:
   ```
   python main.py
   ```

## Instalación en Linux/Ubuntu

```bash
sudo apt install python3.11 python3.11-venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Uso

- Índice + medio → cambiar de par de imágenes
- Solo índice → cambiar imagen dentro del par
- Pinza → efecto zoom (próximamente)
- Mano abierta → pixelación máxima
- **ESC** → salir
