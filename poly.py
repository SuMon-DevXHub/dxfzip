import ezdxf

def list_polyline_coordinates_in_blocks(dxf_file):
    # Load the DXF file
    doc = ezdxf.readfile(dxf_file)
    modelspace = doc.modelspace()

    # Iterate through all blocks
    for block in doc.blocks:
        # print(f"Scanning Block: {block.name}")
        # Iterate through all entities in the block
        for entity in block:
            # Check if the entity is a polyline
            if "SLAB" in block.name:
                if entity.dxftype() == 'LWPOLYLINE' or entity.dxftype() == 'POLYLINE':
                    color = entity.dxf.color  # Getting the color of the polyline
                    print(f"  Found a Polyline in {block.name}, Color: {color}")

                    # Print the coordinates of the polyline
                    for point in entity:
                        print(f"    {round(point[0],3),round(point[1],3)}")
                    print()

# Example usage
dxf_file_path = 'path_to_your_dxf_file.dxf'
list_polyline_coordinates_in_blocks("dxf_files\PK10kat.dxf")