import json 
import time 
import hashlib

# clase bloque
class Bloque:
    def __init__(self, indice: int, transacciones: list, timestamp: int, hash_previo: str, prueba:int =0):
        self.indice=indice
        self.transacciones = transacciones
        self.timestamp=timestamp
        self.hash_previo = hash_previo
        self.prueba = prueba

    # metodo para calcular el hash del bloque
    def calcular_hash(self):
        block_string =json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

# la clase transacción se sustituye por un diccionario

# clase Blockchain
class Blockchain(object):
    def __init__(self):
        self.dificultad = 4
        self.transaccion_list = []
        self.block_list = [self.primer_bloque()]
        self.indice = 2

    #la blockchain no puede ser una lista vacía, por lo que se crea un bloque sin transacciones.
    def primer_bloque(self): 
        return Bloque(1,None,time.time(),1)
    
    def nueva_transaccion(self, origen: str, destino: str, cantidad: int) ->int:
        
        """
        Crea una nueva transaccion a partir de un origen, un destino y una cantidad y la incluye en las
        listas de transacciones
        """

        self.transaccion_list.append({"origen":origen,
                                      "destino":destino,
                                      "cantidad":cantidad})

        return self.block_list[-1].indice

    def nuevo_bloque(self, hash_previo: str) ->Bloque:
        """
        Crea un nuevo bloque a partir de las transacciones que no estan
        confirmadas
        :param hash_previo: el hash del bloque anterior de la cadena
        :return: el nuevo bloque
        """
        nuevo_bloque = Bloque(self.indice,self.transaccion_list,time.time(),hash_previo)
        self.indice += 1 
        return nuevo_bloque
    
    
    # funcion para obtener el hash del bloque que se quiere añadir
    def prueba_trabajo(self, bloque: Bloque) ->str:
        """
        Algoritmo simple de prueba de trabajo:
        - Calculara el hash del bloque hasta que encuentre un hash que empiece
        por tantos ceros como dificultad
        .
        - Cada vez que el bloque obtenga un hash que no sea adecuado,
        incrementara en uno el campo de
        ``prueba'' del bloque
        :param bloque: objeto de tipo bloque
        :return: el hash del nuevo bloque (dejara el campo de hash del bloque sin
        modificar)
        """
        hash_r = ""
        Searching = True
        ceros = "0" * self.dificultad

        #se comprueva que los ceros del hash sean iguales que la dificultad
        while Searching:
            # al cambiar un parametro del bloque el hash cambia.
            bloque.prueba += 1 
            hash_r = bloque.calcular_hash()

            # verificamos que hash_r pueda cumplir con la condición        
            if len(hash_r) >= self.dificultad:
                # verificamos que los primeros d caracteres sean iguales una cadena de longitud d de ceros:
                if hash_r[:self.dificultad] == ceros:
                    return hash_r     

    # funcion que verifica los que el bloque se pueda añadir
    def prueba_valida(self, bloque: Bloque, hash_bloque: str) ->bool:
        """
        Metodo que comprueba si el hash_bloque comienza con tantos ceros como la
        dificultad estipulada en el
        blockchain
        Ademas comprobara que hash_bloque coincide con el valor devuelvo del
        metodo de calcular hash del
        bloque.
        Si cualquiera de ambas comprobaciones es falsa, devolvera falso y en caso
        contrario, verdarero
        :param bloque:
        :param hash_bloque:
        :return:
        """

        if len(hash_bloque) >= self.dificultad:
            # verificamos que los primeros d caracteres sean iguales una cadena de longitud d de ceros:
            if hash_bloque[:self.dificultad] != "0" * self.dificultad:
                return False 
        
        # se verifica que el hash del bloque que se quiere añadir es el que se proporciona como medida de seguridad
        if bloque.calcular_hash() != hash_bloque: 
            return False 
        
        return True 
    
    # función para integrar el bloque 
    def integra_bloque(self, bloque_nuevo: Bloque, hash_prueba: str) ->bool:
        """
        Metodo para integrar correctamente un bloque a la cadena de bloques.
        Debe comprobar que hash_prueba es valida y que el hash del bloque ultimo
        de la cadena
        coincida con el hash_previo del bloque que se va a integrar. Si pasa las
        comprobaciones, actualiza el hash
        7
        del bloque nuevo a integrar con hash_prueba, lo inserta en la cadena y
        hace un reset de las
        transacciones no confirmadas (
        vuelve
        a dejar la lista de transacciones no confirmadas a una lista vacia)
        :param bloque_nuevo: el nuevo bloque que se va a integrar
        :param hash_prueba: la prueba de hash
        :return: True si se ha podido ejecutar bien y False en caso contrario (si
        no ha pasado alguna prueba)
        """
        # se llama a la funcion prueva valida para verificar que se puede añadir el bloque:
        if not self.prueba_valida(bloque_nuevo,hash_prueba): 
            return False
        
        # se verifica que el hash previo del bloque a añadir coincida con el hash del bloque sobre el que se añade. 
        if  self.block_list[-1].calcular_hash() != bloque_nuevo.hash_previo: 
            return False
        
        # se cambia el hash del bloque nuevo y se añade a la blocklist
        bloque_nuevo.hash = hash_prueba 
        self.block_list.append(bloque_nuevo)

        # se reinicia la lista de transferencias.
        self.transaccion_list = []
        return True 