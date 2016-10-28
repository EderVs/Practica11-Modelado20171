import sys
from PyQt4 import QtGui, QtCore, uic
from xmlrpc.client import ServerProxy


class MyWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        uic.loadUi('cliente.ui', self)
        self.expand_table_cells()
        # Que no resalten las celdas al dar click
        self.tableWidget.setSelectionMode(QtGui.QTableWidget.NoSelection)
        # Id del usuario para reconocer en el servidor
        self.user_id = 0
        self.pushButton.clicked.connect(self.ping)
        self.pushButton_2.clicked.connect(self.get_in_game)
        self.snake_direction = 0
        self.server = None
        self.server_interval = 0
        self.user_in_game = False
        self.timer = QtCore.QTimer(self)
        # Conectando el QTimer con las funciones que se tienen que esar
        # constantemente ejecutando.
        self.timer.timeout.connect(self.adjust_table_like_server) 
        self.timer.timeout.connect(self.start_game)
        self.timer.timeout.connect(self.update_interval)
        self.timer.start(self.server_interval)
        self.show()

    def expand_table_cells(self):
        self.tableWidget.horizontalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch
        )
        self.tableWidget.verticalHeader().setResizeMode(
            QtGui.QHeaderView.Stretch
        )

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

    def eventFilter(self, source, event):

        if (event.type() == QtCore.QEvent.KeyPress and
            source is self.tableWidget): 
                key = event.key() 
                if (key == QtCore.Qt.Key_Up and
                    source is self.tableWidget):
                    if self.snake_direction != 2:
                        self.snake_direction = 0
                elif (key == QtCore.Qt.Key_Down and
                    source is self.tableWidget):
                    if self.snake_direction != 0:
                        self.snake_direction = 2
                elif (key == QtCore.Qt.Key_Right and
                    source is self.tableWidget):
                    if self.snake_direction != 3:
                        self.snake_direction = 1
                elif (key == QtCore.Qt.Key_Left and
                    source is self.tableWidget):
                    if self.snake_direction != 1:
                        self.snake_direction = 3
                # Notificamos al servidor del cambio de direccion
                self.server.cambia_direccion(
                    self.user_id, self.snake_direction
                )
        return QtGui.QMainWindow.eventFilter(self, source, event)

    def adjust_table_like_server(self):
        """
            Hace que la tabla sea igual que la del servidor
        """
        # Verificamos que el usuario este en el juego
        if self.user_in_game:
            game = self.server.estado_del_juego()
            self.tableWidget.setRowCount(game["tamy"])
            self.tableWidget.setColumnCount(game["tamx"])
            self.fill_table()

    def start_game(self):
        """
            Empieza y va actualizando el juego
        """
        if self.user_in_game:
            self.fill_table()
            self.tableWidget.installEventFilter(self)
            game_state = self.server.estado_del_juego()
            snakes = game_state['viboras']
            for snake in snakes:
                snake_body = snake['camino']
                colors = snake['color']
                self.draw_snake(snake_body, colors)
    
    def draw_snake(self, snake_body, colors):
        for body_part in snake_body:
            self.tableWidget.item(body_part[0], body_part[1]).\
                setBackground(QtGui.QColor(
                    colors['r'], colors['g'], colors['b'])
                )

    def update_interval(self):
        if self.user_in_game:
            game_state = self.server.estado_del_juego()
            interval = game_state['espera']
            if self.server_interval != interval:
                self.server_interval = interval
                self.timer.setInterval(self.server_interval)

    def create_server(self):
        # Obtenemos los valores de la pantalla
        self.url = self.lineEdit_3.text()
        self.port = self.spinBox.value()
        self.server_url =  'http://' + self.url + ':' + str(self.port)
        self.server = ServerProxy(self.server_url)

    def ping(self):
        self.pushButton.setText('Pinging...')
        # Utilizamos un Try por si no se crea el servidor
        try:
            self.create_server()
            pong = self.server.ping()
            self.pushButton.setText(pong)
        except:
            self.pushButton.setText('No Pong :(')

    def get_in_game(self):
        # Usamos un try por si no se puede crear el servidor
        try:
            self.create_server()
            my_information = self.server.yo_juego()
            self.user_id = my_information['id']
            self.lineEdit.setText(self.user_id)
            color = my_information['color']
            red = color['r']
            blue = color['b']
            green = color['g']
            self.lineEdit_2.setStyleSheet(
                'QLineEdit {background-color: rgb('+
                str(red)+','+ str(green) + ',' + str(blue)+');}'
            )
            self.user_in_game = True
        except:
            self.lineEdit.setText('Error de Conexion')


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())
