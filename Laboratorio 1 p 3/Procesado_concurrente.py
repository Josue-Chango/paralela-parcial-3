import os
import time
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import threading

# Índice compartido para que cada hilo tome la siguiente imagen
indice_imagen = 0
lock = threading.Lock()
#total_tiempo=0

def es_imagen(nombre_archivo):
    nombre = nombre_archivo.lower()
    return nombre.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))

def procesar_imagen(archivo_entrada, carpeta_salida):
    total_tiempo=0
    global indice_imagen
    while True:
        with lock:
            index = indice_imagen
            indice_imagen += 1
        if index >= len(archivos):
            break

        archivo = archivos[index]
        try:
            print(f"Hilo {threading.current_thread().name} procesando: {archivo}")
            
            t0=time.time()
            # Abre la imagen y verifica si se cargó correctamente
            imagen = Image.open(archivo)
            if imagen is None:
                print(f"No se pudo cargar la imagen {archivo}")
                continue

            # Procesar toda la imagen a escala de grises
            imagen_gris = imagen.convert("L")

            # Guardar imagen con prefijo gris_
            nombre_salida = f"gris_{os.path.basename(archivo)}"
            archivo_salida = os.path.join(carpeta_salida, nombre_salida)

            # Guardar la imagen en el formato original
            imagen_gris.save(archivo_salida)

            print(f"Hilo {threading.current_thread().name} guardó: {archivo_salida}")
            t1=time.time()
            total_tiempo=t1-t0+total_tiempo
            
        
        except Exception as e:
            print(f"Error procesando imagen {archivo}: {e}")
    print(f"Procesamiento terminado. Tiempo total: {total_tiempo:.3f} segundos.")

if __name__ == "__main__":
    carpeta_entrada = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\imagenes"
    carpeta_salida = r"H:\GIT\4rto\Paralela\Parcial3\Laboratorios\Laboratorio1\salida"

    if not os.path.exists(carpeta_salida):
        os.makedirs(carpeta_salida)

    # Filtrar solo las imágenes válidas
    archivos = [os.path.join(carpeta_entrada, f) for f in os.listdir(carpeta_entrada) if os.path.isfile(os.path.join(carpeta_entrada, f)) and es_imagen(f)]

    if not archivos:
        print("Carpeta vacía o no encontrada.")
    else:
        # Solicitar al usuario el número de hilos
        while True:
            try:
                numero_hilos = int(input("Ingrese el número de hilos a utilizar (por defecto 4): ") or 4)
                if numero_hilos <= 0:
                    raise ValueError("El número de hilos debe ser mayor que 0.")
                break
            except ValueError as e:
                print(f"Entrada inválida: {e}. Por favor, intente nuevamente.")

        with ThreadPoolExecutor(max_workers=numero_hilos) as executor:
            
            executor.map(lambda archivo: procesar_imagen(archivo, carpeta_salida), archivos)
            
        print("Procesamiento completo de todas las imágenes.")
