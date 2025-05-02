import socket
from matplotlib import pyplot as plt
import matplotlib
import numpy as np

# --- Global flag for exiting the loop when 'q' is pressed
exit_requested = False

# --- Event handler for key press
def on_key_press(event):
    global exit_requested
    if event.key == 'q':
        print("Exit requested by user (pressed 'q').")
        exit_requested = True

# --- Set matplotlib to use a GUI backend
matplotlib.use('TkAgg')

# --- Radar GUI setup ---
fig = plt.figure(facecolor='black')  # Set background color
fig.canvas.manager.set_window_title("Ultrasonic Radar via TCP")  # Window title

# Maximize the window (Linux specific)
mng = plt.get_current_fig_manager()
mng.window.attributes('-zoomed', True)

# Create a polar plot for radar display
ax = fig.add_subplot(1, 1, 1, polar=True, facecolor='#006b70')
ax.tick_params(axis='x', labelsize=20)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='both', which='major', colors='w', labelsize=20)

# Radar range configuration
r_max = 100  # Max distance in cm
ax.set_ylim(0.0, r_max)           # Set radial limit
ax.set_xlim(0.0, np.pi)           # Limit angular range to 180° (π radians)
ax.set_position([-0.05, -0.05, 1.1, 1.05])  # Make radar occupy more screen
ax.set_rticks(np.linspace(0, r_max, 11))   # Radial ticks
ax.set_thetagrids(np.linspace(0.0, 180, 19))  # Angular ticks (every 10°)

# Create marker for detected points (red dots)
pols, = ax.plot([], linestyle='', marker='o', markerfacecolor='r',
                markeredgecolor='w', markersize=12.0, markeredgewidth=1.0, alpha=0.8)

# Create sweep line (optional)
line1 = ax.plot([], color='w', linewidth=1.0)

# Prepare canvas for optimized drawing
fig.canvas.draw()
axbackground = fig.canvas.copy_from_bbox(ax.bbox)

# --- TCP Server Setup ---
HOST = "192.168.0.104"  # PC's IP address (should match SERVER_IP in Pico code)
PORT = 1234             # Port to match Pico's SERVER_PORT

# Create TCP socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of the port
server_sock.bind((HOST, PORT))
server_sock.listen(1)

print(f"Waiting for Pico W on {HOST}:{PORT} ...")
conn, addr = server_sock.accept()  # Accept connection from Pico
print(f"Connected by {addr}")

# --- Data buffers ---
angles = []      # Store angles in radians
distances = []   # Store distances in cm
lines = []       # Store references to plotted lines

# --- Main loop for receiving and drawing data ---
buffer = ""
while not exit_requested:
    try:
        fig.canvas.restore_region(axbackground)  # Restore background (avoids flickering)

        # Receive TCP data (might be multiple or partial messages)
        data = conn.recv(1024)
        if not data:
            break  # End connection if no data

        buffer += data.decode()  # Convert bytes to string and accumulate

        # Process complete lines (messages end with \n)
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if "Angle" in line and "Distance" in line:
                try:
                    # Parse angle and distance from message
                    parts = line.strip().split(',')
                    angle = int(parts[0].split(':')[1].strip())
                    dist = float(parts[1].split(':')[1].replace("cm", "").strip())
                    print(f"The angle is: {angle} and distance is: {dist}")

                    # Convert angle to radians and store
                    angles.append(np.deg2rad(angle))
                    distances.append(dist)

                    # Clear data after a full sweep (18+ points)
                    if len(angles) > 19:
                        angles.clear()
                        distances.clear()
                        for l in lines:
                            l.remove()
                        lines.clear()
                        fig.canvas.restore_region(axbackground)

                    # Update radar dots
                    pols.set_data(angles, distances)

                    # Remove previous lines
                    for l in lines:
                        l.remove()
                    lines.clear()

                    # Draw green lines from each point to outer ring
                    for i in range(len(angles)):
                        line = ax.plot([angles[i], angles[i]], [distances[i], r_max],
                                       color='lime', linewidth=5, alpha=0.5)
                        lines.extend(line)

                    # Draw sweep line at 90° (optional visual effect)
                    line1[0].set_data([np.deg2rad(90), np.deg2rad(90)], [0, r_max])

                    # Redraw updated elements
                    ax.draw_artist(pols)
                    ax.draw_artist(line1[0])
                    for line in lines:
                        ax.draw_artist(line)

                    fig.canvas.blit(ax.bbox)
                    plt.pause(0.01)

                except Exception as e:
                    print("Parse error:", e)

    except KeyboardInterrupt:
        break  # Allow graceful shutdown via Ctrl+C

# --- Clean up on exit ---
conn.close()
server_sock.close()
plt.close('all')
print("Radar closed successfully.")
