import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 12345

def handle_client(client_socket):
    try:
        syn_msg = client_socket.recv(1024).decode()
        if syn_msg == "SYN":
            print("[SERVER] Reçu SYN, envoi SYN+ACK")
            client_socket.send("SYN+ACK".encode())

        request = client_socket.recv(1024).decode()
        num_packets, rcvwindow = map(int, request.split())
        print(f"[SERVER] Le client veut {num_packets} paquets, rcvwindow = {rcvwindow}")

        i = 0
        sent_packets = {}

        while i < num_packets:
            print(f"[SERVER] ➤ Envoi d'une fenêtre de paquets à partir de {i}")
            for j in range(rcvwindow):
                idx = i + j
                if idx >= num_packets:
                    break
                packet = f"PACKET {idx}\n"
                client_socket.send(packet.encode())
                sent_packets[idx] = packet
                print(f"[SERVER] Envoi: {packet.strip()}")
                time.sleep(0.01)

            try:
                ack = client_socket.recv(1024).decode().strip()
            except socket.timeout:
                print("[SERVER] [WAIT] Timeout d'attente ACK/NACK")
                continue

            if ack == "ACK":
                print(f"[SERVER] Reçu ACK pour {rcvwindow} paquets")
                i += rcvwindow
            elif ack.startswith("NACK"):
                try:
                    nack_index = int(ack.split()[1])
                    if nack_index in sent_packets:
                        print(f"[SERVER] [RESEND] Retransmission: PACKET {nack_index}")
                        client_socket.send(sent_packets[nack_index].encode())
                        time.sleep(0.01)
                except:
                    print("[SERVER] Format NACK invalide")
            else:
                print(f"[SERVER] Réponse inattendue: {ack} — ignorée")

        fin_request = client_socket.recv(1024).decode()
        if fin_request == "FIN":
            print("[SERVER] Reçu FIN, envoi ACK-FIN")
            client_socket.send("ACK-FIN".encode())
            fin_ack = client_socket.recv(1024).decode()
            if fin_ack == "ACK":
                print("[SERVER] [OK] Connexion fermée proprement.")

    except Exception as e:
        print(f"[SERVER] Erreur: {e}")
    finally:
        client_socket.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen(5)
print(f"[SERVER] Écoute sur {HOST}:{PORT}")

while True:
    client_sock, addr = server.accept()
    print(f"[SERVER] Connexion acceptée de {addr}")
    thread = threading.Thread(target=handle_client, args=(client_sock,))
    thread.start()
