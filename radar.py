import socket
from matplotlib import pyplot as plt
import matplotlib
import numpy as np

# --- Bandera de salida global, se activa al presionar 'q'
exit_requested = False

# --- Manejador de eventos de teclado
def on_key_press(event):
    global exit_requested
    if event.key == 'q':  # Si se presiona la tecla 'q', se solicita cerrar el programa
        print("Exit requested by user (pressed 'q').")
        exit_requested = True

# --- Selección del backend de matplotlib para uso con GUI (Tkinter)
matplotlib.use('TkAgg')

# --- Configuración de la interfaz gráfica del radar
fig = plt.figure(facecolor='black')  # Fondo negro para la figura
fig.canvas.manager.set_window_title("Ultrasonic Radar via TCP")  # Título de ventana

# Maximiza la ventana
mng = plt.get_current_fig_manager()
mng.window.attributes('-zoomed', True)

# Crear un gráfico polar con fondo tipo radar
ax = fig.add_subplot(1, 1, 1, polar=True, facecolor='#006b70')
ax.tick_params(axis='x', labelsize=20)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='both', which='major', colors='w', labelsize=20)

# Parámetros del radar
r_max = 100  # Rango máximo en cm
ax.set_ylim(0.0, r_max)  # Límite del radio
ax.set_xlim(0.0, np.pi)  # Limita ángulo de 0° a 180° (π radianes)
ax.set_position([-0.05, -0.05, 1.1, 1.05])  # Ajuste de posición para ocupar más ventana
ax.set_rticks(np.linspace(0, r_max, 11))  # Divisiones en radio
ax.set_thetagrids(np.linspace(0.0, 180, 19))  # Divisiones angulares cada 10 grados

# Inicializa marcador de puntos (los obstáculos)
pols, = ax.plot([], linestyle='', marker='o', markerfacecolor='r',
                markeredgecolor='w', markersize=12.0, markeredgewidth=1.0, alpha=0.8)

# Inicializa una línea de barrido central (opcional)
line1 = ax.plot([], color='w', linewidth=1.0)

# Preparar el canvas para actualizaciones rápidas
fig.canvas.draw()
axbackground = fig.canvas.copy_from_bbox(ax.bbox)

# --- Configuración del servidor TCP
HOST = "192.168.0.104"   # Dirección IP del host (PC local)
PORT = 1234              # Puerto que debe coincidir con el de la Pico

# Crear socket TCP
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permite reutilizar puerto
server_sock.bind((HOST, PORT))  # Asigna IP y puerto
server_sock.listen(1)  # Escucha conexiones entrantes

print(f"Waiting for Pico W on {HOST}:{PORT} ...")
conn, addr = server_sock.accept()  # Acepta conexión de la Pico
print(f"Connected by {addr}")

# --- Inicialización de estructuras de datos
angles = []      # Almacena ángulos en radianes
distances = []   # Almacena distancias en cm
lines = []       # Almacena líneas gráficas del radar

# --- Bucle principal de lectura de datos y visualización
buffer = ""
while not exit_requested:
    try:
        fig.canvas.restore_region(axbackground)  # Restaura fondo para evitar parpadeo

        # Recibir datos desde la Pico W
        data = conn.recv(1024)  # Recibe hasta 1024 bytes
        if not data:
            break  # Si no hay datos, cierra

        buffer += data.decode()  # Convierte bytes a string y acumula

        # Procesar cada línea de datos completa (\n del final)
        while '\n' in buffer:
            line, buffer = buffer.split('\n', 1)
            if "Angle" in line and "Distance" in line:
                try:
                    # Parsear ángulo y distancia
                    parts = line.strip().split(',')
                    angle = int(parts[0].split(':')[1].strip())
                    dist = float(parts[1].split(':')[1].replace("cm", "").strip())
                    print(f"The angle is: {angle} and distance is: {dist}")

                    # Convertir ángulo a radianes y guardar
                    angles.append(np.deg2rad(angle))
                    distances.append(dist)

                    # Limpiar cada 18 puntos (i.e., una vuelta de 0° a 180°)
                    if len(angles) > 19:
                        angles.clear()
                        distances.clear()
                        for l in lines:
                            l.remove()
                        lines.clear()
                        fig.canvas.restore_region(axbackground)

                    # Actualizar puntos en la gráfica
                    pols.set_data(angles, distances)

                    # Eliminar líneas anteriores
                    for l in lines:
                        l.remove()
                    lines.clear()

                    # Dibujar línea desde punto hasta el borde (efecto radar)
                    for i in range(len(angles)):
                        line = ax.plot([angles[i], angles[i]], [distances[i], r_max],
                                       color='lime', linewidth=5, alpha=0.5)
                        lines.extend(line)

                    # Dibujar línea de barrido vertical (90°)
                    line1[0].set_data([np.deg2rad(90), np.deg2rad(90)], [0, r_max])

                    # Redibujar elementos
                    ax.draw_artist(pols)
                    ax.draw_artist(line1[0])
                    for line in lines:
                        ax.draw_artist(line)

                    fig.canvas.blit(ax.bbox)  # Actualiza solo el área del gráfico
                    plt.pause(0.01)  # Pequeña pausa para procesar eventos

                except Exception as e:
                    print("Parse error:", e)  # En caso de error en el parsing

    except KeyboardInterrupt:
        break  # Permite salir con Ctrl+C

# --- Cierre de conexión y ventana
conn.close()
server_sock.close()
plt.close('all')
print("Closing terminal .")
