import cv2
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# --- CONFIGURACIÓN ---
CARPETA_ENTRENAMIENTO = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\imagenes_entrenamiento"
CARPETA_IMAGENES = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\imagenes"
CARPETA_SALIDA = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\salida"
NUM_HILOS = 4

os.makedirs(CARPETA_SALIDA, exist_ok=True)

def procesar_imagen(path_imagen, nombre_salida):
    inicio = time.time()
    img = cv2.imread(str(path_imagen))
    if img is None:
        print(f"Error al cargar {path_imagen}")
        return path_imagen, 0.0
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(str(nombre_salida), gris)
    fin = time.time()
    duracion = fin - inicio
    return path_imagen, duracion

# --- FASE 1: ENTRENAMIENTO ---
# Procesa las imágenes de entrenamiento y obtiene un tiempo promedio por tamaño (clave = shape)

entrenamiento_imgs = list(Path(CARPETA_ENTRENAMIENTO).glob("*.jpg")) + list(Path(CARPETA_ENTRENAMIENTO).glob("*.png"))

# Mide los tiempos de entrenamiento por resolución (shape)
tiempos_por_shape = {}

print("\n=== FASE DE ENTRENAMIENTO ===")
for path in entrenamiento_imgs:
    img = cv2.imread(str(path))
    if img is None:
        continue
    shape = img.shape  # (alto, ancho, canales)
    _, duracion = procesar_imagen(path, Path(CARPETA_SALIDA) / f"entrenamiento_{path.name}")
    if shape not in tiempos_por_shape:
        tiempos_por_shape[shape] = []
    tiempos_por_shape[shape].append(duracion)
    print(f"{path.name} (shape: {shape}) tiempo: {duracion:.3f} s")

# Calcula el promedio de tiempo por shape
promedios_shape = {s: sum(lst)/len(lst) for s, lst in tiempos_por_shape.items()}

print("\nPromedios de tiempo por tamaño de imagen (shape):")
for s, prom in promedios_shape.items():
    print(f"{s}: {prom:.3f} s")

# --- FASE 2: PROCESAMIENTO REAL ---

imagenes = list(Path(CARPETA_IMAGENES).glob("*.jpg")) + list(Path(CARPETA_IMAGENES).glob("*.png"))
tiempos_estimados = {}

print("\n=== ASIGNACIÓN PREDICTIVA ===")
for path in imagenes:
    img = cv2.imread(str(path))
    if img is None:
        print(f"Error al cargar {path}")
        continue
    shape = img.shape
    # Busca el promedio de tiempo más cercano por shape
    if shape in promedios_shape:
        tiempos_estimados[path] = promedios_shape[shape]
    else:
        # Si no hay shape idéntico, usa el promedio general
        tiempos_estimados[path] = sum(promedios_shape.values()) / len(promedios_shape)
    print(f"{path.name} (shape: {shape}) tiempo estimado: {tiempos_estimados[path]:.3f} s")

carga_por_hilo = [0.0 for _ in range(NUM_HILOS)]
tareas_por_hilo = [[] for _ in range(NUM_HILOS)]

for path, tiempo in sorted(tiempos_estimados.items(), key=lambda x: -x[1]):
    hilo_menos_cargado = carga_por_hilo.index(min(carga_por_hilo))
    tareas_por_hilo[hilo_menos_cargado].append(path)
    carga_por_hilo[hilo_menos_cargado] += tiempo

for i, tareas in enumerate(tareas_por_hilo):
    print(f"Hilo {i} recibe {len(tareas)} imágenes (carga estimada: {carga_por_hilo[i]:.2f} s)")

# --- FASE 3: PROCESAMIENTO PARALELO ---
def procesar_lote(lista_imagenes, hilo_id):
    for path in lista_imagenes:
        salida = Path(CARPETA_SALIDA) / f"gris_{hilo_id}_{path.name}"
        procesar_imagen(path, salida)

print("\n=== PROCESAMIENTO EN PARALELO ===")
with ThreadPoolExecutor(max_workers=NUM_HILOS) as executor:
    for i in range(NUM_HILOS):
        executor.submit(procesar_lote, tareas_por_hilo[i], i)

print("Procesamiento terminado.")
