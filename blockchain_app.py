import blockchain_test as blockchain
from uuid import uuid4
import requests
import socket
from flask import Flask, jsonify, request
from argparse import ArgumentParser
import json

from threading import Thread, Semaphore
import time
import datetime
import platform

# Instancia del nodo y la aplicación
app = Flask(__name__)

# Para saber mi ip se usa el comando desde la terminal wsl de ifconfig
mi_ip = "http://192.168.1.42"

MainBlockChain = blockchain.Blockchain()
nodos_red = set()

# iniciamos los semáforos a 1
mutex = Semaphore(1)
transaction_block = Semaphore(1)

running = True


# función para guardare el back up
def Backup():
    """
    función que se ejecuta en paralelo, cada 60 segundos llama a la funcion do_Backup para crear una copia de seguridad

    args:
    none

    Return:
    none

    raises:
    None
    """
    global running
    while running:
        mutex.acquire()
        try:
            do_Backup()
            print("archivo de seguridad guardado")

        except Exception as e:
            print("no se ha podido realizar la copia de seguridad")
            print(e)
        finally:
            mutex.release()
            time.sleep(60)

def do_Backup():
    """
    función crea una copia de seguridad con la cadena, la longitud de esta y la fecha de creación

    args:
    none

    Return:
    none

    raises:
    None
    """
    global MainBlockChain 
    # llamamos una sola vez a blockchain_completa para evitar posibles errores
    BC_completa = {
        "chain": [{"indice":b.indice, "transacciones":b.transacciones,"timestamp": b.timestamp, "hash_previo":b.hash_previo, "prueba":b.prueba} for b in MainBlockChain.block_list],
        "longitud": len(MainBlockChain.block_list),
    }
    # obtenemos la cadena y la longitud:
    chain = BC_completa["chain"]
    len_chain = BC_completa["longitud"]

    # obtenemos el tiempo:
    date = datetime.datetime.now()
    date_formated = date.strftime("%d/%m/%Y %H:%M:%S")
    
    backup_data = {
        "cadena de bloques": chain,
        "longitud de la cadena": len_chain,
        "fecha": date_formated
    }

    # Guardamos en un fichero (sobreescribiendo el contenido):
    with open(f"respaldo-nodo{socket.gethostname()}-{args.puerto}.json", "w") as f:
        json.dump(backup_data, f, indent=4)
    

# creamos una página adicional para crear las nuevas transacciones.
@app.route("/transacciones/nueva", methods=["POST"])
def nueva_transaccion():
    """
    función para crear transacciones

    args:
    origen, destino, cantidad

    Return:
    jsonify(
        mensaje de transaccion creada con éxito y el bloque al que se ha añadido
    )
    200: success code

    raises:
    no se obtuvieron los argumentos necesarios
    400 error code
    """

    values = request.get_json()

    # Comprobamos que esten todos los datos de la transaccion utilizando list comprehension
    required = ["origen", "destino", "cantidad"]
    if not all(k in values for k in required):
        return "Faltan valores", 400

    # esto no afecta a la copia de seguridad, pero puede afectar si se está minando un bloque
    # aun que no debería, ya que son procesos que se ejecutan en páginas distintas y en el mismo hilo
    # Creamos una nueva transaccion
    transaction_block.acquire()
    indice = MainBlockChain.nueva_transaccion(
        values["origen"], values["destino"], values["cantidad"]
    )
    response = {
        "mensaje": f"La transaccion se incluira en el bloque con indice {indice}"
    }
    transaction_block.release()
    return jsonify(response), 200

# para obtener la blockchain completa:
@app.route("/chain", methods=["GET"])
def blockchain_completa():
    """
    función para obtener la información del nodo

    args:
    None

    Return:
    jsonify(
        cadena de bloques completa, longitud de la cadena
    )
    200: success code

    raises:
    None
    """
    # utilizamos list comrehension para cear el diccionario non la lista de bloques a devolver.
    response = {
        "chain": [{"indice":b.indice, "transacciones":b.transacciones,"timestamp": b.timestamp, "hash_previo":b.hash_previo, "prueba":b.prueba} for b in MainBlockChain.block_list],
        "longitud": len(MainBlockChain.block_list),
    }

    return jsonify(response), 200

