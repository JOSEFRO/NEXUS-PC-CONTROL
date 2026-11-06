# NEXUS PC CONTROL

<p align="center">
  <img src="docs/images/nexus-pc-control-preview.svg" alt="Vista conceptual de NEXUS PC CONTROL" width="100%">
</p>

**Diagnóstico local y mantenimiento prudente para Windows.** NEXUS PC CONTROL reúne en un panel web local información de almacenamiento y recursos del equipo para ayudarte a entender qué ocupa espacio antes de tomar decisiones.

> Es una herramienta local: el servidor Flask se enlaza a `127.0.0.1` y el panel se abre en tu navegador. No es un servicio remoto ni una página pública de control del ordenador.

[Ver repositorio](https://github.com/JOSEFRO/NEXUS-PC-CONTROL) · [Descargar ZIP](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/archive/refs/heads/main.zip) · [Reportar un problema](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/issues)

## Funciones actuales

- Resumen de unidades, espacio usado y espacio libre.
- Análisis de carpetas habituales del perfil de usuario.
- Búsqueda bajo demanda de archivos grandes (desde 1 GB).
- Lista de ubicaciones temporales permitidas para revisión antes de limpiar.
- Lecturas básicas de CPU y memoria RAM.
- Interfaz web en español con navegación por secciones.

## Diseño

Panel de control oscuro con identidad NEXUS, acentos cyan/azul, navegación lateral, indicadores de estado y tarjetas de diagnóstico. El diseño se adapta a pantallas pequeñas; los valores de la imagen de vista previa son ilustrativos, no telemetría real.

## Tecnologías

- Python 3.10+
- Flask 3.1
- psutil 7
- HTML, CSS y JavaScript

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior disponible en PATH.
- Conexión a Internet para instalar dependencias la primera vez.

## Instalación

1. Descarga el ZIP desde el repositorio y extrae su contenido.
2. Abre la carpeta extraída.
3. Ejecuta `INICIAR.bat`.
4. Espera a que se prepare el entorno y se instalen las dependencias.
5. Abre `http://127.0.0.1:8765` en tu navegador si no se abre automáticamente.

También puedes iniciar desde una terminal:

```bash
git clone https://github.com/JOSEFRO/NEXUS-PC-CONTROL.git
cd NEXUS-PC-CONTROL
py -m venv .venv
.venv\\Scripts\\activate
py -m pip install -r requirements.txt
py app.py
```

## Uso recomendado

1. Pulsa **Analizar ahora** y espera el resultado.
2. Revisa las rutas y tamaños informados.
3. Usa la búsqueda de archivos grandes solo cuando la necesites.
4. Revisa cada candidato temporal y su descripción antes de seleccionarlo.
5. Confirma únicamente los elementos que comprendas y que no necesites.
6. Ejecuta un nuevo análisis para comprobar los cambios.

## Seguridad y límites

- Mantén el servidor en `127.0.0.1`; no lo expongas a Internet ni a redes públicas.
- El análisis puede omitir archivos protegidos, bloqueados o inaccesibles.
- Los tamaños de carpetas pueden solaparse cuando una contiene otra.
- No elimines archivos del sistema, controladores, programas, proyectos, juegos, partidas o máquinas virtuales sin comprobar su función y disponer de una copia de seguridad.
- La limpieza temporal no sustituye una copia de seguridad.
- No es necesario ejecutar como administrador para el análisis habitual; evita elevar permisos salvo que una función documentada lo requiera.

## Desarrollo y comprobaciones

```bash
py -m pip install -r requirements.txt
py app.py
```

Antes de distribuir una versión, prueba en distintos equipos Windows, valida rutas y permisos, revisa los mensajes de error y verifica que el servidor siga limitado a loopback.

## Estado

Prototipo funcional en evolución. No debe presentarse como limpiador automático ni como herramienta de mantenimiento de producción hasta completar pruebas de seguridad, compatibilidad, recuperación y empaquetado.

## Licencia

No se ha añadido una licencia de reutilización. El proyecto permanece reservado a su propietario salvo autorización expresa.
