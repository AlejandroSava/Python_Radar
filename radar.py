import socket
from matplotlib import pyplot as plt
import matplotlib
import numpy as np


exit_requested = False  # Global flag
def on_key_press(event):
    global exit_requested
    if event.key == 'q':
        print("Exit requested by user (pressed 'q').")
        exit_requested = True

# Use GUI backend
matplotlib.use('TkAgg')

# ---- Radar GUI Setup ----
fig = plt.figure(facecolor='black')
fig.canvas.manager.set_window_title("Ultrasonic Radar via TCP")
mng = plt.get_current_fig_manager()
mng.window.attributes('-zoomed', True)

ax = fig.add_subplot(1, 1, 1, polar=True, facecolor='#006b70')
ax.tick_params(axis='x', labelsize=20)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='both', which='major', colors='w', labelsize=20)

r_max = 100
ax.set_ylim(0.0, r_max)
ax.set_xlim(0.0, np.pi)
ax.set_position([-0.05, -0.05, 1.1, 1.05])
ax.set_rticks(np.linspace(0, r_max, 11))
ax.set_thetagrids(np.linspace(0.0, 180, 19))

pols, = ax.plot([], linestyle='', marker='o', markerfacecolor='r',
                markeredgecolor='w', markersize=12.0, markeredgewidth=1.0, alpha=0.8)
line1 = ax.plot([], color='w', linewidth=1.0)

# Prepare canvas
fig.canvas.draw()
axbackground = fig.canvas.copy_from_bbox(ax.bbox)

# ---- TCP Setup ----
HOST = "192.168.0.104"   # IP address of the computer (Pico W connects to this)
PORT = 1234              # Must match Pico's SERVER_PORT

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_sock.bind((HOST, PORT))
server_sock.listen(1)

print(f"Waiting for Pico W on {HOST}:{PORT} ...")
conn, addr = server_sock.accept()
print(f"Connected by {addr}")

# ---- Data Storage ----
angles = []
distances = []
lines = []

# ---- Read + Draw Loop ----
buffer = ""
while not exit_requested:
    try:
        fig.canvas.restore_region(axbackground)

        # Receive data (TCP is stream-based, we buffer by \n)
        data = conn.recv(1024)
        if not data:
            break

        buffer += data.decode()
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if "Angle" in line and "Distance" in line:
                try:
                    parts = line.strip().split(',')
                    angle = int(parts[0].split(':')[1].strip())
                    dist = float(parts[1].split(':')[1].replace("cm", "").strip())
                    print(f"The angle is: {angle} and distance is: {dist}")

                    angles.append(np.deg2rad(angle))
                    distances.append(dist)

                    # Clear data every 18 points (i.e., full sweep)
                    if len(angles) > 18:
                        angles.clear()
                        distances.clear()
                        for l in lines:
                            l.remove()
                        lines.clear()
                        fig.canvas.restore_region(axbackground)

                    # Update dots
                    pols.set_data(angles, distances)

                    for l in lines:
                        l.remove()
                    lines.clear()

                    # Draw lines from each point to outer ring
                    for i in range(len(angles)):
                        line = ax.plot([angles[i], angles[i]], [distances[i], r_max],
                                       color='lime', linewidth=5, alpha=0.5)
                        lines.extend(line)

                    # Optional sweep line
                    line1[0].set_data([np.deg2rad(90), np.deg2rad(90)], [0, r_max])

                    ax.draw_artist(pols)
                    ax.draw_artist(line1[0])
                    for line in lines:
                        ax.draw_artist(line)

                    fig.canvas.blit(ax.bbox)
                    plt.pause(0.01)

                except Exception as e:
                    print("Parse error:", e)

    except KeyboardInterrupt:
        break

# Cleanup
conn.close()
server_sock.close()
plt.close('all')
print("Radar cerrado correctamente.")