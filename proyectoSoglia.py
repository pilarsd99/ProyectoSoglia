#Estas son lineas de codigo para linux
import os
import platform
if platform.system() == "Linux":
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
#_______________________________________________________
import cv2
import mediapipe as mp
import math
import time

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# CONFIGURACIONES DE MANOS
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
mp_manos = mp.solutions.hands
# Color de dedos
COLOR_DEDOS = {
    'gordo':   (0, 0, 255),      #rojo
    'indice':  (0, 165, 255),   #naranja
    'medio':   (0, 255, 255),     #amarillo
    'anular':  (0, 255, 0),    #verde
    'meñique': (255, 0, 0),    #azul
    'muñeca':  (255, 255, 255), #Blanco
}
# Conectores de los dedos
CONEXION_DEDOS ={
    'gordo':   [(0, 1),(1, 2),(2, 3),(3, 4)],
    'indice':  [(0, 5),(5, 6),(6, 7),(7, 8)],
    'medio':   [(0, 9),(9, 10),(10, 11),(11, 12)],
    'anular':  [(0, 13),(13, 14),(14, 15),(15, 16)],
    'meñique': [(0, 17),(17, 18),(18, 19),(19, 20)]
}
# punto de referencias de los dedos
PUNTOS_DE_DEDOS = {}
for  dedo,conns in CONEXION_DEDOS.items():
   for a,b in conns:
      PUNTOS_DE_DEDOS[a] = dedo
      PUNTOS_DE_DEDOS[b] = dedo
PUNTOS_DE_DEDOS[0] = 'muñeca'
# Puntos de referencia de la punta de los dedos
PUNTA_DEDOS = {4,8, 12, 16, 20}

