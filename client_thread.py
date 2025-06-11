import socket
import threading
import time
import random
from PyQt6.QtCore import QThread, pyqtSignal

class ClientThread(QThread):
    update_client = pyqtSignal(str)
    update_server = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    animate_packet = pyqtSignal(str, str, str, str)

    def __init__(self, num_packets, rcvwindow, sync_manager, error_rate):
        super().__init__()
        self.num_packets = num_packets
        self.rcvwindow = rcvwindow
        self.sync_manager = sync_manager
        self.error_rate = error_rate
        self._paused = False
        self._pause_cond = threading.Condition()

    def pause(self):
        with self._pause_cond:
            self._paused = True

    def resume(self):
        with self._pause_cond:
            self._paused = False
            self._pause_cond.notify_all()

    def wait_or_pause(self):
        with self._pause_cond:
            while self._paused:
                self._pause_cond.wait()

    def send_packet_event(self, packet_type, direction, log_target, log_msg, animation_text="", packet_id=""):
        self.animate_packet.emit(packet_type, direction, animation_text, packet_id)
        self.sync_manager.wait_for(packet_id)
        if log_target == "client":
            self.update_client.emit(log_msg)
        elif log_target == "server":
            self.update_server.emit(log_msg)

    def run(self):
        HOST = "127.0.0.1"
        PORT = 12345
        try:
            self.update_client.emit("[...] Connexion au serveur...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((HOST, PORT))

            self.update_client.emit("--> Envoi SYN")
            self.animate_packet.emit("SYN", "client_to_server", "SEQ=0 ACK=0 LEN=0", "syn")
            self.sync_manager.wait_for("syn")

            sock.send(b"SYN")

            response = sock.recv(1024).decode()
            if response == "SYN+ACK":
                self.send_packet_event("SYN+ACK", "server_to_client", "client", "📡 Reçu SYN+ACK", "SEQ=0 ACK=1 LEN=0", "synack")
                self.update_server.emit("[SYN-ACK] Reçu SYN, envoi SYN+ACK")

            self.update_client.emit(f"[REQ] Demande {self.num_packets} paquets")
            sock.send(f"{self.num_packets} {self.rcvwindow}".encode())
            self.update_server.emit("📥 Attente de la demande de paquets...")

            received_packets = []
            ack_count = 0
            expected_index = 0
            buffer = ""

            while len(received_packets) < self.num_packets:
                buffer += sock.recv(1024).decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.startswith("PACKET"):
                        continue

                    packet_id = f"packet_{expected_index}"
                    index = int(line.split()[1])

                    if random.randint(1, 100) <= self.error_rate:
                        self.send_packet_event("NACK", "client_to_server", "client", f"[X] Erreur simulée sur {line}", f"SEQ={index}", f"nack_{index}")
                        sock.send(f"NACK {index}".encode())
                        self.update_server.emit("[!] Reçu NACK — retransmission demandée")
                        continue

                    self.send_packet_event("PACKET", "server_to_client", "server", f"✉️ Envoi {line}", line, packet_id)

                    if index == expected_index:
                        received_packets.append(line)
                        self.update_client.emit(f"[OK] Reçu {line}")
                        ack_count += 1
                        expected_index += 1
                        self.progress_signal.emit(int((len(received_packets) / self.num_packets) * 100))

                        if (ack_count == self.rcvwindow or expected_index == self.num_packets) and ack_count > 0:
                            ack_id = f"ack_{expected_index}"
                            self.animate_packet.emit("ACK", "client_to_server", f"ACK={expected_index}", ack_id)
                            self.sync_manager.wait_for(ack_id)
                            self.update_client.emit(f"[ACK] Envoi ACK pour {ack_count} paquets")
                            sock.send(b"ACK")
                            self.update_server.emit(f"[OK] Reçu ACK")
                            ack_count = 0

                    else:
                        nack_id = f"nack_{expected_index}"
                        self.send_packet_event("NACK", "client_to_server", "client", f"[!] Désordre détecté {line}", f"SEQ={expected_index}", nack_id)
                        sock.send(f"NACK {index}".encode())
                        self.update_server.emit("[ACK] Reçu NACK, retransmission demandée")

            self.send_packet_event("FIN", "client_to_server", "client", "[ACK] Envoi FIN", "", "fin")
            sock.send(b"FIN")
            self.update_server.emit("[x] Reçu FIN, envoi ACK-FIN")

            response = sock.recv(1024).decode()
            if response == "ACK-FIN":
                ack_id = f"ack_{expected_index}"
                self.animate_packet.emit("ACK", "client_to_server", f"ACK={expected_index}", ack_id)
                self.sync_manager.wait_for(ack_id)
                self.update_client.emit(f"[ACK] Envoi ACK final")
                sock.send(b"ACK")
                self.update_server.emit(f"[ACK-OK] Reçu ACK")

            self.finished_signal.emit()
            sock.close()

        except Exception as e:
            self.update_client.emit(f"[ERR] Erreur : {str(e)}")
            self.finished_signal.emit()
