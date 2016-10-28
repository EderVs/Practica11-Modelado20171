# -*- encoding: utf-8 -*-
"""
    Servidor del juego de snake 

    Todo el código lo haré en inglés pero los comentarios
    serán en español
"""

import sys

from PyQt4 import QtGui, QtCore, uic
from xmlrpc.server import SimpleXMLRPCServer
from random import randint
import uuid

class Snake():
    """
        Serán las serpientes que utilizaran los usuarios.
    """
    # red, green, blue son utilizados para definir el color de la serpiente
    # de forma
    def __init__(self, id):
        """
            Constructor de la clase Snake
            
            red, green, blue son utilizados para definir el color de la serpiente
            de forma que sea como código rgba
        """
        # Creamos su id
        self.id = id
        # Crearemos el color de manera aleatoria
        red, green, blue = randint(0, 255), randint(0, 255), randint(0, 255)
        # Los guardamos en un diccionario y así representamos el color
        self.color = {'r': red, 'g': green, 'b': blue}
        # Representaremos la serpiente como una lista de listas de 2 elementos
        self.body = []
        # Esto lo hacemos para evitar estar calculando siempre el tamaño del
        # cuerpo de la serpiente
        self.body_len = len(self.body)
        # De esta manero sabremos hacia donde está mirando la serpiente
        # 0: Arriba
        # 1: Derecha
        # 2: Abajo
        # 3: Izquierda
        self.direction = 0

    def get_dict(self):
        """
            Nos da la información de la serpiente en un diccionario
        """
        snake_dict = {
            'id': self.id,
            # Crearemos una lista de tuplas donde vengan las coordenadas de la
            # serpiente 
            'camino': [(x, y) for x, y in self.body],
            'color': self.color
        }
        return snake_dict


