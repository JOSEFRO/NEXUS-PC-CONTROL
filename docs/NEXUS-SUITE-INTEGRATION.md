# NEXUS Suite Integration — diseño y criterios de entrega

**Estado:** base de trabajo iniciada en `feature/nexus-suite-integration`; endurecimiento de eliminación recuperable en `feat/nexus-safe-trash`. No declarar los módulos como disponibles hasta completar API, interfaz y validación en Windows 10/11.

## Módulos de producto

- **Storage Explorer:** navegación por categorías y carpetas personales, selección múltiple, vista previa y borrado confirmado. AppData y Program Files permanecen en solo lectura.
- **Duplicate Finder:** agrupación por tamaño y verificación SHA-256 por bloques. Categorías: imágenes, documentos, vídeo, audio y todos los archivos. La detección identifica contenido idéntico byte a byte; no promete detectar imágenes visualmente parecidas o archivos reexportados. Nunca elimina automáticamente.
- **Eliminación revisable:** los archivos personales seleccionados se envían a la papelera del sistema mediante Send2Trash; NEXUS no debe afirmar que el espacio se liberó hasta que la papelera se vacíe.
- **App Manager:** inventario de programas desde fuentes nativas de Windows (registro de desinstalación y paquetes instalados), solo lectura. Debe mostrar nombre, editor, versión, arquitectura y origen. No desinstalar ni modificar programas desde el primer lanzamiento.
- **Downloads Manager:** acceso directo a Descargas, filtro, orden, selección y eliminación confirmada. La papelera/recuperación debe ser una preferencia explícita; no prometer recuperación si no está implementada.
- **Settings:** preferencias locales con esquema permitido, idioma, tema, módulos visibles, opciones de análisis y notificaciones. No guardar claves, credenciales ni telemetría.
- **Dashboard:** indicadores de unidades, análisis recientes, duplicados confirmados, errores y espacio potencial recuperable; distinguir siempre estimaciones de espacio realmente liberado.

## Referencias de producto

Inspiración de patrones, sin copiar marcas ni recursos: Microsoft Windows Storage (categorías y limpieza revisable), WizTree (inventario rápido), TreeSize (jerarquía y tamaños), WinDirStat (categorías visuales), dupeGuru (revisión de duplicados), Revo Uninstaller (inventario de aplicaciones). Revalidar funciones y licencias antes de publicar comparativas comerciales.

## Reglas obligatorias

1. Servidor Flask únicamente en `127.0.0.1:8765`; nunca desplegar en hosting ni túneles.
2. Escaneo de solo lectura, sin seguir enlaces simbólicos ni puntos de reanálisis.
3. No borrar manualmente Windows, Program Files, AppData, ni discos virtuales `.vdi/.vmdk`.
4. Confirmación explícita y validación de rutas inmediatamente antes de enviar archivos a la papelera; no usar `unlink()` para la eliminación iniciada desde el explorador.
5. Los módulos pueden ocultarse/desactivarse en preferencias, pero ocultar un módulo no cambia sus permisos ni desactiva las protecciones de seguridad.
6. Mostrar cobertura, errores y cancelaciones; no inventar porcentajes ni espacio recuperado.
7. Preferencias persistidas localmente en el perfil del usuario; no sincronizar ni transmitir inventario.

## Fases

- **S1:** preferencias locales y servicio de detección exacta de duplicados (base añadida).
- **S2:** endpoints de configuración y escaneo con trabajos cancelables.
- **S3:** interfaz premium, navegación de Descargas y revisión de duplicados.
- **S4:** inventario de aplicaciones Windows, solo lectura.
- **S5:** pruebas unitarias/API, CI Windows y validación física en Windows 10/11.
