from .objects_3D import Surface, Spheres, Contours

from PyReconstruct.modules.datatypes import Series

def generateVolumes(series : Series, obj_names : list):
    """Generate the volume items for a set of objects.
    
        Params:
            series (Series): the series containing the object data
            obj_names (list): the list of objects to reconstruct
            alpha (float): the transparency for the 3D scene
        Returns:
            (list): the 3D item objects
            (tuple): xmin, xmax, ymin, ymax, zmin, zmax
    """
    # create the 3D objects
    obj_data = {}
    for obj_name in obj_names:
        mode, opacity = tuple(series.getAttr(obj_name, "3D_modes"))
        if mode == "surface":
            obj_data[obj_name] = (Surface(obj_name), opacity)
        elif mode == "spheres":
            obj_data[obj_name] = (Spheres(obj_name), opacity)
        elif mode == "contours":
            obj_data[obj_name] = (Contours(obj_name), opacity)

    # iterate through all sections and gather points (and colors)
    mags = []
    thicknesses = []

    for snum, section in series.enumerateSections(show_progress=False):
        # ASSUME SOMEWHAT UNIFORM THICKNESS
        thicknesses.append(section.thickness)
        mags.append(section.mag)
        tform = section.tform

        for obj_name in obj_names:
            if obj_name in section.contours:
                for trace in section.contours[obj_name]:
                    # collect all points if generating a full surface
                    obj_data[obj_name][0].addTrace(trace, snum, tform)

    # iterate through all objects and create 3D meshes
    mesh_data_list = []
    extremes = []
    avg_mag = sum(mags) / len(mags)
    avg_thickness = sum(thicknesses) / len(thicknesses)

    for obj_name, (obj_3D, opacity) in obj_data.items():
        extremes = addToExtremes(extremes, obj_3D.extremes)

        if type(obj_3D) is Surface:
            mesh_data_list.append(obj_3D.generate3D(
                avg_mag,
                avg_thickness,
                opacity,
                series.getOption("3D_smoothing")
            ))
        elif type(obj_3D) is Spheres:
            mesh_data_list.append(obj_3D.generate3D(
                avg_thickness,
                opacity
            ))
        elif type(obj_3D) is Contours:
            mesh_data_list.append(obj_3D.generate3D(
                avg_thickness,
                opacity
            ))
    
    # convert snum extremes to z extremes
    extremes[4] *= avg_thickness
    extremes[5] *= avg_thickness
    
    # return list tuples (volume, opengl objects)
    # return global bounding box to set view
    return (
        mesh_data_list,
        tuple(extremes)
    )

def addToExtremes(extremes, new_extremes):
    """Keep track of the extreme values."""
    e = extremes.copy()
    if not e:
        e = new_extremes
    else:
        ne = new_extremes
        if ne[0] < e[0]: e[0] = ne[0]
        if ne[1] > e[1]: e[1] = ne[1]
        if ne[2] < e[2]: e[2] = ne[2]
        if ne[3] > e[3]: e[3] = ne[3]
        if ne[4] < e[4]: e[4] = ne[4]
        if ne[5] > e[5]: e[5] = ne[5]

    return e
