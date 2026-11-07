# NEXUS PC CONTROL

**Panel local de diagnóstico de Windows** para revisar almacenamiento, localizar archivos grandes y consultar CPU/RAM antes de tomar decisiones de mantenimiento.

> El programa se ejecuta en tu propio equipo y escucha únicamente en `127.0.0.1:8765`. No es una herramienta remota ni debe exponerse a Internet.

[Repositorio](https://github.com/JOSEFRO/NEXUS-PC-CONTROL) · [Descargar ZIP](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/archive/refs/heads/main.zip)

## Funciones
- Vista de todas las unidades detectadas, con uso y espacio libre.
- Análisis aproximado de carpetas habituales del perfil del usuario.
- Búsqueda manual de archivos de 1 GB o más; solo informa, no elimina.
- Revisión de tres ubicaciones temporales permitidas.
- Lectura de CPU, memoria RAM y versión del entorno.
- Interfaz en español, responsive y con identidad JOSEFRO.

## Mejoras de seguridad incluidas
- Renderizado de nombres y rutas mediante nodos de texto, evitando interpretar nombres de archivos como HTML.
- Validación de host local para reducir el riesgo de acceso mediante DNS rebinding.
- Cabeceras HTTP de protección, límite del cuerpo JSON y validación de selección.
- La limpieza sigue siendo manual, limitada a categorías predefinidas y con confirmación del usuario.

## Requisitos
- Windows 10 u 11.
- Python 3.10 o superior.
- Conexión inicial para instalar Flask y psutil.

## Instalación rápida
1. Descarga y extrae el ZIP.
2. Ejecuta `INICIAR.bat`.
3. Abre `http://127.0.0.1:8765` si el navegador no se inicia automáticamente.

Desde una terminal:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

## Uso seguro
1. Analiza y revisa las unidades y carpetas.
2. Ejecuta la búsqueda de archivos grandes solo si la necesitas.
3. Lee las descripciones de las ubicaciones temporales.
4. No selecciones una categoría si no comprendes su contenido.
5. Conserva copias de seguridad de los archivos importantes.

No elimina descargas, documentos, fotos, proyectos, juegos, máquinas virtuales ni archivos personales. Los archivos bloqueados o inaccesibles se omiten. El tamaño de carpetas es aproximado y puede omitir datos protegidos.

## Límites conocidos
- No reemplaza el Liberador de espacio de Windows ni las herramientas oficiales de diagnóstico.
- No realiza mediciones de benchmark ni optimizaciones automáticas.
- No se ha verificado todavía un empaquetado instalable ni compatibilidad con todas las variantes de Windows.
- La limpieza requiere pruebas adicionales en entornos controlados antes de considerarse lista para producción.

## Stack
Python · Flask · psutil · HTML · CSS · JavaScript

## Licencia
No se ha añadido una licencia de reutilización. El código permanece reservado a su propietario salvo autorización expresa.
