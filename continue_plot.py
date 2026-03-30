import matplotlib.pyplot as plt
from time import time
from timer import Timer
import numpy as np
import math

# Initialize the 3D plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
# distance from camera 1 to camera 2 in cm
D_CAM = 120


def get_data(path):
# Reads the object position from the specified file.
# Returns coordinates (x, y) or (None, None) if not found.
    with open(path, "r") as f:
        plot_data = f.read().strip()
        # Check if the file contains valid data
        if plot_data == "no ball found" or plot_data == "":
            return (None, None)
        else:
            # Parse the coordinates from the file
            x, y = plot_data.split()
            return (int(x), int(y))


# finds the angle of the ball from the camera within the plane of the camera
def find_alpha(x):
# Calculates the horizontal angle (alpha) of the object based on its x-coordinate.
# Uses geometry assuming a specific field of view.
    # cosine law
    if x is None:
        return
    # 453 pixels is 640/sqrt(2) pixels (related to FOV)
    # 90 degrees is camera field of view, 45 is from isoceles triangle assumption
    m = math.sqrt((x**2) + (453**2) -
                  (2 * x * 453 * math.cos(math.radians(45))))
    # sine law to find the angle
    alpha = math.asin((math.sin(math.radians(45)) * x) / m)
    return alpha


def get_x_y(alpha_1, alpha_2):
# Triangulates the (x, y) position of the object using angles from two cameras.
    # Calculate the third angle in the triangle
    far_angle = math.pi - alpha_1 - alpha_2
    # distance from c2 to ball in cm (Sine Law)
    d_2 = (D_CAM * math.sin(alpha_1)) / math.sin(far_angle)
    # sine law (again) to find cartesian coordinates
    y = (d_2 * math.sin(alpha_2)) / math.sin(math.radians(90))
    x = math.sqrt((d_2**2) - (y**2))
    return (x, y)


def display(x, y, z):
# Helper function to print coordinates (not actively used in loop).
    x = round(x, 2)
    y = round(y, 2)
    z = round(z, 2)
    print(f"({x}, {y}, {z})")


def predict_landing(xyz):
# Predicts the landing position of the object based on its trajectory.
# Uses SVD effectively for line fitting and physics for motion.
    # get x y and z values of the last four points
    points = [(x, y, z) for x, y, z, t in xyz[-8:]]
    delta_t = xyz[-1][3] - xyz[-4][3]  # Time difference
    data = np.array(points)
    
    # Calculate the mean of the data points
    datamean = data.mean(axis=0)
    # Do an SVD on the mean-centered data to find the direction of motion
    uu, dd, vv = np.linalg.svd(data - datamean)
    
    # Calculate the length of the segment covered by the points within Euclidean space
    length = round(math.sqrt(
        ((points[0][0] - points[-1][0])**2) + ((points[0][1] - points[-1][1])**2) + ((points[0][2] - points[-1][2])**2)))
    
    if length == 0:
        return (0, 0)

    # Generate points for the line of best fit (visualizing trajectory)
    linepts = vv[0] * np.mgrid[-7:7:2j][:, np.newaxis]
    linepts += datamean
    final_points = linepts.T.tolist()
    x1, x2 = final_points[0]
    y1, y2 = final_points[1]
    z1, z2 = final_points[2]

    # Calculate velocity in x, y, z directions
    vx = ((x2 - x1) / 100) / delta_t
    vy = ((y2 - y1) / 100) / delta_t
    vz = ((z2 - z1) / 100) / delta_t
    
    # Plot the predicted path segment in red
    ax.plot([x2, x2+(x2-x1)], [y2, y2+(y2-y1)], [z2, z2+(z2-z1)], c="r")
    # print(
    #     f"vx: {round(vx, 2)}m/s, vy: {round(vy, 2)}m/s, vz: {round(vz, 2)}m/s, delta_t: {round(delta_t, 2)}s")
    
    # Calculate time to impact (z=0) using kinematics
    times = np.roots([0.5 * -9.81, vz, height])
    t = max(times) # Take the positive time root
    
    # Return predicted landing x, y coordinates
    return (vx * t * 100), (vy * t * 100)


# Initialize trajectory list and timer
xyz = []
timer = Timer()

# Main processing loop
while True:
    timer.reset()
    # Read current object positions from files (updated by tracker)
    dim_1, height_1 = get_data("target_0")
    dim_2, height_2 = get_data("target_1")

    # Initialize buffer if empty
    if len(xyz) == 0:
        xyz.append((0, 0, 0, time()))
        continue

    # Skip if data closely matches previous data (static object or no update)
    if (xyz[-1][0] == dim_1 and xyz[-1][1] == dim_2 and xyz[-1][2] == 360 - height_1):
        continue
    
    # Use previous values if current ones are missing
    if not dim_1:
        dim_1 = xyz[-1][0]
    if not dim_2:
        dim_2 = xyz[-1][1]

    # Handle height data redundancy or missing data
    if not height_1 and height_2:
        height = height_2
    elif not height_2 and height_1:
        height = height_1
    elif not height_1 and not height_2:
        height = 360 - xyz[-1][2] # Default to previous height
    else:
        height = (height_1 + height_2) / 2 # Average height

    # Keep a limited history of points
    if len(xyz) > 30:
        xyz = xyz[1:]

    # Calculate angles (radians) for triangulation
    alpha_1 = find_alpha(dim_1)
    alpha_2 = (math.pi/2) - find_alpha(dim_2)

    # Triangulate position
    x, y = get_x_y(alpha_1, alpha_2)
    # display(x, y, 360 - height)

    # Add new point to trajectory
    xyz.append((x, y, 360 - height, time()))
    
    # Clear the previous plot to redraw
    ax.clear()

    # Draw the coordinate axes
    ax.plot([0, D_CAM], [0, 0], [0, 0], c="black")
    ax.plot([0, 0], [0, 360], [0, 0], c="black")
    ax.plot([0, 0], [0, 0], [0, D_CAM], c="black")

    if len(xyz) == 0:
        # no data visualization
        ax.scatter([], [], [], c="red", marker='o', s=100, cmap='gist_rainbow')
    else:
        # Unpack trajectory for plotting
        dim_1_list,  dim_2_list, height_list, time_list = zip(*xyz)
        # Scatter plot of the trajectory points, colored by time
        ax.scatter(dim_1_list,  dim_2_list, height_list, c=time_list,
                   marker='o', s=50, cmap='gist_rainbow_r')
        # Highlight current position
        ax.scatter(x, y, 360 - height, c="red", marker='o', s=160)

    # take the last four points and draw a best fit line through them to predict landing
    if len(xyz) > 4:
        pred_x, pred_y = predict_landing(xyz)
        print(f"Predicted landing: ({round(pred_x, 2)}, {round(pred_y, 2)})")
        
        # Write prediction to file for robot
        with open("prediction", "w") as f:
            f.write(f"{pred_x} {pred_y}")
            
        # Visualize predicted landing spot
        ax.scatter(pred_x, pred_y, 0, c="green", marker='o', s=160)
        ax.text2D(
            0.05, 0.95, f"Predicted landing: ({round(pred_x, 2)}, {round(pred_y, 2)})", transform=ax.transAxes)
    
    # Set plot labels
    ax.set_xlabel('Side camera')
    ax.set_ylabel('Laptop camera')
    ax.set_zlabel('Height')
    # set axis bounds
    ax.set_xlim3d(0, D_CAM)
    ax.set_ylim3d(0, 360)
    ax.set_zlim3d(0, D_CAM)
    
    # Small pause to update the plot
    plt.pause(0.015)
