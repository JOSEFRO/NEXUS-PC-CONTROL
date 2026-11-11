# Lista de verificación de publicación — NEXUS PC CONTROL

## Verificación automatizada

- [x] Workflow de comprobaciones completado correctamente en GitHub Actions.
- [x] Suite de pruebas automatizadas incluida en el repositorio.
- [x] Documentación de arquitectura y seguridad enlazada desde README.

Ejecución revisada: [NEXUS PC CONTROL checks](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/actions).

## Pruebas manuales pendientes en Windows 10/11

- [ ] Instalación limpia usando el procedimiento documentado.
- [ ] Arranque y cierre del servidor local.
- [ ] Confirmar que el servidor escucha únicamente en `127.0.0.1`.
- [ ] Lectura de CPU, RAM y unidades en el panel.
- [ ] Análisis de una carpeta pequeña conocida y comparación de resultados.
- [ ] Manejo de rutas sin permisos y archivos bloqueados.
- [ ] Cancelación de un análisis activo.
- [ ] Enviar un archivo de prueba a la papelera y confirmar que se puede restaurar.
- [ ] Verificar que el tamaño enviado a papelera no se informa como espacio ya liberado.
- [ ] Probar unidades extraíbles y perfiles con rutas redirigidas.
- [ ] Revisar errores, cobertura parcial y mensajes de progreso.

## Evidencia visual requerida

Tomar capturas reales desde Windows, ocultando nombres de usuario y rutas privadas:
1. Panel principal con CPU y RAM.
2. Vista de unidades y capacidad.
3. Resultado de análisis de almacenamiento.
4. Pantalla de confirmación de papelera.
5. Vista móvil/responsive del panel local, si se admite oficialmente.

Guardar en `docs/screenshots/`. No sustituir estas pruebas por capturas ilustrativas o generadas.

## Criterio de salida

No anunciar NEXUS como probado en Windows hasta ejecutar esta lista en una máquina física o VM Windows y registrar versión de Windows, Python y resultado.
