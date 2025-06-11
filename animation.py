from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt

PACKET_COLORS = {
    "SYN": QColor("blue"),
    "SYN+ACK": QColor("green"),
    "ACK": QColor("cyan"),
    "DATA": QColor("orange"),
    "PACKET": QColor("orange"),
    "NACK": QColor("red"),
    "FIN": QColor("purple"),
    "ACK-FIN": QColor("magenta")
}

class PacketItem(QGraphicsEllipseItem):
    def __init__(self, packet_type, direction, y, text="", packet_id=None):
        super().__init__(0, 0, 30, 30)
        color = PACKET_COLORS.get(packet_type, QColor("gray"))
        self.setBrush(QBrush(Qt.GlobalColor.white))
        self.setPen(QPen(color, 2))
        self.text = QGraphicsTextItem(text)
        self.text.setDefaultTextColor(color)
        self.direction = direction
        self.y = y
        self.speed = 6
        self.packet_id = packet_id
        self.setPos(460 if direction == "client_to_server" else 0, y)
        self.text.setPos(self.x(), self.y)
        self.line = None

    def move(self):
        dx = -self.speed if self.direction == "client_to_server" else self.speed
        self.setPos(self.x() + dx, self.y)
        self.text.setPos(self.x(), self.y)

class AnimationManager(QObject):
    packet_arrived = pyqtSignal(str)

    def __init__(self, scene):
        super().__init__()
        self.scene = scene
        self.packets = []
        self.paused = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)
        self.animated_ids = set()

    def toggle_pause(self):
        self.paused = not self.paused

    def add_packet(self, packet_type, direction, text="", packet_id=None):
        if packet_id and any(p.packet_id == packet_id for p in self.packets):
            return
        if packet_id in self.animated_ids:
            return
        if packet_id:
            self.animated_ids.add(packet_id)

        y = 20 + len(self.packets) * 40 % 300
        packet = PacketItem(packet_type, direction, y, text, packet_id)
        self.scene.addItem(packet)
        self.scene.addItem(packet.text)

        start_x = 460 if direction == "client_to_server" else 0
        end_x = 0 if direction == "client_to_server" else 460
        line = QGraphicsLineItem(start_x, y, end_x, y)
        line.setPen(QPen(PACKET_COLORS.get(packet_type, Qt.GlobalColor.black), 1, Qt.PenStyle.DashLine))
        self.scene.addItem(line)
        packet.line = line

        self.packets.append(packet)

    def animate(self):
        if self.paused:
            return
        still_active = []
        for packet in self.packets:
            packet.move()
            if 0 <= packet.x() <= 500:
                still_active.append(packet)
            else:
                if packet.packet_id:
                    self.packet_arrived.emit(packet.packet_id)
                still_active.append(packet)
        self.packets = still_active

class PacketSyncManager:
    def __init__(self):
        from threading import Condition
        self.condition = Condition()
        self.arrived_packets = set()

    def wait_for(self, packet_id):
        with self.condition:
            while packet_id not in self.arrived_packets:
                self.condition.wait()
            self.arrived_packets.remove(packet_id)

    def notify_arrival(self, packet_id):
        with self.condition:
            self.arrived_packets.add(packet_id)
            self.condition.notify_all()
