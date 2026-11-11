<div align="center">

<img src="docs/images/nexus-identity.svg" alt="Identidad visual NEXUS PC CONTROL" width="100%">

# NEXUS PC CONTROL

### Comprende tu equipo. Analiza el almacenamiento. Actúa con control.

**Herramienta local para Windows que reúne diagnóstico del sistema y análisis de almacenamiento en una interfaz visual.**

[📂 Repositorio](https://github.com/JOSEFRO/NEXUS-PC-CONTROL) · [⬇ Descargar ZIP](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/archive/refs/heads/main.zip) · [🧾 Cambios recientes](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/commits/main)

<sub>Proyecto de JOSEFRO · Python / Flask</sub>

</div>

## Vista del producto

![Vista conceptual de NEXUS PC CONTROL](docs/images/nexus-pc-control-preview.svg)

[Ver flujo de uso](docs/images/nexus-workflow.svg) · [Arquitectura](docs/ARCHITECTURE.md) · [Registro de cambios](CHANGELOG.md)

> Las imágenes del repositorio son previews conceptuales de la interfaz, no capturas certificadas de ejecución en un equipo Windows.

## Qué es NEXUS

NEXUS PC CONTROL es una aplicación de escritorio/local para Windows. Inicia un servidor en el propio equipo y muestra el panel en el navegador mediante `127.0.0.1:8765`.

**No es un servicio web público ni una herramienta para administrar computadoras por Internet.** Los datos del equipo se consultan localmente.

## Funciones principales

### Diagnóstico del sistema
- Consulta de unidades detectadas y capacidad utilizada/disponible.
- Indicadores visuales de capacidad por unidad.
- Lecturas de CPU y memoria RAM.
- Medidores gráficos para facilitar la interpretación de los recursos.
- Información del entorno de ejecución.

### Análisis de almacenamiento
- Escaneo de carpetas admitidas del perfil de usuario.
- Búsqueda de archivos grandes con umbral configurable.
- Ejecución de análisis en segundo plano.
- Contadores de archivos, carpetas y bytes observados.
- Cancelación cooperativa y resultados parciales cuando corresponde.
- Reporte de cobertura, errores, exclusiones y enlaces simbólicos omitidos.
- Resultados ordenados por tamaño.

### Explorador y acciones cuidadosas
- Presenta resultados para que el usuario los revise antes de actuar.
- Los archivos seleccionados en las ubicaciones admitidas se envían a la papelera del sistema mediante Send2Trash.
- La interfaz distingue entre enviar a la papelera y liberar espacio: el espacio no se considera recuperado hasta vaciar la papelera.
- La operación vuelve a validar la ruta y el tipo de archivo antes de enviarlo a la papelera.

Las acciones de limpieza disponibles requieren selección y confirmación. El análisis no borra archivos.

## Inicio rápido en Windows

**Requisitos:** Windows 10/11, Python 3.10 o superior y conexión inicial para instalar dependencias.

1. Descarga el ZIP del repositorio y extrae su contenido.
2. Ejecuta `INICIAR.bat`.
3. Espera a que se instalen las dependencias y arranque el servidor.
4. Abre [http://127.0.0.1:8765](http://127.0.0.1:8765) si el navegador no se abre automáticamente.

También puedes iniciarlo desde PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

## API local de análisis

| Método | Ruta | Función |
|---|---|---|
| POST | `/api/storage/scans` | Inicia un análisis admitido. |
| GET | `/api/storage/scans/{scan_id}` | Consulta el estado, contadores y resultados. |
| POST | `/api/storage/scans/{scan_id}/cancel` | Solicita cancelar el análisis. |

Los estados del trabajo distinguen entre cola, ejecución, cancelación, finalización, finalización con advertencias y error. Cuando no se conoce el total de elementos, el progreso se presenta como indeterminado en vez de inventar un porcentaje.

Consulta la [especificación de Storage Intelligence](docs/STORAGE-INTELLIGENCE-2.0.md).

## Privacidad y seguridad

- El servidor local debe permanecer ligado a `127.0.0.1`.
- No publiques el servidor en una IP pública, túnel o alojamiento web.
- El escaneo de almacenamiento es de solo lectura.
- No se siguen enlaces simbólicos durante el recorrido.
- Se muestran exclusiones y errores para no confundir cobertura parcial con análisis completo.
- La aplicación no necesita enviar inventarios de archivos a servicios externos.
- Las acciones de limpieza están separadas del escaneo y requieren confirmación.

Los tamaños mostrados representan tamaño lógico y no necesariamente espacio físico asignado en NTFS. El análisis del perfil tampoco equivale a un inventario completo del disco.

## Tecnología

Python · Flask · psutil · Send2Trash · HTML · CSS · JavaScript · GitHub Actions

## Estado y validación

NEXUS se encuentra en desarrollo activo. La integración actual incluye mejoras de seguridad al enviar archivos a la papelera y visualizaciones de almacenamiento, CPU y RAM.

Las comprobaciones automatizadas recientes de GitHub Actions finalizaron correctamente en los entornos configurados. Aun así, se recomienda realizar una prueba manual en equipos físicos Windows 10/11, con unidades NTFS secundarias o extraíbles, perfiles redirigidos y carpetas con permisos restringidos.

La aprobación de CI no sustituye esas pruebas físicas ni garantiza compatibilidad con todas las configuraciones de Windows.

## Próximas mejoras

- Vista de árbol y filtros avanzados de almacenamiento.
- Detección y comparación de archivos duplicados con revisión manual.
- Historial de análisis y reportes exportables.
- Mejoras de accesibilidad y estados de error.
- Pruebas adicionales en equipos Windows reales.

## Licencia

No se ha añadido una licencia de reutilización. El código y los recursos permanecen reservados a su propietario salvo autorización expresa.
