# -*- coding: utf-8 -*-
"""
/***************************************************************************
 HeatMap_PointExtracter
                                 A QGIS plugin
 This Plugin extracts Points of high Point density
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-11-18
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Ben Everad / Endura kommunal
        email                : ben@everad.lu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction,QTableWidgetItem
from qgis.core import QgsProject, QgsCoordinateTransform, QgsVectorLayer, QgsFeature

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .heatPointExtracter_dialog import HeatMap_PointExtracterDialog
import os.path


class HeatMap_PointExtracter:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'HeatMap_PointExtracter_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Heatpoint')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('HeatMap_PointExtracter', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/heatPointExtracter/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'HeatPoint Extracter'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Heatpoint'),
                action)
            self.iface.removeToolBarIcon(action)


    def loadColumn(self):
        self.layerstor.pnktlyr = QgsProject.instance().mapLayersByName(self.dlg.pnktlyr_cb.currentText())[0]
        dest_crs = QgsProject.instance().crs()
        src_crs = self.layerstor.pnktlyr.crs()
        xform = QgsCoordinateTransform(src_crs, dest_crs, QgsProject.instance())
        i = 1
        #templayer with fields
        self.layerstor.temppnktlyr = QgsVectorLayer('Point?crs=%s' % dest_crs.authid(), 'temp', 'memory')
        tempprovider = self.layerstor.temppnktlyr.dataProvider()
        tempprovider.addAttributes(self.layerstor.pnktlyr.fields())
        self.layerstor.temppnktlyr.updateFields()
        self.layerstor.temppnktlyr.startEditing()
        i=0
        for feature in self.layerstor.pnktlyr.getFeatures():
            g = feature.geometry()
            g.transform(xform)
            feature.setGeometry(g)
            nwFeature = QgsFeature()
            nwFeature.setAttributes(feature.attributes())
            nwFeature.setGeometry(g)
            self.layerstor.temppnktlyr.addFeature(nwFeature)
            
        self.layerstor.temppnktlyr.commitChanges()
        self.layerstor.temppnktlyr.updateExtents()
        print(self.layerstor.temppnktlyr.extent())
        print(len([f for f in self.layerstor.temppnktlyr.getFeatures()]))
        
        #print(self.iface.mapCanvas().extent())
        self.dlg.flds_cb.currentIndexChanged.disconnect()
        self.dlg.flds_cb.clear()
        self.dlg.flds_cb.addItems([""]+[field.name() for field in self.layerstor.temppnktlyr.fields()])
        self.dlg.flds_cb.currentIndexChanged.connect(self.loadAttributes)
        QgsProject.instance().addMapLayer(self.layerstor.temppnktlyr)


    def loadAttributes(self):
        field = self.dlg.flds_cb.currentText()
        fieldslist = []
        currentExtent = self.iface.mapCanvas().extent()

        print(self.iface.mapCanvas().extent())
        i = 0
        for feature in self.layerstor.temppnktlyr.getFeatures():
            i=i+1
            if currentExtent.contains(feature.geometry().asPoint()):
                if feature[field] not in fieldslist:
                    fieldslist.append(feature[field])
                i = i+1
            # if i == 30:
            #     break
            # if feature[field] not in fieldslist:
            #     fieldslist.append(feature[field])
        print(fieldslist)
        fieldslist.sort()
        self.dlg.attribute_tw.setColumnCount(2)
        self.dlg.attribute_tw.setRowCount(len(fieldslist)+1)
        self.dlg.attribute_tw.setItem(0,0,QTableWidgetItem("Attribute"))
        for r, attr in enumerate(fieldslist):
            itm = QTableWidgetItem(attr)
            itm.setFlags(Qt.ItemIsEnabled)
            self.dlg.attribute_tw.setItem(r+1,0,itm)
            self.dlg.attribute_tw.setItem(r+1,1,QTableWidgetItem("1"))
        

    def run(self):
        """Run method that performs all the real work"""
        class layerstorage():
            name = "test"
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = HeatMap_PointExtracterDialog()

        self.dlg.title.setText("Git import_function")

        layerlist = QgsProject.instance().mapLayers().values()
        self.dlg.pnktlyr_cb.clear()
        self.dlg.pnktlyr_cb.addItems([lay.name() for lay in layerlist])

        self.dlg.pnktlyr_cb.currentIndexChanged.connect(self.loadColumn)
        self.dlg.flds_cb.currentIndexChanged.connect(self.loadAttributes)
        
        self.layerstor = layerstorage()
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
