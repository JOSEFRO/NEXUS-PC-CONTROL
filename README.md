<div align="center">

<img src="https://d8j0ntlcm91z4.cloudfront.net/user_3MJ8xX039ib9919oo3CFVd7NjMx/hf_20261119_141629_110d8230-27cb-4b12-8c1e-1af9776c6eb4.webp" alt="Arte conceptual de NEXUS PC CONTROL" width="100%">

# NEXUS PC CONTROL

**Aplicación local para diagnóstico de Windows y análisis de almacenamiento.**

[Repositorio](https://github.com/JOSEFRO/NEXUS-PC-CONTROL) · [Incidencias](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/issues) · [Historial](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/commits/main)

![Estado](https://img.shields.io/badge/estado-desarrollo%20activo-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask)
![Plataforma](https://img.shields.io/badge/plataforma-Windows-0078D6?logo=windows)

</div>

## 1. Descripción

NEXUS PC CONTROL es una aplicación local para Windows que presenta información del equipo y permite analizar el almacenamiento desde una interfaz web servida por el propio dispositivo.

No es un servicio web público ni una herramienta de administración remota. La interfaz se abre en el navegador, mientras que el proceso de análisis se ejecuta localmente.

## 2. Capacidades

- Consulta de unidades, capacidad total, espacio utilizado y disponible.
- Indicadores de CPU y memoria RAM.
- Análisis de carpetas admitidas del perfil de usuario.
- Identificación de archivos grandes y ordenamiento de resultados.
- Ejecución en segundo plano y cancelación cooperativa.
- Reporte de cobertura, exclusiones y errores.
- Selección explícita de archivos para enviarlos a la papelera del sistema.

El escaneo es de solo lectura. Las acciones de limpieza son independientes, requieren selección y confirmación y no equivalen a vaciar la papelera.

## 3. Arquitectura y tecnologías

- Python 3.10 o superior.
- Flask 3.1 para el servidor local.
- psutil para métricas del sistema.
- Send2Trash para integración con la papelera.
- HTML, CSS y JavaScript para la interfaz.

### Interfaz local y protocolos

- HTTP sobre loopback para comunicación entre el navegador y el proceso local.
- Dirección prevista: `127.0.0.1:8765`.
- API JSON para iniciar y consultar trabajos de análisis.
- No exponer el servidor local a interfaces públicas ni a redes externas.

## 4. Requisitos

- Windows 10/11.
- Python 3.10 o superior.
- PowerShell o terminal de Windows.
- Dependencias indicadas en `requirements.txt`.

## 5. Inicio rápido

Descarga el ZIP desde [GitHub](https://github.com/JOSEFRO/NEXUS-PC-CONTROL/archive/refs/heads/main.zip), extrae los archivos y ejecuta `INICIAR.bat`.

Inicio manual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```

Abre [http://127.0.0.1:8765](http://127.0.0.1:8765).

## 6. API local

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/storage/scans` | Inicia un análisis admitido. |
| GET | `/api/storage/scans/{scan_id}` | Consulta el estado y los resultados. |
| POST | `/api/storage/scans/{scan_id}/cancel` | Solicita cancelar un análisis. |

Los estados deben distinguir cola, ejecución, cancelación, finalización, finalización con advertencias y error. Si no se conoce el total de elementos, el progreso debe mostrarse como indeterminado.

## 7. Seguridad y privacidad

- Mantén el servidor enlazado exclusivamente a `127.0.0.1`.
- No uses túneles ni reenvío de puertos para publicar el panel.
- Valida cada ruta en el servidor antes de cualquier acción sobre archivos.
- Evita seguir enlaces simbólicos durante el recorrido.
- Mantén el escaneo separado de las acciones de limpieza.
- Exige confirmación explícita para operaciones que modifican archivos.
- No transmitas inventarios de archivos a servicios externos.
- Informa claramente de errores y carpetas excluidas.

Los tamaños mostrados son tamaños lógicos y no necesariamente equivalen al espacio físico asignado en el sistema de archivos.

## 8. Pruebas recomendadas

- Windows 10 y Windows 11.
- Perfiles con permisos restringidos.
- Unidades secundarias y extraíbles.
- Rutas largas, nombres Unicode y enlaces simbólicos.
- Cancelación durante el análisis.
- Errores de acceso y archivos bloqueados.
- Validación de rutas y confirmaciones antes de enviar a la papelera.

## 9. Estado del proyecto

NEXUS está en desarrollo activo. Las pruebas automatizadas deben complementarse con validación manual en equipos Windows reales antes de publicar una versión estable.

## 10. Licencia

No se ha incorporado una licencia de reutilización. El código y los recursos permanecen reservados a su titular salvo autorización expresa.
