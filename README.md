# Blockchain Distribuida — API REST en Python
 
Proyecto final de la asignatura **Fundamentos de los Sistemas Operativos** (IMAT).  
Implementación completa de una Blockchain descentralizada con API REST en Flask, soporte multi-nodo, prueba de trabajo (Proof of Work), backups automáticos y protocolo Ping/Pong de conectividad.
 
---
 
## Descripción
 
El proyecto implementa una Blockchain funcional que puede ejecutarse en múltiples nodos (máquinas físicas o virtuales) de forma simultánea. Cada nodo expone una API REST con la que se pueden crear transacciones, minar bloques, consultar la cadena y sincronizarse con el resto de la red.
 
**Características principales:**
- Estructura de bloques enlazados por hash SHA-256
- Algoritmo de Proof of Work configurable por dificultad
- API REST con Flask para interactuar con la cadena
- Red descentralizada: varios nodos se sincronizan entre sí
- Resolución de conflictos: siempre prevalece la cadena más larga
- Backup automático en JSON cada 60 segundos (hilo paralelo)
- Protocolo Ping/Pong para verificar conectividad entre nodos
- Semáforos para gestión de concurrencia entre hilos
---
 
## Estructura del proyecto
 
```
blockchain/
├── blockchain.py        # Clases Bloque y Blockchain con la lógica central
├── blockchain_app.py    # API REST Flask + gestión de nodos + hilos
├── resquests.py         # Script de prueba: crea transacciones y mina bloques
└── README.md
```
 
| Archivo | Descripción |
|---|---|
| `blockchain.py` | Define `Bloque`, `Blockchain`, Proof of Work e integración de bloques |
| `blockchain_app.py` | Servidor Flask con todos los endpoints, backup y red multi-nodo |
| `resquests.py` | Cliente de prueba que automatiza transacciones y minado |
 
---
 
## Cómo ejecutar
 
**Requisitos:** Python 3.x
 
```bash
pip install flask requests
```
 
**Iniciar un nodo** (por defecto en el puerto 5000):
```bash
python blockchain_app.py
```
 
**Iniciar un nodo en un puerto específico:**
```bash
python blockchain_app.py -p 5001
```
 
Para una red multi-nodo, ejecuta el comando en distintas máquinas o máquinas virtuales con sus respectivas IPs y puertos.
 
---
 
## API — Endpoints disponibles
 
### `GET /system`
Devuelve información del sistema donde corre el nodo.
```json
{
  "maquina": "Intel64 Family 6 Model 183",
  "sistema operativo": "Windows",
  "version": "10"
}
```
 
### `POST /transacciones/nueva`
Crea una nueva transacción pendiente de ser minada.
```json
{
  "origen": "nodoA",
  "destino": "nodoB",
  "cantidad": 100
}
```
 
### `GET /chain`
Devuelve la blockchain completa del nodo con su longitud.
```json
{
  "chain": [...],
  "longitud": 2
}
```
 
### `GET /minar`
Mina un nuevo bloque con las transacciones pendientes. Requiere que haya al menos una transacción. El nodo que mina recibe una recompensa de 1 unidad automáticamente.
 
### `POST /nodos/registrar`
Registra uno o varios nodos nuevos en la red y les envía una copia actualizada de la blockchain.
```json
{
  "direccion_nodos": ["http://192.168.1.58:5000", "http://192.168.1.59:5000"]
}
```
 
### `GET /nodos/registro_simple`
Endpoint interno: recibe la lista de nodos y la blockchain del nodo principal y se actualiza.
 
### `GET /ping`
Envía un ping a todos los nodos registrados y devuelve el resultado de conectividad.
 
### `POST /pong`
Responde a un ping con los datos del nodo receptor (fuente, mensaje y marca temporal).
 
---
 
## Arquitectura del código
 
### Clase `Bloque`
Cada bloque contiene:
 
| Campo | Tipo | Descripción |
|---|---|---|
| `indice` | int | Identificador único del bloque |
| `transacciones` | list | Lista de transacciones incluidas |
| `timestamp` | float | Momento de creación |
| `hash_previo` | str | Hash del bloque anterior (garantiza integridad) |
| `prueba` | int | Nonce para el Proof of Work |
 
### Clase `Blockchain`
| Método | Descripción |
|---|---|
| `primer_bloque()` | Crea el bloque génesis que inicia la cadena |
| `nueva_transaccion()` | Añade una transacción a la lista pendiente |
| `nuevo_bloque()` | Crea un bloque con las transacciones pendientes |
| `prueba_trabajo()` | Calcula el hash válido (empieza por N ceros) |
| `prueba_valida()` | Verifica que el hash cumple la dificultad |
| `integra_bloque()` | Añade el bloque validado a la cadena |
 
### Proof of Work
El algoritmo incrementa el campo `prueba` del bloque hasta encontrar un hash SHA-256 que empiece por `dificultad` ceros (por defecto 4):
 
```python
while hash_r[:dificultad] != "0000":
    bloque.prueba += 1
    hash_r = bloque.calcular_hash()
```
 
---
 
## Funcionamiento multi-nodo
 
1. Se lanza el nodo principal con `blockchain_app.py`.
2. Se registran los demás nodos con `POST /nodos/registrar`.
3. Cada nodo recibe una copia de la blockchain y la lista de nodos de la red.
4. Al minar, cada nodo ejecuta `resuelve_conflictos()`: si existe una cadena más larga en la red, la adopta antes de minar.
5. El backup automático guarda un fichero `respaldo-nodoX-PUERTO.json` cada 60 segundos.
---
 
## Concurrencia
 
Se usan dos semáforos para evitar condiciones de carrera entre hilos:
 
- `mutex` — protege el acceso a la blockchain durante el minado y el backup.
- `transaction_block` — protege la lista de transacciones pendientes al crear nuevas.
---
 
## Tecnologías
 
- Python 3
- `Flask` — servidor web y API REST
- `hashlib` — hashing SHA-256
- `requests` — comunicación HTTP entre nodos
- `threading` — ejecución paralela de backup y servidor
- `socket` / `platform` — información del sistema
---
 
## Autores
 
- **Guzmán Pérez**
- **Santiago Urtiaga**
Proyecto entregado en el Grado en Ingeniería Matemática e Inteligencia Artificial (IMAT) — Comillas ICAI, Fundamentos de los Sistemas Operativos.
 
