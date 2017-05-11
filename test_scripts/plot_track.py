import matplotlib.pyplot as plt
import numpy as np

logname = '2017-5-11_15:1:27.txt'
f_quad = open('quad_coords/'+logname, 'r')
f_car = open('car_coords/'+logname, 'r')

quad_coords = []
car_coords = []

for line in f_quad:
    data = line.strip().split('\t')
    quad_coords.append(data)

for line in f_car:
    data = line.strip().split('\t')
    car_coords.append(data)

q = np.asarray(quad_coords, dtype='double')
c = np.asarray(car_coords, dtype='double')

q_n = q[:,0]
q_e = q[:,1]
q_d = q[:,2]
q_y = q[:,3]

print(q_y)

q_u = np.sin(q_y)
q_v = np.cos(q_y)


c_n = c[:,0]
c_e = c[:,1]

plt.plot(q_e, q_n)
plt.quiver(q_e, q_n, q_u,q_v)
plt.scatter(c_e, c_n)
plt.axis('equal')
plt.xlabel('East (m)')
plt.ylabel('North (m)')

plt.grid(True)

plt.show()
