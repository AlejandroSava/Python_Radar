from matplotlib import pyplot as plt
import matplotlib
from pyparsing import alphas  # (not used — can be removed if unused)

matplotlib.use('TkAgg')  # Use the TkAgg backend for GUI rendering
import numpy as np

# Create a figure with black background
fig = plt.figure(facecolor='black')

# Hide the default toolbar
fig.canvas.toolbar.pack_forget()

# Set the window title
fig.canvas.manager.set_window_title("Ultrasonic Radar using FreeRTOS and Pico W")

# Get the figure manager and maximize the window (Linux-specific way)
mng = plt.get_current_fig_manager()
mng.window.attributes('-zoomed', True)  # For Linux

# Create a polar subplot with custom background color
ax = fig.add_subplot(1, 1, 1, polar=True, facecolor='#006b70')

# Customize tick label sizes and colors
ax.tick_params(axis='x', labelsize=20)  # Angular ticks
ax.tick_params(axis='y', labelsize=20)  # Radial ticks
ax.tick_params(axis='both', which='major', colors='w', labelsize=20)

# Define radar range and angle limits
r_max = 100
ax.set_ylim(0.0, r_max)
ax.set_xlim(0.0, np.pi)

# Adjust the subplot size within the figure
ax.set_position([-0.05, -0.05, 1.1, 1.05])

# Set radial ticks and angular grid lines
ax.set_rticks(np.linspace(0.0, r_max, 5))
ax.set_thetagrids(np.linspace(0.0, 180, 12))

# Define angles from 0 to 180 degrees (in radians)
angles = np.arange(0, 181, 1)
theta = angles * (np.pi / 180)

# Initialize plot for red dots (detected points)
pols, = ax.plot([], linestyle='', marker='o', markerfacecolor='r',
                markeredgecolor='w', markersize=8.0, markeredgewidth=1.0,
                alpha=0.5)
# Optional sweep line
line1 = ax.plot([], color='w', linewidth=3.0)

# Initial canvas draw
fig.canvas.draw()

# Distance array placeholder (initial values)
dists = np.ones((len(angles), ))

# Copy the background for efficient blitting
axbackground = fig.canvas.copy_from_bbox(ax.bbox)

# Index to progressively draw points
index = 0

# Store lines from dots to r_max
lines = []

# Main loop
while True:
    try:
        # Restore clean background
        fig.canvas.restore_region(axbackground)

        # Simulate data (use real input here if needed)
        simulated_dists = 40 + 30 * np.sin(2 * theta + index * 0.05)
        dists = simulated_dists

        # Plot progressively more dots
        if index < len(theta):
            pols.set_data(theta[:index], dists[:index])
            index += 1

        # Optional static sweep line (can animate if desired)
        line1[0].set_data([theta[90], theta[90]], [0, r_max])

        # Remove old radial lines
        for line in lines:
            line.remove()
        lines.clear()

        # Draw a line from each point to the edge (r_max)
        for i in range(index):
            line = ax.plot([theta[i], theta[i]], [dists[i], r_max],
                           color='lime', linewidth=1.5, alpha=0.5)
            lines.extend(line)

        # Redraw updated elements
        ax.draw_artist(pols)
        ax.draw_artist(line1[0])
        for line in lines:
            ax.draw_artist(line)

        # Refresh the canvas (only the changed area)
        fig.canvas.blit(ax.bbox)

        # Control speed of updates
        plt.pause(0.01)

    except KeyboardInterrupt:
        plt.close('all')
        print("Keyboard Interrupt")
        break

exit()