class ServerWindow(QtGui.QMainWindow):
    """
        Ventana principal del servidor.
    """

    def __init__(self):
        """
            Constructor de la clase.
        """
        super(ServerWindow, self).__init__()
        uic.loadUi('servidor.ui', self)

        # Vamos a poner unos atributos a la clase
        # Variables para saber el estado del juego
        self.game_started = self.game_paused = False
        # Se inicia el servidor sólo al oprimir el boton
        self.pushButton.clicked.connect(self.start_server)
        # agregamos el timer del servidor
        self.timer_server = 0
        # Para que la ventana tenga contadores
        self.timer = None
        # Lista con todas las serpientes del juego
        self.snakes = []
        self.snakes_len = len(self.snakes)
        self.current_id = 0 
        # Que no resalten las celdas al dar click
        self.tableWidget.setSelectionMode(QtGui.QTableWidget.NoSelection)
        # Método para expandir las celdas de la tabla de forma que estén bien
        # acomodadas
        self.expand_table_cells()
        # Pondremos items en toda la tabla para poder pintarla como queramos
        self.fill_table()

        # Conectamos que se cambie las columnas y filas de la tabla al método
        # update_table
        # Columnas
        self.spinBox_2.valueChanged.connect(self.update_table)
        # Filas
        self.spinBox_3.valueChanged.connect(self.update_table)

        # Conectamos que se cambie la velocidad de las serpientes al método
        # update_timer
        self.spinBox.valueChanged.connect(self.update_timer)

        # Conectamos el boton de iniciar juego al método de start_game
        self.pushButton_2.clicked.connect(self.change_game_state)
        # Enconderemos el boton de terminar juego ya que este sólo
        # aparece cuando se inicia el juego
        self.pushButton_3.hide()
        # Conectamos el boton de terminar juego al método de game_over
        self.pushButton_3.clicked.connect(self.game_over)
        
        # Mostramos la ventana
        self.show()

    def fill_table(self):
        """
            Se encarga de llenar la tabla con items en cada celda
        """
        for i in range(self.tableWidget.rowCount()):
            for j in range(self.tableWidget.columnCount()):
                self.tableWidget.setItem(i, j, QtGui.QTableWidgetItem())
                self.tableWidget.item(i,j).setBackground(
                    QtGui.QColor(255,255,255)
                )

    def expand_table_cells(self):
        """
            Se encarga de poner en el tamaño correcto las celdas    
        """
        self.tableWidget.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch
        )
        self.tableWidget.verticalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch
        )

    def update_table(self):
        """
            Actualiza la tabla si se incremente el numero de filas o de
            columnas
        """
        # Obtenemos los valores de los spinBox y actualizamos el número
        # de columnas y filas
        rows = self.spinBox_3.value()
        columns = self.spinBox_2.value()
        self.tableWidget.setRowCount(rows)
        self.tableWidget.setColumnCount(columns)
        self.fill_table()

    def update_timer(self):
        """
            Este método se encarga de cambiar la velocidad de la serpiente
            si es que la cambia el jugador en el spinBox
        """
        value = self.spinBox.value()
        self.timer.setInterval(value)

    def start_server(self):
        """
            Método encarfado de crear y empezar el servidor xmlrpc. Se le da una
            ip y un puerto. Además agregamos las funciones que tendran acceso
        """
        ip = self.lineEdit.text()
        port = self.spinBox_4.value()
        self.server = SimpleXMLRPCServer((ip, port))
        if port == 0:
            port = self.server.server_address[1]
        # Ponemos en la interfaz el puerto que tiene
        self.spinBox_4.setValue(port)
        # Ahora vamos a bloquear las configuraciones para que no sean
        # modificadas
        self.spinBox_4.setReadOnly(True)
        self.lineEdit.setReadOnly(True)
        self.pushButton.setEnabled(False)
        # Vamos a agregar las funciones del servidor
        # Están en español porque así los pide la práctica
        self.server.register_function(self.ping)
        self.server.register_function(self.yo_juego)
        self.server.register_function(self.cambia_direccion)
        self.server.register_function(self.estado_del_juego)
        # Intervalo del servidor
        self.server.timeout = 0
        self.timer_server = QtCore.QTimer(self)
        self.timer_server.timeout.connect(self.do_something_server)
        # Inicializamos el Timer con el intervalo del servidor
        self.timer_server.start(self.server.timeout)

    def do_something_server(self):
        """
            El servidor va ejecutando las peticiones que están en la cola.
        """
        self.server.handle_request()

    def change_game_state(self):
        """
            Inicializa o pausa el juego
        """
        if not self.game_started:
            # Mostramos el boton de terminar el juego
            self.pushButton_3.show()
            # Ponemos el boton de iniciar juego a pausar juego
            self.pushButton_2.setText('Pausar el Juego')

            # La pintamos en la tabla
            self.draw_snakes()
            # Le asignamos la velocidad
            self.timer = QtCore.QTimer(self)
            # Para cada timer se le conecta con el metodo move_snakes
            self.timer.timeout.connect(self.move_snakes)
            self.timer.start(200)
            # Le ponemos un EventFilter para escuchar a la
            # tabla
            self.tableWidget.installEventFilter(self)
            # Si no hay ningun error, ponemos que el juego ha sido
            # empezado
            self.game_started = True

        # Esto es para cuando el juego ha empezado y no está pausado
        elif self.game_started and not self.game_paused:
            # Paramos el timer
            self.timer.stop()
            self.game_paused = True
            self.pushButton_2.setText("Continuar juego")
        
        # Al final cuando el juego esta pausado
        elif self.game_started and self.game_paused:
            # Continuamos el timer
            self.timer.start()
            self.game_paused = False
            self.pushButton_2.setText("Pausar Juego")

    def game_over(self):
        """
            Termina el juego
        """
        # Paramos el timer
        self.timer.stop()
        # Borramos todas la serpientes
        self.snakes = []
        self.game_started = False
        self.game_paused = False
        # Volvemos a esconder el boton de terminar juego
        self.pushButton_3.hide()
        self.pushButton_2.setText('Iniciar Juego')
        # Volvemos a llenar la tabla
        self.fill_table()

    def draw_snakes(self):
        """
            Dibuja todas las serpientes en la tabla
        """
        for snake in self.snakes:
            for body_part in snake.body:
                self.tableWidget.item(body_part[0], body_part[1]).\
                    setBackground(QtGui.QColor(
                        snake.color['r'], snake.color['g'], snake.color['b']
                ))

    def move_snakes(self):
        """
            Hace el movimiento de las serpientes
        """
        for snake in self.snakes:
            if self.check_snake_has_crash(snake):
                # Quitamos la serpiente si es que ha chocado
                self.snakes.remove(snake)
                self.snakes_len -= 1
                if self.snakes_len == 0:
                    self.game_over()
                    return
                # Debemos de rellenar la tabla
                self.fill_table()

            # Poner de blanco el item donde estaba la cola de la serpiente
            self.tableWidget.item(
                snake.body[0][0],snake.body[0][1]
            ).setBackground(QtGui.QColor(255,255,255))

            aux = 1
            # Cada parte del cuerpo debe de moverse a donde está la
            # siguiente
            for body_part in snake.body[0:-1]:
                body_part[0] = snake.body[aux][0]
                body_part[1] = snake.body[aux][1]
                aux += 1

            # Vemos la dirección hacía donde se dirige la serpiente y
            # verificamos si la cabeza llega al borde de la tabla
            if snake.direction == 0:
                if snake.body[-1][0] != 0:
                    snake.body[-1][0] -= 1
                else:
                    snake.body[-1][0] = self.tableWidget.rowCount()-1
            elif snake.direction == 1:
                if snake.body[-1][1] < self.tableWidget.columnCount()-1:
                    snake.body[-1][1] += 1
                else:
                    snake.body[-1][1] = 0
            elif snake.direction == 2:
                if snake.body[-1][0] < self.tableWidget.rowCount()-1:
                    snake.body[-1][0] += 1
                else:
                    snake.body[-1][0] = 0
            elif snake.direction == 3:
                if snake.body[-1][1] != 0:
                    snake.body[-1][1] -= 1
                else:
                    snake.body[-1][1] = self.tableWidget.columnCount()-1
        # Al final de todo se vuelven a dibujar las serpientes
        self.draw_snakes()

    def check_snake_has_crash(self, snake):
        """
            Checa que la serpiente no haya chocado.
        """
        for current_snake in self.snakes:
            # Checamos 2 casos, si la serpiente actual es la serpiente
            # que estamos iterando ahora y si no. Esto es para que
            # una serpiente no choque con su misma cabeza ya que esto es
            # imposible
            if snake != current_snake:
                # Verificamos si chocaron ambas cabezas
                if snake.body[-1][0] == current_snake.body[-1][0] and (
                    snake.body[-1][1] == current_snake.body[-1][1]):
                    return True
            # Aquí ya verificamos todo el cuerpo excepto la cabeza
            for body_part in current_snake.body[0:-1]:
                if snake.body[-1][0] == body_part[0] and (
                    snake.body[-1][1] == body_part[1]):
                    return True
            return False

    def eventFilter(self, source, event):
        """
            Este método lo utilizaremos para los eventos cuando oprimamos
            las teclas y que la serpiente se mueva
        """
        if (event.type() == QtCore.QEvent.KeyPress) and (
            source is self.tableWidget):

            #Obtenemos que tecla es la que fue presionada
            key = event.key()
            # Checamos los casos cuando la tecla presionada es una de las
            # flechas
            if (key == QtCore.Qt.Key_Up and
                source is self.tableWidget):
                for snake in self.snakes:
                    if snake.direction != 2:
                        snake.direction = 0
            elif (key == QtCore.Qt.Key_Down and
                source is self.tableWidget):
                for snake in self.snakes:
                    if snake.direction != 0:
                        snake.direction = 2
            elif (key == QtCore.Qt.Key_Right and
                source is self.tableWidget):
                for snake in self.snakes:
                    if snake.direction != 3:
                        snake.direction = 1
            elif (key == QtCore.Qt.Key_Left and
                source is self.tableWidget):
                for snake in self.snakes:
                    if snake.direction != 1:
                        snake.direction = 3
        return QtGui.QMainWindow.eventFilter(self, source, event)

    def ping(self):
        """
            Utilizado por el cliente.
            Método que sólo regresa ¡Pong!
        """
        return '¡Pong!'

    def add_snake(self):
        """
            Agrega una serpiente en el juego
        """
        new_snake_id = str(self.current_id)
        self.current_id += 1
        new_snake = Snake(new_snake_id)
        correct_snake = False
        while not correct_snake:
            # Creamos las serpientes de forma horizontal
            head_y = randint(1, self.tableWidget.rowCount()/2)
            body_1_y = head_y + 1
            body_2_y = head_y + 2
            snake_x = randint(1, self.tableWidget.columnCount()-1)
            head, body_1, body_2 = (
                [head_y, snake_x], [body_1_y, snake_x],[body_2_y, snake_x]
            )
            # Verificamos que no choque con alguna otra serpiente
            for snake in self.snakes:
                if (head in snake.body or body_1 in snake.body
                    or body_2 in snake.body):
                    break
            else:
                correct_snake = True
            if correct_snake:
                new_snake.body = [body_2, body_1, head]
        self.snakes.append(new_snake)
        return new_snake


    def yo_juego(self):
        """
            Utilizado por el cliente.
            Registra una serpiente
        """
        new_snake = self.add_snake()
        snake_dict = {'id': new_snake.id, 'color': new_snake.color}
        return snake_dict

    def cambia_direccion(self, id, direction):
        """
            Utilizado por el cliente.
            Cambia la direccion de una serpiente
        """
        # Buscamos la serpiente con el id que queremos
        for snake in self.snakes:
            if snake.id == id:
                if direction == 0 and snake.direction != 2:
                    snake.direction = direction
                elif direction == 1 and snake.direction != 3:
                    snake.direction = direction
                elif direction == 2 and snake.direction != 0:
                    snake.direction = direction
                elif direction == 3 and snake.direction != 1:
                    snake.direction = direction
        # Esto es porque las funciones de servidor deben de regresar algo
        # siempre
        return True

    def get_snakes(self):
        """
            Nos trae la lista de serpientes dentro del juego
        """
        snakes = []
        for snake in self.snakes:
            snakes.append(snake.get_dict())
        return snakes

    def estado_del_juego(self):
        """
            Utilizado por el cliente.
            Regresa la información importante del juego
        """
        game_dict = {
            'espera': self.server.timeout,
            'tamx': self.tableWidget.columnCount(),
            'tamy': self.tableWidget.rowCount(),
            'viboras': self.get_snakes()
        }
        return game_dict

    def update_server_timeout(self):
        self.server.timeout = self.timer.value()
        self.timer_server.setInterval(self.time.value())


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv) 
    window = ServerWindow()
    sys.exit(app.exec_())
