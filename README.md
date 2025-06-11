# IP-Protocol-Simulation
# Overview
This project simulates a basic end-to-end TCP protocol exchange between a client and a server. It aims to reproduce the essential stages of a TCP connection: establishment, data transfer, and termination, in a simplified and controlled environment.

# Connection Establishment
The simulation begins with the three-way handshake:

The client initiates the connection by sending a SYN packet and starts a timeout timer.

The server replies with a SYN + ACK packet, acknowledging the connection request.

# Data Transfer
Once the connection is established:

The client requests a variable number of packets (N) and informs the server of its receiving window size (rcvwindow).

The server compares N and rcvwindow, and sends packets accordingly—either in one batch or in multiple rounds.

The client acknowledges received packets. In case of negative acknowledgment (NAK), the server retransmits the corresponding packet(s).

# Connection Termination
To close the connection:

The client sends a FIN packet.

The server acknowledges it with a "closing" response.

The client acknowledges the closing packet and initiates a 30-second timeout before fully closing the connection.


# Technologies Used
Programming Language: Python (you can replace this if another language was used)

Socket Programming

Timeout & Buffer Management