@app.route("/system", methods=["GET"])
def system_info():
    """
    función para obtener la información del nodo

    args:
    None

    Return:
    jsonify(
        procesador de la máquina, su sistema operativo y su versión.
    )
    200: success code

    raises:
    None
    """
    response = {
        "maquina": platform.processor(),
        "sistema operativo": platform.system(),
        "version": platform.release(),
    }
    return jsonify(response), 200

# creamos una nueva página para minar bloques:
@app.route("/minar", methods=["GET"])
def minar():
    """
    función para añadir un bloque a la cadena de bloques, también crea una transacción al nodo que
    haya logrado minar el bloque.

    args:
    Blockchain

    Return:
    jsonify(
        recompensa en el bloque de indice: n, bloque minado
    )
    200: success code

    raises:
    no hay transacciones en el bloque
    400 error code
    """
    global MainBlockChain
    # Si se intenta minar un Bloque que aún no tiene transacciones:
    if len(MainBlockChain.transaccion_list) == 0:
        response = {
            "mensaje": "No es posible crear un nuevo bloque. No hay transacciones"
        }
        return jsonify(response), 400

    # si hay transacciones el bloque se pued minar.
    else:
        mutex.acquire()
        mined = True
        mined = resuelve_conflictos()
        if not mined: 
            response = {
                    "mensaje": "no se ha podido minar, ya que hay una blockchain más larga. Espere a que haya transacciones y vuelva a intentarlo"
                }
        else:    
            hash_anterior = MainBlockChain.block_list[-1].calcular_hash()
            bloque = MainBlockChain.nuevo_bloque(hash_anterior)
            hash_prueba = MainBlockChain.prueba_trabajo(bloque)
            add = MainBlockChain.integra_bloque(bloque, hash_prueba)
        
            """ Hay transaccion, por lo tanto ademas de minar el bloque, recibimos recompensa
            Recibimos un pago por minar el bloque. Creamos una nueva transaccion
            con:
            Dejamos como origen el 0
            Destino nuestra ip
            Cantidad = 1"""

            # verificamos que el bloque se haya integrado:
            if add:
                indice = MainBlockChain.nueva_transaccion("0", mi_ip, 1)
                response = {
                    "mensaje": f"ha recibido una compensación por minar el bloque, esta se incluira en el bloque con indice {indice}"
                }
            else:
                response = {
                    "mensaje": "no se ha podido minar el bloque. la blockchain está corrupta"
                }
        mutex.release()
    

    return jsonify(response), 200


@app.route('/nodos/registrar', methods=['POST'])
def registrar_nodos_completo():
    """
    función para añadir un conjunto de nodos
    args:
    none
    returns:
    mensaje y código de error o acierto.
    raises
    none
    """

    global MainBlockChain
    global nodos_red

    values =request.get_json()

    nodos_nuevos =values["direccion_nodos"]
    if nodos_nuevos is None:
        return "Error: No se ha proporcionado una lista de nodos", 400
    
    all_correct =True

    # añadimos los nodos a nodos_red
    nodos_red = set(nodos_nuevos)
    my_ip = str(mi_ip + ':' + str(puerto))
    nodos_red.add(my_ip)

    for nodo in nodos_nuevos:
        if nodo != {mi_ip + ':' + str(puerto)} and nodo != None:
            nodos_red.discard(nodo)

            # se devuelven los datos
            datos = {
                'nodos_direcciones': list(nodos_red),
                # el mismo método que en blockchain_completa pero sin la longitud
                'MainBlockChain': [{"indice":b.indice, "transacciones":b.transacciones,"timestamp": b.timestamp, "hash_previo":b.hash_previo, "prueba":b.prueba} for b in MainBlockChain.block_list]
            }
            # añadimos el nodo que hemos eliminado antes
            nodos_red.add(nodo)

            # registramos el nodo individualmente
            response = requests.get(
            nodo + "/nodos/registro_simple",
            data=json.dumps(datos),
            headers={"Content-Type": "application/json"},
        )
            # comprobamos que no haya dado error
            if response.status_code != 200:
                all_correct = False
    nodos_red.discard(my_ip)

    if all_correct:
        response ={
            'mensaje': 'Se han incluido nuevos nodos en la red',
            'nodos_totales': list(nodos_red)
        }
    else:
        response ={
            'mensaje': 'Error notificando el nodo estipulado',
        }

    return jsonify(response), 201

