import dronekit as dk
import time
import socket
import RC_client
import threading
import RC_utils

inbound_socket = socket.socket()
inbound_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
inbound_socket.bind(('0.0.0.0', 8002))
inbound_socket.listen(0)

port = 'udp:localhost:14551'
print('Connecting to %s'%(port))
vehicle = dk.connect(port, wait_ready=True)

print('Connected!')
print('Battery voltage is %f V'%vehicle.battery.voltage)
threading.Thread(target=RC_utils.controller_priority, args=(vehicle,)).start()
while True:
    c, addr = inbound_socket.accept()
    args = (c, addr, vehicle)
    threading.Thread(target=RC_client.client_handler,args=args).start()
    print('RC client connected: %s:%s'%addr)
