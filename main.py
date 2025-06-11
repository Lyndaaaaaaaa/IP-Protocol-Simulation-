from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt
import sys
from client_thread import ClientThread
from animation import AnimationManager, PacketSyncManager

class TCPInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation TCP avec Animation")
        self.setStyleSheet("""
            QWidget {
                background-color: #eeeeee;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit, QTextEdit, QProgressBar {
                background-color: #f8f8f8;
                color: #2e2e2e;
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 4px;
            }
            QTextEdit {
                background-color: #f3e5f5;  /* light purple */
                color: #3c3c3c;
            }
            QPushButton {
                background-color: #a1887f;  /* mat brown */
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #9575cd;  /* mat purple */
            }
            QProgressBar {
                text-align: center;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: #81c784;  /* light green */
            }
            QGraphicsView {
                background-color: #dddddd;
                border: 1px solid #ccc;
            }
        """)


        self.setGeometry(200, 100, 1000, 700)

        layout = QVBoxLayout()
        form_layout = QHBoxLayout()

        self.entry_packets = QLineEdit()
        self.entry_packets.setPlaceholderText("Nombre de paquets")
        form_layout.addWidget(self.entry_packets)

        self.entry_rcvwindow = QLineEdit()
        self.entry_rcvwindow.setPlaceholderText("Taille de rcvwindow")
        form_layout.addWidget(self.entry_rcvwindow)

        self.entry_error_rate = QLineEdit()
        self.entry_error_rate.setPlaceholderText("Taux d'erreur (%)")
        form_layout.addWidget(self.entry_error_rate)

        self.btn_start = QPushButton("Démarrer")
        self.btn_start.clicked.connect(self.start_client)
        form_layout.addWidget(self.btn_start)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setCheckable(True)
        self.btn_pause.toggled.connect(self.toggle_simulation_pause)
        form_layout.addWidget(self.btn_pause)

        layout.addLayout(form_layout)

        label_layout = QHBoxLayout()
        label_layout.addWidget(QLabel("Serveur", alignment=Qt.AlignmentFlag.AlignLeft))
        label_layout.addWidget(QLabel("Client", alignment=Qt.AlignmentFlag.AlignRight))
        layout.addLayout(label_layout)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        logs = QHBoxLayout()
        self.server_log = QTextEdit()
        self.server_log.setReadOnly(True)
        self.client_log = QTextEdit()
        self.client_log.setReadOnly(True)
        logs.addWidget(self.server_log)
        logs.addWidget(self.client_log)
        layout.addLayout(logs)

        self.graphics_view = QGraphicsView()
        self.scene = QGraphicsScene(0, 0, 500, 350)
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)

        self.setLayout(layout)
        self.sync_manager = PacketSyncManager()
        self.anim_manager = AnimationManager(self.scene)
        self.anim_manager.packet_arrived.connect(self.sync_manager.notify_arrival)

    def toggle_simulation_pause(self, paused):
        if hasattr(self, 'thread'):
            if paused:
                self.thread.pause()
            else:
                self.thread.resume()
        self.anim_manager.toggle_pause()

    def start_client(self):
        try:
            n = int(self.entry_packets.text())
            w = int(self.entry_rcvwindow.text())
            error = int(self.entry_error_rate.text())
        except ValueError:
            self.client_log.append("[!] Valeurs invalides.")
            return

        self.client_log.clear()
        self.server_log.clear()
        self.progress.setValue(0)

        self.thread = ClientThread(n, w, self.sync_manager, error)
        self.thread.update_client.connect(self.client_log.append)
        self.thread.update_server.connect(self.server_log.append)
        self.thread.progress_signal.connect(self.progress.setValue)
        self.thread.finished_signal.connect(lambda: self.client_log.append("[OK] Terminé."))
        self.thread.animate_packet.connect(self.anim_manager.add_packet)
        self.thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TCPInterface()
    window.show()
    sys.exit(app.exec())
