import math

def WristFind(arm_x, arm_y, arm_z, wrist_orientation='up'):

    # if wrist is up: positive value
    # if wrist is down: negative value
    if wrist_orientation == 'up': wrist_length = 32
    if wrist_orientation == 'down': wrist_length = -32
    #d_flat = (arm_x ** 2 + arm_y ** 2) ** 0.5

    p1 = (arm_z ** 2 - 2 * wrist_length * arm_z + arm_y ** 2 + arm_x ** 2 + wrist_length ** 2) ** 0.5
    p1 = - math.acos(p1 / 500)

    p2 = (((arm_y ** 2 + arm_x ** 2) ** 0.5) / (arm_z - wrist_length))
    p2 = - math.atan(p2)

    total = p1 + p2 + math.pi
    angle = math.degrees(total)
    if angle > 180: angle = angle - 180
    if angle < -180: angle = angle + 180
    # for wrist down, we are interested in the complementary angle
    if wrist_length < 0: angle = 180 - angle

    return angle


if __name__ == "__main__":
    r = WristFind(200, 200, 300, wrist_orientation='down')
    print(r)
