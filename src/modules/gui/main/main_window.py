import os
import sys
import time
import subprocess

from PySide6.QtWidgets import (
    QMainWindow, 
    QFileDialog,
    QInputDialog, 
    QApplication,
    QMessageBox, 
    QMenu
)
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
    QPixmap
)
from PySide6.QtCore import Qt

from .field_widget import FieldWidget

from modules.gui.palette import MousePalette, ZarrPalette
from modules.gui.dialog import (
    AlignmentDialog,
    GridDialog,
    CreateZarrDialog,
    AddToZarrDialog,
    TrainDialog,
    SegmentDialog,
    PredictDialog,
    SwiftDialog
)
from modules.gui.popup import HistoryWidget
from modules.gui.utils import (
    progbar,
    populateMenuBar,
    populateMenu,
    notify,
    saveNotify,
    unsavedNotify,
    getSaveLocation,
    setMainWindow
)
from modules.backend.func import (
    xmlToJSON,
    jsonToXML,
    importTransforms,
    importSwiftTransforms
)
from modules.backend.autoseg import seriesToZarr, seriesToLabels, labelsToObjects
from modules.datatypes import Series, Transform
from modules.constants import welcome_series_dir, assets_dir, img_dir, src_dir

class MainWindow(QMainWindow):

    def __init__(self, argv):
        """Constructs the skeleton for an empty main window."""
        super().__init__() # initialize QMainWindow
        self.setWindowTitle("PyReconstruct")

        # set the window icon
        pix = QPixmap(os.path.join(img_dir, "PyReconstruct.ico"))
        self.setWindowIcon(pix)

        # set the main window to be slightly less than the size of the monitor
        screen = QApplication.primaryScreen()
        screen_rect = screen.size()
        x = 50
        y = 80
        w = screen_rect.width() - 100
        h = screen_rect.height() - 160
        self.setGeometry(x, y, w, h)

        # misc defaults
        self.series = None
        self.field = None  # placeholder for field
        self.menubar = None
        self.mouse_palette = None  # placeholder for palettes
        self.zarr_palette = None
        self.setMouseTracking(True) # set constant mouse tracking for various mouse modes
        self.is_zooming = False
        self.explorer_dir = ""
        self.restart_mainwindow = False

        # create status bar at bottom of window
        self.statusbar = self.statusBar()

        # open the series requested from command line
        if len(argv) > 1:
            self.openSeries(jser_fp=argv[1])
        else:
            welcome_series = Series(
                os.path.join(
                    welcome_series_dir,
                    "welcome.ser"
                ),
                {0: "welcome.0"}
            )
            welcome_series.src_dir = os.path.dirname(welcome_series_dir)  # set the images directory for the welcome series
            self.openSeries(welcome_series)
        
        self.field.generateView()

        # create menu and shortcuts
        self.createMenuBar()
        self.createContextMenus()
        self.createShortcuts()

        # set the main window as the parent of the progress bar
        setMainWindow(self)

        self.show()

    def createMenuBar(self):
        """Create the menu for the main window."""
        menu = [
            
            {
                "attr_name": "filemenu",
                "text": "File",
                "opts":
                [   
                    ("new_act", "New", "Ctrl+N", self.newSeries),
                    ("open_act", "Open", "Ctrl+O", self.openSeries),
                    None,  # None acts as menu divider
                    ("save_act", "Save", "Ctrl+S", self.saveToJser),
                    ("saveas_act", "Save as...", "", self.saveAsToJser),
                    ("backup_act", "Auto-backup series", "checkbox", self.autoBackup),
                    None,
                    ("fromxml_act", "New from XML series...", "", self.newFromXML),
                    ("exportxml_act", "Export as XML series...", "", self.exportToXML),
                    None,
                    ("username_act", "Change username...", "", self.changeUsername),
                    None,
                    ("restart_act", "Restart", "Ctrl+R", self.restart),
                    None,
                    ("quit_act", "Quit", "Ctrl+Q", self.close),
                ]
            },

            {
                "attr_name": "editmenu",
                "text": "Edit",
                "opts":
                [
                    ("undo_act", "Undo", "Ctrl+Z", self.field.undoState),
                    ("redo_act", "Redo", "Ctrl+Y", self.field.redoState),
                    None,
                    ("cut_act", "Cut", "Ctrl+X", self.field.cut),
                    ("copy_act", "Copy", "Ctrl+C", self.field.copy),
                    ("paste_act", "Paste", "Ctrl+V", self.field.paste),
                    ("pasteattributes_act", "Paste attributes", "Ctrl+B", self.field.pasteAttributes),
                    None,
                    ("incbr_act", "Increase brightness", "=", lambda : self.editImage(option="brightness", direction="up")),
                    ("decbr_act", "Decrease brightness", "-", lambda : self.editImage(option="brightness", direction="down")),
                    ("inccon_act", "Increase contrast", "]", lambda : self.editImage(option="contrast", direction="up")),
                    ("deccon_act", "Decrease contrast", "[", lambda : self.editImage(option="contrast", direction="down"))
                ]
            },

            {
                "attr_name": "seriesmenu",
                "text": "Series",
                "opts":
                [
                    {
                        "attr_name": "imagesmenu",
                        "text": "Images",
                        "opts":
                        [
                            ("change_src_act", "Find images", "", self.changeSrcDir),
                            ("zarrimage_act", "Convert images to zarr", "", self.srcToZarr)
                        ]
                    },
                    None,
                    ("objectlist_act", "Object list", "Ctrl+Shift+O", self.openObjectList),
                    ("ztracelist_act", "Z-trace list", "Ctrl+Shift+Z", self.openZtraceList),
                    ("history_act", "View series history", "", self.viewSeriesHistory),
                    None,
                    {
                        "attr_name": "alignments",
                        "text": "Alignments",
                        "opts":
                        [
                            {
                                "attr_name": "importmenu",
                                "text": "Import alignments",
                                "opts":
                                [
                                    ("import_transforms_act", ".txt file", "", self.importTransforms),
                                    ("import_swift_transforms_act", "SWiFT project", "", self.importSwiftTransforms),
                                ]
                            },
                            ("changealignment_act", "Change alignment", "Ctrl+Shift+A", self.changeAlignment),
                            {
                                "attr_name": "propogatemenu",
                                "text": "Propogate transform",
                                "opts":
                                [
                                    ("startpt_act", "Begin propogation", "", lambda : self.field.setPropogationMode(True)),
                                    ("endpt_act", "Finish propogation", "", lambda : self.field.setPropogationMode(False)),
                                    None,
                                    ("proptostart_act", "Propogate to start", "", lambda : self.field.propogateTo(False)),
                                    ("proptoend_act", "Propogate to end", "", lambda : self.field.propogateTo(True))
                                ]
                            }
                        ]
                    },
                    None,
                    {
                        "attr_name": "importmenu",
                        "text": "Import",
                        "opts":
                        [
                            ("importtraces_act", "Import traces", "", self.importTraces),
                            ("importzrtraces_act", "Import ztraces", "", self.importZtraces)
                        ]
                    },
                    None,
                    ("calibrate_act", "Calibrate pixel size...", "", self.calibrateMag),
                    None,
                    ("resetpalette_act", "Reset trace palette", "", self.mouse_palette.resetPalette)    
                ]
            },
            
            {
                "attr_name": "sectionmenu",
                "text": "Section",
                "opts":
                [
                    ("nextsection_act", "Next section", "PgUp", self.incrementSection),
                    ("prevsection_act", "Previous section", "PgDown", lambda : self.incrementSection(down=True)),
                    None,
                    ("sectionlist_act", "Section list", "Ctrl+Shift+S", self.openSectionList),
                    ("goto_act", "Go to section", "Ctrl+G", self.changeSection),
                    ("changetform_act", "Change transformation", "Ctrl+T", self.changeTform),
                    None,
                    ("tracelist_act", "Trace list", "Ctrl+Shift+T", self.openTraceList),
                    ("findcontour_act", "Find contour...", "Ctrl+F", self.field.findContourDialog),
                    None,
                    ("linearalign_act", "Align linear", "", self.field.linearAlign)
                ]
            },

            {
                "attr_name": "viewmenu",
                "text": "View",
                "opts":
                [
                    ("fillopacity_act", "Edit fill opacity...", "", self.setFillOpacity),
                    None,
                    ("homeview_act", "Set view to image", "Home", self.field.home),
                    ("viewmag_act", "View magnification...", "", self.field.setViewMagnification),
                    None,
                    ("paletteside_act", "Palette to other side", "Shift+L", self.toggleHandedness),
                    ("cornerbuttons_act",  "Toggle corner buttons", "Shift+T", self.mouse_palette.toggleCornerButtons),
                    None,
                    {
                        "attr_name": "zarrlayermenu",
                        "text": "Zarr layer",
                        "opts":
                        [
                            ("setzarrlayer_act", "Set zarr layer...", "", self.setZarrLayer),
                            ("removezarrlayer_act", "Remove zarr layer", "", self.removeZarrLayer)
                        ]
                    }
                ]
            },
            {
                "attr_name": "autosegmenu",
                "text": "Autosegment",
                "opts":
                [
                    ("export_zarr_act", "Export to zarr...", "", self.exportToZarr),
                    ("trainzarr_act", "Train...", "", self.train),
                    ("retrainzarr_act", "Retrain...", "", lambda : self.train(retrain=True)),
                    ("predictzarr_act", "Predict (infer)...", "", self.predict),
                    ("sementzarr_act", "Segment...", "", self.segment),
                    {
                        "attr_name": "zarrlayermenu",
                        "text": "Zarr layer",
                        "opts":
                        [
                            ("setzarrlayer_act", "Set zarr layer...", "", self.setZarrLayer),
                            ("removezarrlayer_act", "Remove zarr layer", "", self.removeZarrLayer)
                        ]
                    }
                ]
            }
        ]

        if self.menubar:
            self.menubar.close()

        # Populate menu bar with menus and options
        self.menubar = self.menuBar()
        self.menubar.setNativeMenuBar(False)
        populateMenuBar(self, self.menubar, menu)
    
    def createContextMenus(self):
        """Create the right-click menus used in the field."""
        field_menu_list = [
            ("edittrace_act", "Edit attributes...", "Ctrl+E", self.field.traceDialog),
            {
                "attr_name": "modifymenu",
                "text": "Modify",
                "opts":
                [
                    ("mergetraces_act", "Merge traces", "Ctrl+M", self.field.mergeSelectedTraces),
                    ("mergeobjects_act", "Merge object traces...", "Ctrl+Shift+M", lambda : self.field.mergeSelectedTraces(merge_objects=True)),
                    None,
                    ("makenegative_act", "Make negative", "", self.field.makeNegative),
                    ("makepositive_act", "Make positive", "", lambda : self.field.makeNegative(False)),
                    None,
                    ("markseg_act", "Add to good segmentation group", "Shift+G", self.markKeep)
                ]
            },
            None,
            {
                "attr_name": "viewmenu",
                "text": "View",
                "opts":
                [
                    ("hidetraces_act", "Hide traces", "Ctrl+H", self.field.hideTraces),
                    ("unhideall_act", "Unhide all traces", "Ctrl+U", self.field.unhideAllTraces),
                    None,
                    ("hideall_act", "Toggle hide all", "H", self.field.toggleHideAllTraces),
                    ("showall_act", "Toggle show all", "A", self.field.toggleShowAllTraces),
                    None,
                    ("hideimage_act", "Toggle hide image", "I", self.field.toggleHideImage),
                    ("blend_act", "Toggle section blend", " ", self.field.toggleBlend),
                ]
            },
            None,
            self.cut_act,
            self.copy_act,
            self.paste_act,
            self.pasteattributes_act,
            None,
            ("selectall_act", "Select all traces", "Ctrl+A", self.field.selectAllTraces),
            ("deselect_act", "Deselect traces", "Ctrl+D", self.field.deselectAllTraces),
            None,
            ("deletetraces_act", "Delete traces", "Del", self.field.backspace)
        ]
        self.field_menu = QMenu(self)
        populateMenu(self, self.field_menu, field_menu_list)

        # organize actions
        self.trace_actions = [
            self.edittrace_act,
            self.modifymenu,
            self.mergetraces_act,
            self.makepositive_act,
            self.makenegative_act,
            self.hidetraces_act,
            self.cut_act,
            self.copy_act,
            self.pasteattributes_act,
            self.deletetraces_act
        ]
        self.ztrace_actions = [
            self.edittrace_act
        ]

        # create the label menu
        label_menu_list = [
            ("importlabels_act", "Import label(s)", "", self.importLabels),
            ("mergelabels_act", "Merge labels", "", self.mergeLabels)
        ]
        self.label_menu = QMenu(self)
        populateMenu(self, self.label_menu, label_menu_list)


    def createShortcuts(self):
        """Create shortcuts that are NOT included in any menus."""
        # domain translate motions
        shortcuts = [
            ("Backspace", self.field.backspace),

            ("/", self.flickerSections),

            ("Ctrl+Left", lambda : self.translate("left", "small")),
            ("Left", lambda : self.translate("left", "med")),
            ("Shift+Left", lambda : self.translate("left", "big")),
            ("Ctrl+Right", lambda : self.translate("right", "small")),
            ("Right", lambda : self.translate("right", "med")),
            ("Shift+Right", lambda : self.translate("right", "big")),
            ("Ctrl+Up", lambda : self.translate("up", "small")),
            ("Up", lambda : self.translate("up", "med")),
            ("Shift+Up", lambda : self.translate("up", "big")),
            ("Ctrl+Down", lambda : self.translate("down", "small")),
            ("Down", lambda : self.translate("down", "med")),
            ("Shift+Down", lambda : self.translate("down", "big")),

            ("Ctrl+Shift+Left", self.field.rotateTform),
            ("Ctrl+Shift+Right", lambda : self.field.rotateTform(cc=False))
        ]

        for kbd, act in shortcuts:
            QShortcut(QKeySequence(kbd), self).activated.connect(act)
    
    def createPaletteShortcuts(self):
        """Create shortcuts associate with the mouse palette."""
        # trace palette shortcuts (1-20)
        trace_shortcuts = []
        for i in range(1, 21):
            sc_str = ""
            if (i-1) // 10 > 0:
                sc_str += "Shift+"
            sc_str += str(i % 10)
            s_switch = (
                sc_str,
                lambda pos=i-1 : self.mouse_palette.activatePaletteButton(pos)
            )
            s_modify = (
                "Ctrl+" + sc_str,
                lambda pos=i-1 : self.mouse_palette.modifyPaletteButton(pos)
            )
            trace_shortcuts.append(s_switch)
            trace_shortcuts.append(s_modify)
        
        # mouse mode shortcuts (F1-F8)
        mode_shortcuts = [
            ("p", lambda : self.mouse_palette.activateModeButton("Pointer")),
            ("z", lambda : self.mouse_palette.activateModeButton("Pan/Zoom")),
            ("k", lambda : self.mouse_palette.activateModeButton("Knife")),
            ("c", lambda : self.mouse_palette.activateModeButton("Closed Trace")),
            ("o", lambda : self.mouse_palette.activateModeButton("Open Trace")),
            ("s", lambda : self.mouse_palette.activateModeButton("Stamp"))
        ]
  
        for kbd, act in (mode_shortcuts + trace_shortcuts):
            QShortcut(QKeySequence(kbd), self).activated.connect(act)
    
    def changeSrcDir(self, new_src_dir : str = None, notify=False):
        """Open a series of dialogs to change the image source directory.
        
            Params:
                new_src_dir (str): the new image directory
                notify (bool): True if user is to be notified with a pop-up
        """
        if notify:
            reply = QMessageBox.question(
                self,
                "Images Not Found",
                "Images not found.\nWould you like to locate them?",
                QMessageBox.Yes,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        if new_src_dir is None:
            new_src_dir = QFileDialog.getExistingDirectory(
                self,
                "Select folder containing images",
                dir=self.explorer_dir
            )
        if not new_src_dir:
            return
        self.series.src_dir = new_src_dir
        if self.field:
            self.field.reloadImage()
    
    def srcToZarr(self):
        """Convert the series images to zarr."""
        if self.field.section_layer.is_zarr_file:
            notify("Images are already in zarr format.")
            return

        if not self.field.section_layer.image_found:
            notify("Images not found.")
            return
        
        zarr_fp, ext = QFileDialog.getSaveFileName(
            self,
            "Convert Images to Zarr",
            f"{self.series.name}_images.zarr",
            filter="Zarr Directory (*.zarr)"
        )

        if not zarr_fp:
            return

        python_bin = sys.executable
        zarr_converter = os.path.join(assets_dir, "scripts", "create_zarr.py")

        convert_cmd = f'{python_bin} {zarr_converter} {self.series.src_dir} {zarr_fp}'

        if os.name == 'nt':
            subprocess.Popen(convert_cmd, creationflags=subprocess.CREATE_NEW_CONSOLE, shell=True)
        else:
            convert_cmd = "nohup " + convert_cmd
            print(convert_cmd)
            subprocess.Popen(convert_cmd, shell=True, stdout=None, stderr=None, preexec_fn=os.setpgrp)

    def changeUsername(self, new_name : str = None):
        """Edit the login name used to track history.
        
            Params:
                new_name (str): the new username
        """
        if new_name is None:
            new_name, confirmed = QInputDialog.getText(
                self,
                "Change Login",
                "Enter your desired username:",
                text=os.getlogin()
            )
            if not confirmed or not new_name:
                return
        
        def getlogin():
            return new_name
        
        os.getlogin = getlogin
    
    def setFillOpacity(self, opacity : float = None):
        """Set the opacity of the trace highlight.
        
            Params:
                opacity (float): the new fill opacity
        """
        if opacity is None:
            opacity, confirmed = QInputDialog.getText(
                self,
                "Fill Opacity",
                "Enter fill opacity (0-1):",
                text=str(round(self.series.options["fill_opacity"], 3))
            )
            if not confirmed:
                return
        
        try:
            opacity = float(opacity)
        except ValueError:
            return
        
        if not (0 <= opacity <= 1):
            return
        
        self.series.options["fill_opacity"] = opacity
        self.field.generateView(generate_image=False)

    def openSeries(self, series_obj=None, jser_fp=None):
        """Open an existing series and create the field.
        
            Params:
                series_obj (Series): the series object (optional)
        """
        if not series_obj:  # if series is not provided            
            # get the new series
            new_series = None
            if not jser_fp:
                jser_fp, extension = QFileDialog.getOpenFileName(
                    self,
                    "Select Series",
                    dir=self.explorer_dir,
                    filter="*.jser"
                )
                if jser_fp == "": return  # exit function if user does not provide series
            
            # user has opened an existing series
            if self.series:
                response = self.saveToJser(notify=True)
                if response == "cancel":
                    return

            # check for a hidden series folder
            sdir = os.path.dirname(jser_fp)
            sname = os.path.basename(jser_fp)
            sname = sname[:sname.rfind(".")]
            hidden_series_dir = os.path.join(sdir, f".{sname}")

            if os.path.isdir(hidden_series_dir):
                # find the series and timer files
                new_series_fp = ""
                sections = {}
                for f in os.listdir(hidden_series_dir):
                    # check if the series is currently being modified
                    if "." not in f:
                        current_time = round(time.time())
                        time_diff = current_time - int(f)
                        if time_diff <= 7:  # the series is currently being operated on
                            QMessageBox.information(
                                self,
                                "Series In Use",
                                "This series is already open in another window.",
                                QMessageBox.Ok
                            )
                            if not self.series:
                                exit()
                            else:
                                return
                    else:
                        ext = f[f.rfind(".")+1:]
                        if ext.isnumeric():
                            sections[int(ext)] = f
                        elif ext == "ser":
                            new_series_fp = os.path.join(hidden_series_dir, f)                    

                # if a series file has been found
                if new_series_fp:
                    # ask the user if they want to open the unsaved series
                    open_unsaved = unsavedNotify()
                    if open_unsaved:
                        new_series = Series(new_series_fp, sections)
                        new_series.modified = True
                        new_series.jser_fp = jser_fp
                    else:
                        # remove the folder if not needed
                        for f in os.listdir(hidden_series_dir):
                            os.remove(os.path.join(hidden_series_dir, f))
                        os.rmdir(hidden_series_dir)
                else:
                    # remove the folder if no series file detected
                    for f in os.listdir(hidden_series_dir):
                        os.remove(os.path.join(hidden_series_dir, f))
                    os.rmdir(hidden_series_dir)

            # open the JSER file if no unsaved series was opened
            if not new_series:
                new_series = Series.openJser(jser_fp)
                # user pressed cancel
                if new_series is None:
                    if self.series is None:
                        exit()
                    else:
                        return
            
            # clear the current series
            if self.series and not self.series.isWelcomeSeries():
                self.series.close()

            self.series = new_series

        # series has already been provided by other function
        else:
            self.series = series_obj
        
        # set the title of the main window
        self.seriesModified(self.series.modified)

        # set the explorer filepath to the series
        if not self.series.isWelcomeSeries():
            self.explorer_dir = os.path.dirname(self.series.getwdir())

        # create field
        if self.field is not None:  # close previous field widget
            self.field.createField(self.series)
        else:
            self.field = FieldWidget(self.series, self)
            self.setCentralWidget(self.field)

        # create mouse palette
        if self.mouse_palette: # close previous mouse dock
            self.mouse_palette.reset(self.series.palette_traces, self.series.current_trace)
        else:
            self.mouse_palette = MousePalette(self.series.palette_traces, self.series.current_trace, self)
            self.createPaletteShortcuts()
        self.changeTracingTrace(self.series.current_trace) # set the current trace

        # ensure that images are found
        if not self.field.section_layer.image_found:
            # check jser directory
            src_path = os.path.join(
                os.path.dirname(self.series.jser_fp),
                os.path.basename(self.field.section.src)
            )
            images_found = os.path.isfile(src_path)
            
            if images_found:
                self.changeSrcDir(src_path)
            else:
                self.changeSrcDir(notify=True)
    
    def newSeries(
        self,
        image_locations : list = None,
        series_name : str = None,
        mag : float = None,
        thickness : float = None
    ):
        """Create a new series from a set of images.
        
            Params:
                image_locations (list): the filpaths for the section images.
        """
        # get images from user
        if not image_locations:
            image_locations, extensions = QFileDialog.getOpenFileNames(
                self,
                "Select Images",
                dir=self.explorer_dir,
                filter="*.jpg *.jpeg *.png *.tif *.tiff *.bmp"
            )
            if len(image_locations) == 0:
                return
        # get the name of the series from user
        if series_name is None:
            series_name, confirmed = QInputDialog.getText(
                self, "New Series", "Enter series name:")
            if not confirmed:
                return
        # get calibration (microns per pix) from user
        if mag is None:
            mag, confirmed = QInputDialog.getDouble(
                self, "New Series", "Enter image calibration (μm/px):",
                0.00254, minValue=0.000001, decimals=6)
            if not confirmed:
                return
        # get section thickness (microns) from user
        if thickness is None:
            thickness, confirmed = QInputDialog.getDouble(
                self, "New Series", "Enter section thickness (μm):",
                0.05, minValue=0.000001, decimals=6)
            if not confirmed:
                return
        
        # save and clear the existing backend series
        self.saveToJser(notify=True, close=True)
        
        # create new series
        series = Series.new(sorted(image_locations), series_name, mag, thickness)
    
        # open series after creating
        self.openSeries(series)
    
    def newFromXML(self, series_fp : str = None):
        """Create a new series from a set of XML files.
        
            Params:
                series_fp (str): the filepath for the XML series
        """

        # get xml series filepath from the user
        if not series_fp:
            series_fp, ext = QFileDialog.getOpenFileName(
                self,
                "Select XML Series",
                dir=self.explorer_dir,
                filter="*.ser"
            )
        if series_fp == "": return  # exit function if user does not provide series

        # save and clear the existing backend series
        self.saveToJser(notify=True, close=True)
        
        # convert the series
        series = xmlToJSON(os.path.dirname(series_fp))
        if not series:
            return

        # open the series
        self.openSeries(series)
    
    def exportToXML(self, export_fp : str = None):
        """Export the current series to XML.
        
            Params:
                export_fp (str): the filepath for the XML .ser file
        """
        # save the current data
        self.saveAllData()

        # get the new xml series filepath from the user
        if not export_fp:
            export_fp, ext = QFileDialog.getSaveFileName(
                self,
                "Export Series",
                f"{self.series.name}.ser",
                filter="XML Series (*.ser)"
            )
            if not export_fp:
                return False
        
        # convert the series
        jsonToXML(self.series, os.path.dirname(export_fp))
    
    def seriesModified(self, modified=True):
        """Change the title of the window reflect modifications."""
        # check for welcome series
        if self.series.isWelcomeSeries():
            self.setWindowTitle("PyReconstruct")
            return
        
        if modified:
            self.setWindowTitle(self.series.name + "*")
        else:
            self.setWindowTitle(self.series.name)
        self.series.modified = modified
    
    def importTransforms(self, tforms_fp : str = None):
        """Import transforms from a text file.
        
            Params:
                tforms_file (str): the filepath for the transforms file
        """
        self.saveAllData()
        # get file from user
        if tforms_fp is None:
            tforms_fp, ext = QFileDialog.getOpenFileName(
                self,
                "Select file containing transforms",
                dir=self.explorer_dir
            )
        if not tforms_fp:
            return
        # import the transforms
        importTransforms(self.series, tforms_fp)
        # reload the section
        self.field.reload()

    def importSwiftTransforms(self, tforms_fp : str = None):
        """Import transforms from a text file.
        
            Params:
                tforms_file (str): the filepath for the transforms file
        """
        self.saveAllData()

        swift_fp = None  # Ummmmm, not sure about this?
        
        # get file from user
        if swift_fp is None:
            swift_fp, ext = QFileDialog.getOpenFileName(
                self,
                "Select SWiFT project file",
                dir=self.explorer_dir
            )

        if not swift_fp: return

        response, confirmed = SwiftDialog(self, swift_fp).exec()
        scale, cal_grid = response

        # import transforms
        print(f'Importing SWiFT transforms at scale {scale}...')
        if cal_grid: print('Cal grid included in series')
        importSwiftTransforms(self.series, swift_fp, scale, cal_grid)
        
        self.field.reload()
    
    def importTraces(self, jser_fp : str = None):
        """Import traces from another jser series.
        
            Params:
                jser_fp (str): the filepath with the series to import data from
        """
        if jser_fp is None:
            jser_fp, extension = QFileDialog.getOpenFileName(
                self,
                "Select Series",
                dir=self.explorer_dir,
                filter="*.jser"
            )
        if jser_fp == "": return  # exit function if user does not provide series

        self.saveAllData()

        # open the other series
        o_series = Series.openJser(jser_fp)

        # import the traces and close the other series
        self.series.importTraces(o_series)
        o_series.close()

        # reload the field to update the traces
        self.field.reload()

        # refresh the object list if needed
        if self.field.obj_table_manager:
            self.field.obj_table_manager.refresh()
    
    def importZtraces(self, jser_fp : str = None):
        """Import ztraces from another jser series.
        
            Params:
                jser_fp (str): the filepath with the series to import data from
        """
        if jser_fp is None:
            jser_fp, extension = QFileDialog.getOpenFileName(
                self,
                "Select Series",
                dir=self.explorer_dir,
                filter="*.jser"
            )
        if jser_fp == "": return  # exit function if user does not provide series

        self.saveAllData()

        # open the other series
        o_series = Series.openJser(jser_fp)

        # import the ztraces and close the other series
        self.series.importZtraces(o_series)
        o_series.close()

        # reload the field to update the ztraces
        self.field.reload()

        # refresh the ztrace list if needed
        if self.field.ztrace_table_manager:
            self.field.ztrace_table_manager.refresh()
    
    def editImage(self, option : str, direction : str):
        """Edit the brightness or contrast of the image.
        
            Params:
                option (str): brightness or contrast
                direction (str): up or down
        """
        if option == "brightness" and direction == "up":
            self.field.changeBrightness(1)
        elif option == "brightness" and direction == "down":
            self.field.changeBrightness(-1)
        elif option == "contrast" and direction == "up":
            self.field.changeContrast(2)
        elif option == "contrast" and direction == "down":
            self.field.changeContrast(-2)
    
    def changeMouseMode(self, new_mode):
        """Change the mouse mode of the field (pointer, panzoom, tracing...).

        Called when user clicks on mouse mode palette.

            Params:
                new_mode: the new mouse mode to set
        """
        self.field.setMouseMode(new_mode)

    def changeTracingTrace(self, trace):
        """Change the trace utilized by the user.

        Called when user clicks on trace palette.

            Params:
                trace: the new tracing trace to set
        """
        self.series.current_trace = trace
        self.field.setTracingTrace(trace)
    
    def changeSection(self, section_num : int = None, save=True):
        """Change the section of the field.
        
            Params:
                section_num (int): the section number to change to
                save (bool): saves data to files if True
        """
        if section_num is None:
            section_num, confirmed = QInputDialog.getText(
                self, "Go To Section", "Enter the desired section number:", text=str(self.series.current_section))
            if not confirmed:
                return
            try:
                section_num = int(section_num)
            except ValueError:
                return
        
        # end the field pending events
        self.field.endPendingEvents()
        # save data
        if save:
            self.saveAllData()
        # change the field section
        self.field.changeSection(section_num)
        # update status bar
        self.field.updateStatusBar()
    
    def flickerSections(self):
        """Switch between the current and b sections."""
        if self.field.b_section:
            self.changeSection(self.field.b_section.n, save=False)
    
    def incrementSection(self, down=False):
        """Increment the section number by one.
        
            Params:
                down (bool): the direction to move
        """
        section_numbers = sorted(list(self.series.sections.keys()))  # get list of all section numbers
        section_number_i = section_numbers.index(self.series.current_section)  # get index of current section number in list
        if down:
            if section_number_i > 0:
                self.changeSection(section_numbers[section_number_i - 1])  
        else:   
            if section_number_i < len(section_numbers) - 1:
                self.changeSection(section_numbers[section_number_i + 1])       
    
    def wheelEvent(self, event):
        """Called when mouse scroll is used."""
        # do nothing if middle button is clicked
        if self.field.mclick:
            return
        
        modifiers = QApplication.keyboardModifiers()

        # if zooming
        if modifiers == Qt.ControlModifier:
            field_cursor = self.field.cursor()
            p = self.field.mapFromGlobal(field_cursor.pos())
            x, y = p.x(), p.y()
            if not self.is_zooming:
                # check if user just started zooming in
                self.field.panzoomPress(x, y)
                self.zoom_factor = 1
                self.is_zooming = True

            if event.angleDelta().y() > 0:  # if scroll up
                self.zoom_factor *= 1.1
            elif event.angleDelta().y() < 0:  # if scroll down
                self.zoom_factor *= 0.9
            self.field.panzoomMove(zoom_factor=self.zoom_factor)
        
        # if changing sections
        elif modifiers == Qt.NoModifier:
            # check for the position of the mouse
            mouse_pos = event.point(0).pos()
            field_geom = self.field.geometry()
            if not field_geom.contains(mouse_pos.x(), mouse_pos.y()):
                return
            # change the section
            if event.angleDelta().y() > 0:  # if scroll up
                self.incrementSection()
            elif event.angleDelta().y() < 0:  # if scroll down
                self.incrementSection(down=True)
    
    def keyReleaseEvent(self, event):
        """Overwritten: checks for Ctrl+Zoom."""
        if self.is_zooming and event.key() == 16777249:
            self.field.panzoomRelease(zoom_factor=self.zoom_factor)
            self.is_zooming = False
        
        super().keyReleaseEvent(event)
    
    def saveAllData(self):
        """Write current series and section data into backend JSON files."""
        if self.series.isWelcomeSeries():
            return
        # save the trace palette
        self.series.palette_traces = []
        for button in self.mouse_palette.palette_buttons:  # get trace palette
            self.series.palette_traces.append(button.trace)
            if button.isChecked():
                self.series.current_trace = button.trace
        self.field.section.save()
        self.series.save()
    
    def saveToJser(self, notify=False, close=False):
        """Save all data to JSER file.
        
        Params:
            save_data (bool): True if series and section files in backend should be save
            close (bool): Deletes backend series if True
        """
        # save the series data
        self.saveAllData()

        # if welcome series -> close without saving
        if self.series.isWelcomeSeries():
            return
        
        # notify the user and check if series was modified
        if notify and self.series.modified:
            save = saveNotify()
            if save == "no":
                if close:
                    self.series.close()
                return
            elif save == "cancel":
                return "cancel"
        
        # check if the user is closing and the series was not modified
        if close and not self.series.modified:
            self.series.close()
            return

        # run save as if there is no jser filepath
        if not self.series.jser_fp:
            self.saveAsToJser(close=close)
        else:        
            self.series.saveJser(close=close)
        
        # set the series to unmodified
        self.seriesModified(False)
    
    def saveAsToJser(self, close=False):
        """Prompt the user to find a save location."""
        # save the series data
        self.saveAllData()

        # check for wlecome series
        if self.series.isWelcomeSeries():
            return

        # get location from user
        new_jser_fp, confirmed = getSaveLocation(self.series)
        if not confirmed:
            return
        
        # move the working hidden folder to the new jser directory
        self.series.move(
            new_jser_fp,
            self.field.section,
            self.field.b_section
        )
        
        # save the file
        self.series.saveJser(close=close)

        # set the series to unmodified
        self.seriesModified(False)
    
    def autoBackup(self):
        """Set up the auto-backup functionality for the series."""
        # user checked the option
        if self.backup_act.isChecked():
            # prompt the user to find a folder to store backups
            new_dir = QFileDialog.getExistingDirectory(
                self,
                "Select folder to contain backup files",
                dir=self.explorer_dir
            )
            if not new_dir:
                self.backup_act.setChecked(False)
                return
            self.series.options["backup_dir"] = new_dir
        # user unchecked the option
        else:
            self.series.options["backup_dir"] = ""
        
        self.seriesModified()
    
    def viewSeriesHistory(self):
        """View the history for the entire series."""
        # load all log objects from the all traces
        log_history = []
        update, canceled = progbar("Object History", "Loading history...")
        progress = 0
        final_value = len(self.series.sections)
        for snum in self.series.sections:
            section = self.series.loadSection(snum)
            for trace in section.tracesAsList():
                for log in trace.history:
                    log_history.append((log, trace.name, snum))
            if canceled():
                return
            progress += 1
            update(progress/final_value * 100)
        
        log_history.sort()

        output_str = "Series History\n"
        for log, name, snum in log_history:
            output_str += f"Section {snum} "
            output_str += name + " "
            output_str += str(log) + "\n"
        
        self.history_widget = HistoryWidget(self, output_str)
    
    def openObjectList(self):
        """Open the object list widget."""
        self.saveAllData()
        self.field.openObjectList()
    
    def openZtraceList(self):
        """Open the ztrace list widget."""
        self.saveAllData()
        self.field.openZtraceList()
    
    def openTraceList(self):
        """Open the trace list widget."""
        self.field.openTraceList()
    
    def openSectionList(self):
        """Open the section list widget."""
        self.saveAllData()
        self.field.openSectionList()
    
    def setToObject(self, obj_name : str, section_num : str):
        """Focus the field on an object from a specified section.
        
            Params:
                obj_name (str): the name of the object
                section_num (str): the section the object is located
        """
        self.changeSection(section_num)
        self.field.findContour(obj_name)
    
    def changeTform(self, new_tform_list : list = None):
        """Open a dialog to change the transform of a section."""
        # check for section locked status
        if self.field.section.align_locked:
            return
        
        if new_tform_list is None:
            current_tform = " ".join(
                [str(round(n, 5)) for n in self.field.section.tforms[self.series.alignment].getList()]
            )
            new_tform_list, confirmed = QInputDialog.getText(
                self, "New Transform", "Enter the desired section transform:", text=current_tform)
            if not confirmed:
                return
            try:
                new_tform_list = [float(n) for n in new_tform_list.split()]
                if len(new_tform_list) != 6:
                    return
            except ValueError:
                return
        self.field.changeTform(Transform(new_tform_list))
    
    def translate(self, direction : str, amount : str):
        """Translate the current transform.
        
            Params:
                direction (str): left, right, up, or down
                amount (str): small, med, or big
        """
        if amount == "small":
            num = self.series.options["small_dist"]
        elif amount == "med":
            num = self.series.options["med_dist"]
        elif amount == "big":
            num = self.series.options["big_dist"]
        if direction == "left":
            x, y = -num, 0
        elif direction == "right":
            x, y = num, 0
        elif direction == "up":
            x, y = 0, num
        elif direction == "down":
            x, y = 0, -num
        self.field.translate(x, y)
    
    def newAlignment(self, new_alignment_name : str):
        """Add a new alignment (based on existing alignment).
        
            Params:
                new_alignment_name (str): the name of the new alignment
        """
        if new_alignment_name in self.field.section.tforms:
            QMessageBox.information(
                self,
                " ",
                "This alignment already exists.",
                QMessageBox.Ok
            )
            return
        self.series.newAlignment(
            new_alignment_name,
            self.series.alignment
        )
    
    def changeAlignment(self, alignment_name : str = None):
        """Open dialog to modify and change alignments.
        
            Params:
                alignment_name (str): the name of the alignment ro switch to
        """
        alignments = list(self.field.section.tforms.keys())

        if alignment_name is None:
            response, confirmed = AlignmentDialog(
                self,
                alignments
            ).exec()
            if not confirmed:
                return
            (
                alignment_name,
                added,
                removed,
                renamed
            ) = response
        else:
            added, removed, renamed = [], [], []
        
        if added or removed or renamed:
            self.series.modifyAlignments(added, removed, renamed)
            self.field.reload()
        
        if alignment_name:
            self.field.changeAlignment(alignment_name)
    
    def calibrateMag(self, trace_lengths : dict = None):
        """Calibrate the pixel size for the series.
        
            Params:
                trace_lengths (dict): the lengths of traces to calibrate
        """
        self.saveAllData()
        
        if trace_lengths is None:
            # gather trace names
            names = []
            for trace in self.field.section.selected_traces:
                if trace.name not in names:
                    names.append(trace.name)
            
            if len(names) == 0:
                notify("Please select traces for calibration.")
            
            # prompt user for length of each trace name
            trace_lengths = {}
            for name in names:
                d, confirmed = QInputDialog.getText(
                    self,
                    "Trace Length",
                    f'Length of "{name}" in microns:'
                )
                if not confirmed:
                    return
                try:
                    d = float(d)
                except ValueError:
                    return
                trace_lengths[name] = d
        
        self.field.calibrateMag(trace_lengths)
    
    def modifyGrid(self, event=None):
        """Modify the grid properties."""
        response, confirmed = GridDialog(
            self,
            tuple(self.series.options["grid"])
        ).exec()
        if not confirmed:
            return
        
        self.series.options["grid"] = response
        self.seriesModified()
    
    def toggleHandedness(self):
        """Toggle the handedness of the palettes."""
        self.mouse_palette.toggleHandedness()
        if self.zarr_palette:
            self.zarr_palette.toggleHandedness()
    
    def setZarrLayer(self, zarr_dir=None):
        """Set a zarr layer."""
        if not zarr_dir:
            zarr_dir = QFileDialog.getExistingDirectory(
                self,
                "Select overlay zarr",
                dir=self.explorer_dir
            )
            if not zarr_dir:
                return

        self.series.zarr_overlay_fp = zarr_dir
        self.series.zarr_overlay_group = None

        groups = []
        for g in os.listdir(zarr_dir):
            if os.path.isdir(os.path.join(zarr_dir, g)):
                groups.append(g)

        self.zarr_palette = ZarrPalette(groups, self)
    
    def setLayerGroup(self, group_name):
        """Set the specific group displayed in the zarr layer."""
        if not group_name:
            group_name = None
        if self.zarr_palette.cb.currentText != group_name:
            self.zarr_palette.cb.setCurrentText(group_name)
        self.series.zarr_overlay_group = group_name
        self.field.createZarrLayer()
        self.field.generateView()
    
    def removeZarrLayer(self):
        """Remove an existing zarr layer."""
        self.series.zarr_overlay_fp = None
        self.series.zarr_overlay_group = None
        if self.zarr_palette:
            self.zarr_palette.close()
        self.field.createZarrLayer()
        self.field.generateView()

    def exportToZarr(self):
        """Set up an autosegmentation for a series.
        
            Params:
                run (str): "train" or "segment"
        """
        self.saveAllData()
        self.removeZarrLayer()

        if not self.series.jser_fp:
            self.saveAsToJser()
            if not self.series.jser_fp:
                return

        inputs, dialog_confirmed = CreateZarrDialog(self, self.series).exec()

        if not dialog_confirmed: return

        print("Making zarr directory...")
        
        # export to zarr
        border_obj, srange, mag = inputs
        data_fp = seriesToZarr(
            self.series,
            border_obj,
            srange,
            mag
        )

        self.series.options["autoseg"]["zarr_current"] = data_fp

        print("Zarr directory done.")
    
    def train(self, retrain=False):
        """Train an autosegmentation model."""
        self.saveAllData()
        self.removeZarrLayer()

        print("Importing training modules...")

        from autoseg import train, make_mask, model_paths
        # model_paths = {"a":{"b":"a/b/m.py"}}

        opts = self.series.options["autoseg"]

        response, confirmed = TrainDialog(self, self.series, model_paths, opts, retrain).exec()
        if not confirmed: return
        
        (data_fp, iterations, save_every, group, model_path, cdir, \
         pre_cache, min_masked, downsample) = response

        training_opts = {
            'zarr_current': data_fp,
            'iters': iterations,
            'save_every': save_every,
            'group': group,
            'model_path': model_path,
            'checkpts_dir': cdir,
            'pre_cache': pre_cache,
            'min_masked': min_masked,
            'downsample_bool': downsample
        }

        for k, v in training_opts.items():
            opts[k] = v
        self.seriesModified(True)

        print("Exporting labels to zarr directory...")
        
        if retrain:
            group_name = f"labels_{self.series.getRecentSegGroup()}_keep"
            seriesToLabels(self.series, data_fp)
            
        else:
            group_name = f"labels_{group}"
            seriesToLabels(self.series, data_fp, group)

        print("Zarr directory updated with labels!")

        if retrain: self.field.reload()
        if retrain and self.field.obj_table_manager:
            self.field.obj_table_manager.refresh()

        print("Starting training....")

        make_mask(data_fp, group_name)
        
        sources = [{
            "raw" : (data_fp, "raw"),
            "labels" : (data_fp, group_name),
            "unlabelled" : (data_fp, "unlabelled")
        }]

        train(
            iterations=iterations,
            save_every=save_every,
            sources=sources,
            model_path=model_path,
            pre_cache=pre_cache,
            min_masked=min_masked,
            downsample=downsample,
            checkpoint_basename=os.path.join(cdir, "model")  # where existing checkpoints
        )

        print("Done training!")
    
    def markKeep(self):
        """Add the selected trace to the most recent "keep" segmentation group."""
        keep_tag = f"{self.series.getRecentSegGroup()}_keep"
        for trace in self.field.section.selected_traces:
            trace.addTag(keep_tag)
        # deselect traces and hide
        self.field.hideTraces()
        self.field.deselectAllTraces()

    def predict(self, data_fp : str = None):
        """Run predictons.
        
            Params:
                data_fp (str): the filepath for the zarr
        """
        self.saveAllData()
        self.removeZarrLayer()

        print("Importing models...")
        
        from autoseg import predict, model_paths
        # model_paths = {"a":{"b":"a/b/m.py"}}

        opts = self.series.options["autoseg"]

        response, dialog_confirmed = PredictDialog(self, model_paths, opts).exec()

        if not dialog_confirmed: return

        data_fp, model_path, cp_path, write_opts, increase, downsample, full_out_roi = response

        predict_opts = {
            'zarr_current': data_fp,
            'model_path': model_path,
            'checkpts_dir': os.path.dirname(cp_path),
            'write': write_opts,
            'increase': increase,
            'downsample_bool': downsample,
            'full_out_roi': full_out_roi
        }

        for k, v in predict_opts.items():
            opts[k] = v
        self.seriesModified(True)
                
        print("Running predictions...")

        zarr_datasets = predict(
            sources=[(data_fp, "raw")],
            out_file=data_fp,
            checkpoint_path=cp_path,
            model_path=model_path,
            write=write_opts,
            increase=increase,
            downsample=downsample,
            full_out_roi=full_out_roi
        )

        # display the affinities
        self.setZarrLayer(data_fp)
        for zg in os.listdir(data_fp):
            if zg.startswith("pred_affs"):
                self.setLayerGroup(zg)
                break

        print("Predictions done.")
        
    def segment(self, data_fp : str = None):
        """Run an autosegmentation.
        
            Params:
                data_fp (str): the filepath for the zarr
        """
        self.saveAllData()
        self.removeZarrLayer()

        print("Importing modules...")
        
        from autoseg import hierarchical

        opts = self.series.options["autoseg"]

        response, dialog_confirmed = SegmentDialog(self, opts).exec()

        if not dialog_confirmed: return

        data_fp, thresholds, downsample, norm_preds, min_seed, merge_fun = response

        segment_opts = {
            "zarr_current": data_fp,
            "thresholds": thresholds,
            "downsample_int": downsample,
            "norm_preds": norm_preds,
            "min_seed": min_seed,
            "merge_fun": merge_fun
        }

        for k, v in segment_opts.items():
            opts[k] = v
        self.seriesModified(True)

        print("Running hierarchical...")

        dataset = None
        for d in os.listdir(data_fp):
            if "affs" in d:
                dataset = d
                break

        print("Segmentation started...")
            
        hierarchical.run(
            data_fp,
            dataset,
            thresholds=list(sorted(thresholds)),
            normalize_preds=norm_preds,
            min_seed_distance=min_seed,
            merge_function=merge_fun
        )

        print("Segmentation done.")

        # display the segmetnation
        self.setZarrLayer(data_fp)
        for zg in os.listdir(data_fp):
            if zg.startswith("seg"):
                self.setLayerGroup(zg)
                break
    
    def importLabels(self, all=False):
        """Import labels from a zarr."""
        if not self.field.zarr_layer or not self.field.zarr_layer.is_labels:
            return
        
        # get necessary data
        data_fp = self.series.zarr_overlay_fp
        group_name = self.series.zarr_overlay_group

        labels = None if all else self.field.zarr_layer.selected_ids
        
        labelsToObjects(
            self.series,
            data_fp,
            group_name,
            labels
        )
        self.field.reload()
        self.removeZarrLayer()

        if self.field.obj_table_manager:
            self.field.obj_table_manager.refresh()
    
    def mergeLabels(self):
        """Merge selected labels in a zarr."""
        if not self.field.zarr_layer:
            return
        
        self.field.zarr_layer.mergeLabels()
        self.field.generateView()
    
    def mergeObjects(self, new_name=None):
        """Merge full objects across the series.
        
            Params:
                new_name (str): the new name for the merged objects
        """            
        names = set()
        for trace in self.field.section.selected_traces:
            names.add(trace.name)
        names = list(names)
        
        if not new_name:
            new_name, confirmed = QInputDialog.getText(
                self,
                "Object Name",
                "Enter the desired name for the merged object:",
                text=names[0]
            )
            if not confirmed or not new_name:
                return
        
        self.series.mergeObjects(names, new_name)
        self.field.reload()

    def restart(self):
        self.restart_mainwindow = True

        # Clear console
        
        if os.name == 'nt':  # Windows
            _ = os.system('cls')
        
        else:  # Mac and Linux
            _ = os.system('clear')
        
        self.close()
            
    def closeEvent(self, event):
        """Save all data to files when the user exits."""
        if self.series.options["autosave"]:
            self.saveToJser(close=True)
        else:
            response = self.saveToJser(notify=True, close=True)
            if response == "cancel":
                event.ignore()
                return
        event.accept()
