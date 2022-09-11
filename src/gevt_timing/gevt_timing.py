# -*- coding: utf-8 -*-
"""
Created on Mon Sep 24 21:50:38 2018

@author: Sébastien Weber
"""
import sys
import os
from pathlib import Path
import requests

from gpxpy import gpx
path_here = os.path.split(__file__)[0]
sys.path.append(path_here)

from qtpy import QtWidgets, QtCore, QtGui
from qtpy.QtCore import Signal, Slot
from pymodaq.daq_utils.gui_utils import DockArea
from pymodaq.daq_utils import daq_utils as utils
from pymodaq.daq_utils.parameter import pymodaq_ptypes
import json
import datetime
from pymodaq.resources.QtDesigner_Ressources import QtDesigner_ressources_rc
from pymodaq.daq_utils import config
from pymodaq.daq_utils.exceptions import ActuatorError
from pymodaq.daq_utils.messenger import deprecation_msg


# local_path = config.get_set_local_dir('gevt_dir')
# sys.path.append(local_path)
# logger = utils.set_logger('gevt_timing', add_handler=True, base_logger=True, logger_base_name='gevt',
#                           local_dir='gevt_dir')
#

def request_umap(umap_code):
    r = requests.get(f'https://umap.openstreetmap.fr/fr/map/{umap_code}/geojson/')
    r_dict = r.json()
    assert r_dict['properties']['umap_id'] == umap_code
    name = r_dict['properties']['name']
    layers = [(layer['name'], layer['id']) for layer in r_dict['properties']['datalayers']]
    layers.sort(key=lambda x: x[0].lower())
    
    return name, layers


def request_layer(layer_id, gpx_obj: gpx.GPX):
    r = requests.get(f'https://umap.openstreetmap.fr/fr/datalayer/{layer_id}/')
    r_dict = r.json()
    assert r_dict['_umap_options']['id'] == layer_id
    features = r_dict['features']

    for feature in features:
        if 'name' in feature['properties']:
            name = feature['properties']['name']
        else:
            name = ''
        if 'description' in feature['properties']:
            description = feature['properties']['description']
        else:
            description = ''
            
        if feature['geometry']['type'] == 'MultiLineString':
            # Create first track in our GPX:
            gpx_track = gpx.GPXTrack(name, description)
            gpx_obj.tracks.append(gpx_track)
            for segment in feature['geometry']['coordinates']:
                # Create first segment in our GPX track:
                gpx_segment = gpx.GPXTrackSegment()
                gpx_track.segments.append(gpx_segment)
                for coordinates in segment:
                    gpx_segment.points.append(gpx.GPXTrackPoint(*coordinates))
        elif feature['geometry']['type'] == 'LineString':
            gpx_track = gpx.GPXTrack(name, description)
            gpx_obj.tracks.append(gpx_track)
            gpx_segment = gpx.GPXTrackSegment()
            gpx_track.segments.append(gpx_segment)
            segment = feature['geometry']['coordinates']
            for coordinates in segment:
                gpx_segment.points.append(gpx.GPXTrackPoint(*coordinates))
        elif feature['geometry']['type'] == 'Point':
            gpx_obj.waypoints.append(gpx.GPXWaypoint(*feature['geometry']['coordinates'],
                                                     name=name, description=description))



class GevtTiming(QtCore.QObject):
    """

    """
    def __init__(self, mainwindow):
        super().__init__()


        self.mainwindow = mainwindow
        self.area = DockArea()
        self.mainwindow.setCentralWidget(self.area)
        self.mainwindow.closing.connect(self.do_stuff_before_closing)

        self.setup_ui()

    def do_stuff_before_closing(self,event):
        if self.h5file.isopen:
            self.h5file.flush()
            self.h5file.close()
        event.setAccepted(True)

    def quit(self):
        if self.h5file.isopen:
            self.h5file.close()

        self.mainwindow.close()



class MyMainWindow(QtWidgets.QMainWindow):
    closing = Signal(QtGui.QCloseEvent)

    def __init__(self):
        super(MyMainWindow, self).__init__()

    def closeEvent(self, event):
        self.closing.emit(event)


def start():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = MyMainWindow()

    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    
    name, layers = request_umap(726243)
    gpx_obj = gpx.GPX()
    for layer, id in layers:
        request_layer(id, gpx_obj)

    pass
