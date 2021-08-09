import time
# all in mm
X = -500
Y = 100
Z = 0

start = time.time()

reach = 500
track_range = 1200
resolution = 10


if X > 0:
    start_x = -track_range
    x_step = resolution
else:
    start_x = track_range
    x_step = -resolution

S2 = 100000
while True:
    S1 = ((X - start_x)**2 + Y**2) ** 0.5
    S2 = (S1**2 + Z**2) ** 0.5
    print(S2)
    if S2 <= reach: break
    start_x = start_x + x_step

end = time.time()
print(end - start)
print(start_x, X, Y, Z)