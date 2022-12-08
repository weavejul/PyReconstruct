import os
import json

from modules.pyrecon.ztrace import Ztrace
from modules.pyrecon.section import Section
from modules.pyrecon.trace import Trace

from modules.pyrecon.obj_group_dict import ObjGroupDict

from constants.locations import assets_dir, backend_series_dir
from constants.defaults import getDefaultPaletteTraces

class Series():

    def __init__(self, filepath : str):
        """Load the series file.
        
            Params:
                filepath (str): the filepath for the series JSON file
        """
        self.filepath = filepath
        self.name = os.path.basename(self.filepath)[:-4]

        try:
            with open(filepath, "r") as f:
                series_data = json.load(f)
        except json.decoder.JSONDecodeError:
            print("Invalid JSON file")
            raise json.decoder.JSONDecodeError

        self.jser_fp = ""
        self.modified = False

        self.sections = {}  # section number : section file
        for section_num, section_filename in series_data["sections"].items():
            self.sections[int(section_num)] = section_filename
        self.current_section = series_data["current_section"]
        self.src_dir = series_data["src_dir"]
        self.screen_mag = 0  # default value for screen mag (calculated when generateView is called)
        self.window = series_data["window"]
        self.palette_traces = series_data["palette_traces"]
        for i in range(len(self.palette_traces)):
            self.palette_traces[i] = Trace.fromDict(self.palette_traces[i])
        self.current_trace = Trace.fromDict(series_data["current_trace"])
        self.ztraces = series_data["ztraces"]
        for i in range(len(self.ztraces)):
            self.ztraces[i] = Ztrace.fromDict(self.ztraces[i])
        self.alignment = series_data["alignment"]
        self.object_groups = ObjGroupDict(series_data["object_groups"])
        self.object_3D_modes = series_data["object_3D_modes"]

        # default settings
        self.fill_opacity = 0.2
    
    def getDict(self) -> dict:
        """Convert series object into a dictionary.
        
            Returns:
                (dict) all of the compiled section data
        """
        d = {}
        d["sections"] = self.sections
        d["current_section"] = self.current_section
        d["src_dir"] = self.src_dir
        d["window"] = self.window
        d["palette_traces"] = []
        for trace in self.palette_traces:
            d["palette_traces"].append(trace.getDict())
        d["current_trace"] = self.current_trace.getDict()
        d["ztraces"] = []
        for ztrace in self.ztraces:
            d["ztraces"].append(ztrace.getDict())
        d["alignment"] = self.alignment
        d["object_groups"] = self.object_groups.getGroupDict()
        d["object_3D_modes"] = self.object_3D_modes
        return d
    
    # STATIC METHOD
    def new(image_locations : list, series_name : str, mag : float, thickness : float):
        """Create a new blank series.
        
            Params:
                image_locations (list): the paths for each image
                series_name (str): user-entered series name
                mag (float): the microns per pixel for the series
                thickness (float): the section thickness
            Returns:
                (Series): the newly created series object
        """
        wdir = os.path.dirname(image_locations[0])
        series_data = {}
        series_data["sections"] = {}  # section_number : section_filename
        series_data["current_section"] = 0  # last section left off
        series_data["src_dir"] = wdir  # the directory of the images
        series_data["window"] = [0, 0, 1, 1] # x, y, w, h of reconstruct window in field coordinates
        for i in range(len(image_locations)):
            series_data["sections"][i] = series_name + "." + str(i)
        series_data["palette_traces"] = getDefaultPaletteTraces()  # trace palette
        series_data["current_trace"] = series_data["palette_traces"][0]
        series_data["ztraces"] = []
        series_data["alignment"] = "default"
        series_data["object_groups"] = {}
        series_data["object_3D_modes"] = {}

        series_fp = os.path.join(backend_series_dir, series_name + ".ser")
        with open(series_fp, "w") as series_file:
            series_file.write(json.dumps(series_data, indent=2))
        
        # create section files (.#)
        for i in range(len(image_locations)):
            Section.new(series_name, i, image_locations[i], mag, thickness, backend_series_dir)
        
        return Series(series_fp)
    
    def isWelcomeSeries(self):
        """Return True if self is the welcome series."""
        try:
            if os.path.samefile(self.filepath, os.path.join(assets_dir, "welcome_series", "welcome.ser")):
                return True
            else:
                return False
        except FileNotFoundError:
            print("yeet")
            return False
        
    def save(self):
        """Save file into json."""
        if self.isWelcomeSeries():
            return

        d = self.getDict()
        with open(self.filepath, "w") as f:
            f.write(json.dumps(d, indent=1))
    
    def getwdir(self) -> str:
        """Get the working directory of the series.
        
            Returns:
                (str): the directory containing the series
        """
        return os.path.dirname(self.filepath)
    
    def loadSection(self, section_num : int) -> Section:
        """Load a section object.
        
            Params:
                section_num (int): the section number
        """
        return Section(os.path.join(self.getwdir(), self.sections[section_num]))
    
    def newAlignment(self, alignment_name : str, base_alignment="default"):
        """Create a new alignment.
        
            Params:
                alignment_name (str): the name of the new alignment
                base_alignment (str): the name of the reference alignment for this new alignment
        """
        for snum in self.sections:
            section = self.loadSection(snum)
            section.tforms[alignment_name] = section.tforms[base_alignment]
            section.save()
    
    def createZtrace(self, obj_name : str):
        """Create a ztrace from an existing object in the series.
        
            Params:
                obj_name (str): the name of the object to create the ztrace from
        """
        for ztrace in self.ztraces:
            if obj_name == ztrace.name:
                self.ztraces.remove(ztrace)
                break
        points = []
        for snum in sorted(self.sections.keys()):
            section = self.loadSection(snum)
            if obj_name in section.contours:
                contour = section.contours[obj_name]
                p = (*contour.getMidpoint(), snum)
                points.append(p)
        self.ztraces.append(Ztrace(obj_name, points))

                
