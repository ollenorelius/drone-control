"""
Server running on the Raspberry Pi, handling all communications to the FC.

Opens a network interface on port 8002, listening for byte commands and
translates these to the FC.
This should start automatically from /etc/rc.local.

FC connection is through a local loopback to MAVProxy.py, also running on the
Pi. Handling it like this allows for a ground station connection to
Mission planner through WiFi at the same time which is convenient.
"""
import dronekit as dk
import socket
import RC_client_handler as RC_client
import threading
import RC_utils

inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8002))
inbound_socket.listen(0)

port = 'udp:localhost:14551'
print('Connecting to %s' % (port))
vehicle = dk.connect(port, wait_ready=True)

print('Connected!')
print('Battery voltage is %f V' % vehicle.battery.voltage)
threading.Thread(target=RC_utils.controller_priority, args=(vehicle,)).start()
while True:
    c, addr = inbound_socket.accept()
    args = (c, addr, vehicle)
    threading.Thread(target=RC_client.client_handler, args=args).start()
    print('RC client connected: %s:%s' % addr)
