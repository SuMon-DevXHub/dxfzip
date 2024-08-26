import ezdxf
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
import math


def Segmentify(polyline, segmentl=10):
    vertices = polyline.get_points()
    is_closed = polyline.closed
    if is_closed:
        vertices.append(vertices[0])
    allp = []
    for i in range(len(vertices) - 1):
        start = vertices[i][:2]
        end = vertices[i + 1][:2]
        bulge = vertices[i][4] if len(vertices[i]) >= 5 else 0
        allp.append(start)
        if bulge != 0:  # Line
            center, start_angle, end_angle, radius = ezdxf.math.bulge_to_arc(
                start, end, bulge
            )
            total_angle = end_angle - start_angle
            if total_angle <= 0:
                total_angle += 2 * math.pi
            num_segments = int(total_angle * radius / segmentl)
            segment_angle = total_angle / num_segments if num_segments>0 else total_angle
            arc_points = [
                (
                    center[0] + radius * math.cos(start_angle + i * segment_angle),
                    center[1] + radius * math.sin(start_angle + i * segment_angle),
                    i
                )
                for i in range(num_segments + 1)
            ]
            prec=1000000
            if int(arc_points[-1][0]*prec) == int(start[0]*prec) and int(arc_points[-1][1]*prec) == int(start[1]*prec) :
                arc_points.reverse()
            for j in range(len(arc_points) - 1):
                allp.append(arc_points[j])
    allp.append(end)
    return allp


# Load the DXF file
file_path = "denemeler2.dxf"
doc = ezdxf.readfile(file_path)
msp = doc.modelspace()
polyline = msp.query("LWPOLYLINE")[0]

# Plot the polyline
allp = Segmentify(polyline, segmentl=50)

fig, ax = plt.subplots()
# Assume there's only one polyline in the drawing

for p in range(len(allp) - 1):
    print(allp[p])
    ax.plot([allp[p][0], allp[p + 1][0]], [allp[p][1], allp[p + 1][1]], color="red")
# Now plot all vertices points as dots
ax.scatter([x[0] for x in allp], [x[1] for x in allp], color="green", s=10, zorder=5)
ax.set_aspect("equal", adjustable="datalim")
ax.autoscale(enable=True)
plt.xlabel("X")
plt.ylabel("Y")
plt.title("DXF Polyline with Segmented Arcs")
plt.grid(True)
plt.show()