# ============================================================
# PIXELACIÓN
# ============================================================
def pixelar(imagen, pixel_tamaño):
    if pixel_tamaño <= 1:
        return imagen.copy()
    h, w = imagen.shape[:2]
    small_w = max(1, w // pixel_tamaño)
    small_h = max(1, h // pixel_tamaño)
    small = cv2.resize(imagen, (small_w, small_h), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
#================================================================
# Gestos
# ===============================================================
# Dedos levantados revisa si los dedos estan totalmente levantodos
# con el dato de las puntas
def dedos_levantados(puntos_Mano):
    puntas = [4, 8, 12, 16, 20]
    nudillos = [3, 6, 10, 14, 18]
    dedos = []
    for punta, nudillo in zip(puntas, nudillos):
        p = puntos_Mano.landmark[punta]
        n = puntos_Mano.landmark[nudillo]
        dedos.append(1 if p.y < n.y else 0)
    return dedos

# Este es el gesto de zoom o de pinzas es donde se genera
# la hipontenusa entre dedo gordo dedo indice
def pinzas (puntos_Mano):
    gordo = puntos_Mano.landmark[4]
    indice = puntos_Mano.landmark[8]
    return math.hypot(gordo.x - indice.x, gordo.y - indice.y)

# reconocimineto de los gestos
def reconocer_gesto(puntos_Mano):
#aqui se define que tanto se se va desenfocar la imagen
# 1 sin pixelear
# 25 desenfocar
    dedos = dedos_levantados(puntos_Mano)
    distpinzas =  pinzas(puntos_Mano)
    total = sum(dedos)
    #swap en horizontal
    if dedos[1] == 1 and dedos[2] == 1 and sum(dedos[1:]) == 2:
        return "SWAP_HORIZONTAL", 8
    # swap vertical
    if dedos[1] == 1 and sum(dedos[1:]) == 1:
        return "SWAP_VERTICAL", 8
    #pinzas o zoom
    if distpinzas < 0.05:
        return "PINZA", 1
    #mano enterera para pixelar la imagen
    if total >= 4:
        return "ABIERTA", 25
        # sin gesto reconocido
    return "—", 1

#=============================================================
 # Carga de imagenes
# ============================================================
def cargar_pares(max_w, max_h):

    BASE = os.path.join(os.path.dirname(__file__), "Imagenes") + os.sep
    rutas = [
        [BASE + "img1A.png", BASE + "img1B.png"],
        [BASE + "img2A.png", BASE + "img2B.png"]
    ]

    # Calcular tamaño objetivo a partir de la primera imagen
    primera = cv2.imread(rutas[0][0])
    if primera is None:
        print(f"❌ No se pudo leer: {rutas[0][0]}")
        exit(1)
    h0, w0 = primera.shape[:2]
    escala = min(max_w/ w0, max_h / h0, 1.0)
    ancho_obj = int(w0 * escala)
    alto_obj = int(h0 * escala)
    print(f"📐 Tamaño objetivo: {ancho_obj}x{alto_obj}")

    pares = []
    for par_rutas in rutas:
        par_imagenes = []
        for ruta in par_rutas:
            if not os.path.exists(ruta):
                print(f"❌ No existe: {ruta}")
                exit(1)
            img = cv2.imread(ruta)
            if img is None:
                print(f"❌ OpenCV no pudo leer: {ruta}")
                exit(1)

            # Forzar TODAS al mismo tamaño objetivo
            if img.shape[:2] != (alto_obj, ancho_obj):
                img = cv2.resize(img, (ancho_obj, alto_obj),
                                 interpolation=cv2.INTER_AREA)

            par_imagenes.append(img)
        pares.append(par_imagenes)

    print(f"✅ Cargados {len(pares)} pares de imágenes")
    return pares

# ============================================================
# ANIMACIÓN
# ============================================================
class ValorSuavizado:
    def __init__(self, inicial=1.0, suavizado=0.15):
        self.valor = float(inicial)
        self.objetivo = float(inicial)
        self.suavizado = suavizado
    def fijar_objetivo(self, objetivo):
        self.objetivo = float(objetivo)
    def actualizar(self):
        self.valor += (self.objetivo - self.valor) * self.suavizado
        return self.valor
# ============================================================
# DIBUJAR MANO
# ============================================================
def dibujar_mano(img, puntos_Mano, w, h):
    for dedo, conns in CONEXION_DEDOS.items():
        color = COLOR_DEDOS[dedo]
        for a, b in conns:
            p1 = puntos_Mano.landmark[a]
            p2 = puntos_Mano.landmark[b]
            cv2.line(img,
                     (int(p1.x * w), int(p1.y * h)),
                     (int(p2.x * w), int(p2.y * h)),
                     color, 2)
    for idx, lm in enumerate(puntos_Mano.landmark):
        cx, cy = int(lm.x * w), int(lm.y * h)
        color = COLOR_DEDOS[PUNTOS_DE_DEDOS.get(idx, 'muñeca')]
        radius = 6 if idx in PUNTA_DEDOS else 4
        cv2.circle(img, (cx, cy), radius, color, cv2.FILLED)

# ============================================================
# CONFIGURACIÓN INICIAL
# ============================================================
MODO = "imagen" # aqui elegimos si se pone en modo imagen webcam

# Máximo tamaño de ventana
MAX_PANTALLA_W = 1280
MAX_PANTALLA_H = 720

# 1. CÁMARA: SIEMPRE se abre
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Cámara no disponible. ¿Está conectada?")
    exit(1)
print("✅ Cámara abierta")

# 2. IMÁGENES: pares y estado inicial
pares_imagenes = cargar_pares(MAX_PANTALLA_W, MAX_PANTALLA_H)
indice_par = 0
indice_imagen = 0
gesto_anterior = "—"

# 3. MODELO DE MANOS
manos = mp_manos.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5
)

# 4. ANIMADOR
animador_pixel = ValorSuavizado(inicial=1.0, suavizado=0.15)

#variables de tiempo minidelay
ultimo_cambio = 0.0      # timestamp del último swap
COOLDOWN_SEG = 1       # segundos entre cambios

print("ESC para salir")

# ============================================================
# LOOP PRINCIPAL
# ============================================================

while True:
    # --- 1. Leer cámara SIEMPRE (una sola vez) ---
    ret_cam, cam_frame = cap.read()
    if not ret_cam:
        break
    cam_frame = cv2.flip(cam_frame, 1)

    # --- 2. Frame base según el modo ---
    if MODO == "webcam":
        frame = cam_frame.copy()
    else:
        frame = pares_imagenes[indice_par][indice_imagen].copy()

    h, w = frame.shape[:2]

    # --- 3. Detectar mano sobre el frame de la cámara ---
    nombre_gesto = "—"
    cam_rgb = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
    resultados = manos.process(cam_rgb)

    if resultados.multi_hand_landmarks:
        puntos_Mano = resultados.multi_hand_landmarks[0]
        nombre_gesto, objetivo_pixel = reconocer_gesto(puntos_Mano)
        animador_pixel.fijar_objetivo(objetivo_pixel)
        if MODO == "webcam":
            dibujar_mano(frame, puntos_Mano, w, h)
    else:
        animador_pixel.fijar_objetivo(1.0)

    # --- 4. FLANCO: solo actúa cuando el gesto CAMBIA ---
    ahora = time.time()
    en_cooldown = (ahora - ultimo_cambio) < COOLDOWN_SEG
    if not en_cooldown:
        if nombre_gesto == "SWAP_VERTICAL" and gesto_anterior != "SWAP_VERTICAL":
            indice_imagen = (indice_imagen + 1) % 2
            ultimo_cambio = ahora

        if nombre_gesto == "SWAP_HORIZONTAL" and gesto_anterior != "SWAP_HORIZONTAL":
            indice_par = (indice_par + 1) % len(pares_imagenes)
            indice_imagen = 0  # reset al primer elemento del par nuevo
            ultimo_cambio = ahora


    # --- 5. Aplicar pixelación animada ---
    pixel_actual = animador_pixel.actualizar()
    frame = pixelar(frame, int(pixel_actual))

    # --- 6. Miniatura de la webcam (solo modo imagen) ---
    if MODO == "imagen" and cam_frame is not None:
        thumb_w, thumb_h = 240, 180
        cam_thumb = cv2.resize(cam_frame, (thumb_w, thumb_h))
        x0 = w - thumb_w - 15
        y0 = h - thumb_h - 15
        frame[y0:y0 + thumb_h, x0:x0 + thumb_w] = cam_thumb
        cv2.rectangle(frame, (x0, y0),
                      (x0 + thumb_w, y0 + thumb_h),
                      (255, 255, 255), 2)

    # --- 7. HUD ---
    cv2.putText(frame, f"Gesto: {nombre_gesto}",
                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)
    cv2.putText(frame, f"Pixel: {pixel_actual:.1f}",
                (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (0, 255, 0), 2)
    cv2.putText(frame, f"Par: {indice_par} | Img: {indice_imagen}",
                (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                (255, 255, 0), 2)

    # --- 8. Mostrar ---
    cv2.imshow("Proyecto Soglia", frame)

    # --- 9. Teclas ---
    tecla = cv2.waitKey(10) & 0xFF
    if tecla == 27:  # ESC
        break
    if tecla == ord('s'):
        cv2.imwrite(f"captura_{indice_par}_{indice_imagen}.png", frame)
        print(f"📸 Guardado")

    # --- 10. Actualizar gesto anterior ---
    gesto_anterior = nombre_gesto

# --- Limpieza ---
cap.release()
cv2.destroyAllWindows()
print("✅ Fin")
