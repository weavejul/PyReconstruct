from modules.legacy_recon.classes.zcontour import ZContour as XMLZContour

class Ztrace():

    def __init__(self, name : str, color : tuple, points : list = []):
        """Create a new ztrace.
        
            Params:
                name (str): the name of the ztrace
                color (tuple): the display color of the ztrace
                points (list): the points for the trace (x, y, section)
        """
        self.name = name
        self.color = color
        self.points = points
    
    def getDict(self) -> dict:
        """Get a dictionary representation of the object.
        
            Returns:
                (dict): the dictionary representation of the object
        """
        d = {}
        d["name"] = self.name
        d["color"] = self.color
        d["points"] = self.points.copy()
        return d
    
    # STATIC METHOD
    def dictFromXMLObj(xml_ztrace : XMLZContour):
        """Create a trace from an xml contour object.
        
            Params:
                xml_trace (XMLContour): the xml contour object
                xml_image_tform (XMLTransform): the xml image transform object
            Returns:
                (Trace) the trace object
        """
        # get basic attributes
        name = xml_ztrace.name
        color = list(xml_ztrace.border)
        for i in range(len(color)):
            color[i] = int(color[i] * 255)
        new_ztrace = Ztrace(name, color)
        new_ztrace.points = xml_ztrace.points.copy()
        
        return new_ztrace.getDict()
    
    def fromDict(d):
        """Create the object from a dictionary.
        
            Params:
                d (dict): the dictionary representation of the object
        """
        ztrace = Ztrace(d["name"], d["color"])
        ztrace.points = d["points"]
        return ztrace
    
    def smooth(self, smooth=10):
        """Smooth a ztrace."""

        x = [None] * smooth
        y = [None] * smooth

        points = [[p[0], p[1]] for p in self.points]

        pt_idx = 0
        p = points[pt_idx]

        for i in range(int(smooth/2) + 1):
            
             x[i] = p[0]
             y[i] = p[1]
        
        q = p
    
        for i in range(int(smooth/2) + 1, smooth):
        
            x[i] = q[0]
            y[i] = q[1]
            
            pt_idx += 1
            q = points[pt_idx]
        
        xMA = 0
        yMA = 0

        for i in range(smooth):
            
            xMA += x[i]/smooth
            yMA += y[i]/smooth
        
        for i, point in enumerate(points):  # Loop over all points
        
            point[0] = round(xMA, 4)
            point[1] = round(yMA, 4)
        
            old_x = x[0]
            old_y = y[0]
        
            for i in range(smooth - 1):
                x[i] = x[i+1]
                y[i] = y[i+1]
        
            try:
                pt_idx += 1
                q = points[pt_idx]
                x[smooth - 1] = q[0]
                y[smooth - 1] = q[1]
        
            except:
                pass
                
            xMA += (x[smooth-1] - old_x) / smooth
            yMA += (y[smooth-1] - old_y) / smooth

        # Update self.points
        for i, p in enumerate(points):
            save_point_old = self.points[i]
            current_sec = self.points[i][2]
            self.points[i] = (p[0], p[1], current_sec)
            print(f'old: {save_point_old} new: {self.points[i]}')

        return None
    
    def getSectionData(self, snum : int):
        """Get all the ztrace points on a section.
        
            Params:
                snum (int): the section number
            Returns:
                (list): list of points
                (list): list of lines between points
        """
        pts = []
        lines = []
        for i, pt in enumerate(self.points):
            # add point to list
            if pt[2] == snum:
                pts.append(pt[:2])
            
            # check for lines to draw
            if i > 0:
                prev_pt = self.points[i-1]
                if prev_pt[2] <= pt[2]:
                    p1, p2 = prev_pt, pt
                else:
                    p2, p1 = prev_pt, pt 
                if p1[2] <= snum <= p2[2]:
                    segments = p2[2] - p1[2] + 1
                    x_inc = (p2[0] - p1[0]) / segments
                    y_inc = (p2[1] - p1[1]) / segments
                    segment_i = snum - p1[2]
                    lines.append((
                        (
                            p1[0] + segment_i*x_inc,
                            p1[1] + segment_i*y_inc
                        ),
                        (
                            p1[0] + (segment_i+1)*x_inc,
                            p1[1] + (segment_i+1)*y_inc
                        )
                    ))
        
        return pts, lines
