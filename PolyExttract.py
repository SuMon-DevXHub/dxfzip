import ezdxf
import json
import math

def point_on_arc(start, end, bulge, segments=10):
    """ Calculate points on an arc segment defined by start, end, and bulge. """
    angle = 4 * math.atan(bulge)
    distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
    radius = distance / (2 * math.sin(angle / 2))
    center_angle = math.atan2(end[1] - start[1], end[0] - start[0]) + (math.pi / 2 - angle / 2) * (-1 if bulge < 0 else 1)
    center = (start[0] + math.cos(center_angle) * radius, start[1] + math.sin(center_angle) * radius)

    points = [start]
    for i in range(1, segments):
        theta = center_angle + angle * (i / segments) * (-1 if bulge < 0 else 1)
        points.append((center[0] + math.cos(theta) * radius, center[1] + math.sin(theta) * radius))
    points.append(end)
    return [{'x': p[0], 'y': p[1]} for p in points]

def extract_polylines(msp):
    polylines = []
    for entity in msp.query('LWPOLYLINE POLYLINE'):
        points = []
        is_lwpolyline = entity.dxftype() == 'LWPOLYLINE'

        vertices = entity if is_lwpolyline else list(entity.vertices())

        for i in range(len(vertices) - 1):
            if is_lwpolyline:
                start = vertices[i][:2]
                end = vertices[i + 1][:2]
                bulge = vertices[i][3] if len(vertices[i]) > 2 else 0
            else:
                start = vertices[i].dxf.location[:2]
                end = vertices[i + 1].dxf.location[:2]
                bulge = vertices[i].dxf.bulge if hasattr(vertices[i].dxf, 'bulge') else 0

            if bulge == 0:
                points.append({'x': round(start[0],3), 'y': round(start[1],3)})
                points.append({'x': round(start[0],3), 'y': round(start[1],3)})
            else:
                arc_points = point_on_arc(start, end, bulge)
                points.extend(arc_points)

        # Add the last point if not closed
        if not entity.is_closed:
            last_point = (vertices[-1][:2] if is_lwpolyline else vertices[-1].dxf.location[:2])
            points.append({'x': round(last_point[0],3), 'y': round(last_point[1],3)})
            points.append({'x': round(last_point[0],3), 'y': round(last_point[1],3)})

        polylines.append({'points': points})
    return polylines

def parse_dxf_to_json(file_path, output_file):
    doc = ezdxf.readfile(file_path)
    msp = doc.modelspace()
    polylines = extract_polylines(msp)
    with open(output_file, 'w') as f:
        json.dump({'polylines': polylines}, f, indent=4)