# función para crear la blockchain a partir de un json
def json_to_blockchain(blockchain_json):
    main = blockchain.Blockchain()
    for bloque in blockchain_json:
        bloque_class = blockchain.Bloque(
            bloque['indice'],
            bloque['transacciones'],
            bloque['timestamp'],
            bloque['hash_previo'],
            bloque['prueba'],
            )
        if bloque["hash_previo"] != 1:
            main.integra_bloque(bloque_class,bloque_class.calcular_hash())
        else:
            main.block_list[0] = bloque_class
    return main        

@app.route('/nodos/registro_simple', methods=['GET'])
def registrar_nodo_actualiza_blockchain():

    # Obtenemos la variable global de blockchain
    global nodos_red, MainBlockChain

    read_json = request.get_json()

    nodes_addreses = read_json["nodos_direcciones"]
    blockchain_leida = read_json["MainBlockChain"]

    nodos_red = set(nodes_addreses)

    blockchain_leida = json_to_blockchain(blockchain_leida)
    
    if blockchain_leida is None:
        return "El blockchain de la red esta currupto", 400
    else:
        MainBlockChain = blockchain_leida
        return "La blockchain del nodo" +str(mi_ip) +":" +str(puerto) +"ha sido correctamente actualizada", 200

def change_blockchain(new_blockchain:blockchain.Blockchain):
    global MainBlockChain
    MainBlockChain = new_blockchain


# creamos una función para verificar que se pueda minar
def resuelve_conflictos():
    """
    funcion que obtiene la blockchain de mayor longitud dentro de la red de nodos
    args:
    none
    raises:
    InterruptedError si detecta una blockchain corrupta
    """
    global MainBlockChain, nodos_red

    longest_chain = None
    max_length = 0

    for nodo in nodos_red:
        response = requests.get(f"{nodo}/chain")

        if response.status_code == 200:
            cadena_nodo = response.json()["chain"]
            longitud_nodo = response.json()["longitud"]

            if longitud_nodo > max_length:
                longest_chain = json_to_blockchain(cadena_nodo)
                max_length = longitud_nodo

    if max_length > len(MainBlockChain.block_list):
        change_blockchain(longest_chain)
        return False
    else:
        return True

@app.route('/ping', methods=['GET'])
def ping():
    """
    función que envia un ping a todos los nodos de la red para comprobar la conexión
    args:
    none
    rerturns:
    mensaje y código de exíto o fracaso
    raises:
    none
    """
    global mi_ip, puerto, nodos_red

    resultados_ping = []

    for nodo in nodos_red:
        if nodo != f"{mi_ip}:{puerto}":
            datos_ping_nodo = {
                'fuente': f'{mi_ip}:{puerto}',
                'mensaje': 'PING',
                'marca_temporal': time.strftime("%d/%m/%Y %H:%M:%S")
            }
            

            respuesta = requests.post(
                f'{nodo}/pong', 
                data=json.dumps(datos_ping_nodo), 
                headers={'Content-Type': 'application/json'}
            )
            if respuesta.status_code == 200:
                resultados_ping.append({
                    'nodo': nodo,
                    'respuesta_nodo': respuesta.json(),
                })

    estado_final = 'Todos los nodos responden' if resultados_ping else 'algún nodo no ha respondido'
    resultado_final = {'estado_final': estado_final}

    return jsonify({'resultados_ping': resultados_ping, 'resultado_final': resultado_final}), 200

@app.route('/pong', methods=['POST'])
def pong():
    """
    función que recibe un pong y responde
    args:
    fuente, mensaje, marca temporal
    rerturns:
    datos de respuesta y código de exíto o fracaso
    raises:
    none
    """
    global mi_ip, puerto
    datos_ping = request.get_json()
    datos_respuesta = {
        'fuente': f'{mi_ip}:{puerto}',
        'mensaje': f'PONG {datos_ping["fuente"]}',
        'marca_temporal': time.strftime("%d/%m/%Y %H:%M:%S")
    }

    return jsonify(datos_respuesta), 200


def runapp(puerto):
    app.run(host="0.0.0.0", port=puerto)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--puerto", default=5000, type=int, help="puerto para escuchar"
    )
    args = parser.parse_args()
    puerto = args.puerto

    # ejecutamos el hilo para hacer los backups
    backup = Thread(target=Backup)
    backup.start()
    # una vez estan listas las configuraciones, ejecutamos la página.
    runap = Thread(target=runapp,args=(puerto,))    # iniciamos el hilo:
    runap.start()