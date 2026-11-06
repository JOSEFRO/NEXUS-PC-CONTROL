# NEXUS PC CONTROL

Panel local para analizar almacenamiento y recursos de Windows 10/11.

## Funciones
- Vista de unidades y espacio libre.
- Estimación de carpetas habituales del perfil.
- Búsqueda de archivos grandes (>= 1 GB) dentro del perfil.
- Limpieza selectiva de temporales conocidos.
- Métricas de CPU y RAM.

## Inicio
1. Instala Python 3.10 o superior.
2. Descarga este repositorio o extrae el ZIP de distribución.
3. Ejecuta `INICIAR.bat`.
4. Abre http://127.0.0.1:8765.

## Seguridad
- El servidor escucha solo en 127.0.0.1.
- La limpieza solo admite categorías temporales predefinidas.
- No elimina Descargas, Documentos, juegos ni máquinas virtuales.
- No desactiva antivirus, servicios, controladores ni programas de inicio.
- Los archivos bloqueados o sin permisos se omiten.

## Limitaciones de v1
El escaneo de carpetas es una estimación de profundidad limitada. Los archivos grandes se buscan dentro del perfil de usuario. La versión inicial no modifica configuración de juegos ni mide temperatura de GPU.

## Aviso
Revisa siempre las rutas y los elementos seleccionados antes de limpiar. Haz una copia de seguridad de los datos importantes.
