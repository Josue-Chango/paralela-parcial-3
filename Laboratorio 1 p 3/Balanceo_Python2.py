import cv2
import os
import time
import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# --- CONFIGURACIÓN ---
CARPETA_ENTRENAMIENTO = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\imagenes_entrenamiento"
CARPETA_IMAGENES = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\imagenes"
CARPETA_SALIDA = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\salida"
CARPETA_SALIDA_ENTRENAMIENTO = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\salida_entrenamiento"
ARCHIVO_ENTRENAMIENTO = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\tiempos_entrenamiento.csv"
NUM_HILOS = 8

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

def procesar_lote(lista_imagenes, hilo_id):
    for path in lista_imagenes:
        salida = Path(CARPETA_SALIDA) / f"gris_{hilo_id}_{path.name}"
        procesar_imagen(path, salida)

def fase_entrenamiento():
    entrenamiento_imgs = list(Path(CARPETA_ENTRENAMIENTO).glob("*.jpg")) + list(Path(CARPETA_ENTRENAMIENTO).glob("*.png"))
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

    promedios_shape = {s: sum(lst)/len(lst) for s, lst in tiempos_por_shape.items()}

    # --- Guardar promedios en archivo CSV ---
    with open(ARCHIVO_ENTRENAMIENTO, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["alto", "ancho", "canales", "tiempo_promedio"])
        for s, prom in promedios_shape.items():
            alto, ancho, canales = s
            writer.writerow([alto, ancho, canales, prom])

    print("\nPromedios guardados en", ARCHIVO_ENTRENAMIENTO)
    for s, prom in promedios_shape.items():
        print(f"{s}: {prom:.3f} s")

def cargar_promedios():
    promedios_shape = {}
    with open(ARCHIVO_ENTRENAMIENTO, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            shape = (int(row["alto"]), int(row["ancho"]), int(row["canales"]))
            prom = float(row["tiempo_promedio"])
            promedios_shape[shape] = prom
    return promedios_shape

def fase_ejecucion():
    promedios_shape = cargar_promedios()
    imagenes = list(Path(CARPETA_IMAGENES).glob("*.jpg")) + list(Path(CARPETA_IMAGENES).glob("*.png"))
    tiempos_estimados = {}

    print("\n=== ASIGNACIÓN PREDICTIVA ===")
    for path in imagenes:
        img = cv2.imread(str(path))
        if img is None:
            print(f"Error al cargar {path}")
            continue
        shape = img.shape
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

    # --- PROCESAMIENTO PARALELO ---
    print("\n=== PROCESAMIENTO EN PARALELO ===")
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=NUM_HILOS) as executor:
        futures = []
        for i in range(NUM_HILOS):
            futures.append(executor.submit(procesar_lote, tareas_por_hilo[i], i))
        for f in futures:
            f.result()  # Esperar a que todos terminen

    t1 = time.time()
    tiempo_total = t1 - t0

    print(f"Procesamiento terminado. Tiempo total: {tiempo_total:.2f} segundos.")

if __name__ == "__main__":
    # Cambia entre 'entrenamiento' y 'ejecutar' aquí:
    modo = input("Escribe 'entrenamiento' para entrenar o 'ejecutar' para balancear y procesar: ").strip().lower()
    if modo == "entrenamiento":
        fase_entrenamiento()
    elif modo == "ejecutar":
        fase_ejecucion()
    else:
        print("Modo no reconocido.")