// Balanceo Centralizado
#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <string.h>
#include <dirent.h>
#include <sys/stat.h>
#include <windows.h>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#define MAX_ARCHIVOS 200
#define MAX_NOMBRE 256

const char *carpeta_entrada = "H:\\GIT\paralela-parcial-3\\Laboratorio 1 p 3\\imagenes";
const char *carpeta_salida  = "H:\\GIT\\paralela-parcial-3\\Laboratorio 1 p 3\\salida";

void convertir_a_grises(const char *nombre_archivo, const char *nombre_salida) {
    int width, height, channels;
    unsigned char *img = stbi_load(nombre_archivo, &width, &height, &channels, 0);
    if (img == NULL) {
        printf("Error al cargar la imagen %s\n", nombre_archivo);
        return;
    }

    unsigned char *img_grises = (unsigned char *)malloc(width * height);
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int idx = (y * width + x) * channels;
            unsigned char gray = (unsigned char)(0.299 * img[idx] + 0.587 * img[idx + 1] + 0.114 * img[idx + 2]);
            img_grises[y * width + x] = gray;
        }
    }

    stbi_write_png(nombre_salida, width, height, 1, img_grises, width);
    free(img_grises);
    stbi_image_free(img);
}

int es_imagen(const char *nombre) {
    const char *ext = strrchr(nombre, '.');
    return (ext && (strcmp(ext, ".png") == 0 || strcmp(ext, ".jpg") == 0 || strcmp(ext, ".bmp") == 0));
}

void crear_carpeta(const char *ruta) {
    if (CreateDirectory(ruta, NULL) || GetLastError() == ERROR_ALREADY_EXISTS) {
        // Carpeta creada o ya existe
    } else {
        printf("Error al crear la carpeta: %s\n", ruta);
    }
}

int main(int argc, char *argv[]) {
    int num_hilos = 4;

    if (argc > 1) {
        num_hilos = atoi(argv[1]);
    } else {
        printf("Ingrese el numero de hilos a utilizar: ");
        scanf("%d", &num_hilos);
    }

    if (num_hilos < 2) {
        printf("Debe usar al menos 2 hilos (1 maestro + 1 trabajador).\n");
        return 1;
    }

    char archivos[MAX_ARCHIVOS][MAX_NOMBRE];
    int n_archivos = 0;

    DIR *d = opendir(carpeta_entrada);
    struct dirent *dir;
    if (d) {
        while ((dir = readdir(d)) != NULL && n_archivos < MAX_ARCHIVOS) {
            if (es_imagen(dir->d_name)) {
                snprintf(archivos[n_archivos], sizeof(archivos[n_archivos]), "%s\\%s", carpeta_entrada, dir->d_name);
                n_archivos++;
            }
        }
        closedir(d);
    } else {
        printf("No se pudo abrir la carpeta de entrada.\n");
        return 1;
    }

    if (n_archivos == 0) {
        printf("No se encontraron imagenes en la carpeta de entrada.\n");
        return 0;
    }

    crear_carpeta(carpeta_salida);
    double start_time = omp_get_wtime();

    omp_set_num_threads(num_hilos);
    printf("Hilo maestro asignando tareas con %d hilos disponibles...\n", num_hilos);

    #pragma omp parallel
    {
        int thread_id = omp_get_thread_num();
        int total_threads = omp_get_num_threads();

        if (thread_id == 0) {
            for (int i = 0; i < n_archivos; i++) {
                int hilo_asignado = i % (total_threads - 1) + 1;

                char nombre_salida[MAX_NOMBRE];
                snprintf(nombre_salida, sizeof(nombre_salida), "%s\\gris_%s", carpeta_salida, strrchr(archivos[i], '\\') + 1);

                printf("Hilo maestro asignando la imagen %s a hilo %d...\n", strrchr(archivos[i], '\\') + 1, hilo_asignado);

                #pragma omp task
                {
                    convertir_a_grises(archivos[i], nombre_salida);
                }
            }
        }
    }

    #pragma omp taskwait
    double end_time = omp_get_wtime();

    printf("Todas las imagenes han sido procesadas y guardadas en '%s'.\n", carpeta_salida);
    printf("Tiempo total de procesamiento: %.2f segundos.\n", end_time - start_time);

    return 0;
}


