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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem, QDialog, QPushButton, QComboBox, QListWidget
from qgis.core import QgsProject, QgsCoordinateTransform, QgsVectorLayer, QgsFeature, QgsPointXY, QgsGeometry, QgsRectangle, QgsField, QgsVectorLayerUtils
import numpy as np
import time
import pandas as pd

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

    def pnkt_lyr_in_extent(self):
        self.layerstor.pnktlyr = QgsProject.instance().mapLayersByName(self.dlg.pnktlyr_cb.currentText())[0]
        self.crsstor.dest_crs = QgsProject.instance().crs()
        self.crsstor.src_crs = self.layerstor.pnktlyr.crs()
        xform = QgsCoordinateTransform(self.crsstor.src_crs, self.crsstor.dest_crs, QgsProject.instance())
        currentExtent = self.iface.mapCanvas().extent()
        #templayer with fields
        self.layerstor.punktlyr_in_extent = QgsVectorLayer('Point?crs=%s' % self.crsstor.dest_crs.authid(), 'lyr_in_extent', 'memory')
        tempprovider = self.layerstor.punktlyr_in_extent.dataProvider()
        tempprovider.addAttributes(self.layerstor.pnktlyr.fields())
        self.layerstor.punktlyr_in_extent.updateFields()
        self.layerstor.punktlyr_in_extent.startEditing()
        for feature in self.layerstor.pnktlyr.getFeatures():
            g = feature.geometry()
            g.transform(xform)
            if currentExtent.contains(g.asPoint()):
                feature.setGeometry(g)
                nwFeature = QgsFeature()
                nwFeature.setAttributes(feature.attributes())
                nwFeature.setGeometry(g)
                self.layerstor.punktlyr_in_extent.addFeature(nwFeature)
            
        self.layerstor.punktlyr_in_extent.commitChanges()
        self.layerstor.punktlyr_in_extent.updateExtents()
        if self.show_zwischenergenisse:
            QgsProject.instance().addMapLayer(self.layerstor.punktlyr_in_extent)


    def loadColumn(self):
        if self.dlg.pnktlyr_cb.currentText() =="":
            self.table.clear()
            self.dlg.flds_cb.currentIndexChanged.disconnect()
            self.dlg.flds_cb.clear()
            self.dlg.flds_cb.currentIndexChanged.connect(self.loadAttributes)
            return()
        self.pnkt_lyr_in_extent()
        #print(self.iface.mapCanvas().extent())
        self.dlg.flds_cb.currentIndexChanged.disconnect()
        self.dlg.flds_cb.clear()
        self.dlg.flds_cb.addItems([""]+[field.name() for field in self.layerstor.punktlyr_in_extent.fields()])
        self.dlg.flds_cb.currentIndexChanged.connect(self.loadAttributes)

    def createRasterPoints(self, rectangle, dist):
        height = rectangle.height()
        width = rectangle.width()
        nheight = int(height/dist)
        rectlist_factor = 30
        nRectHeight = int(height/(dist*rectlist_factor))
        nwidth = int(width/dist)
        nRectWidth = int(width/(dist*rectlist_factor))
        self.layerstor.temprasterpunktlyr = QgsVectorLayer('Point?crs=%s' % self.crsstor.dest_crs.authid(), 'rastertemp', 'memory')
        tempprovider = self.layerstor.temprasterpunktlyr.dataProvider()
        self.layerstor.temprasterpunktlyr.startEditing()
        tempprovider.addAttributes([QgsField("score",QVariant.Double, "double", 10, 3)])
        #self.layerstor.temprasterpunktlyr.updateFields()
        #self.layerstor.temprasterpunktlyr.startEditing()
        xmin = rectangle.xMinimum()
        ymin = rectangle.yMinimum()
        for xn in range(nwidth+1):
            for yn in range(nheight+1):
                nwFeature = QgsFeature()
                nwFeature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(xn*dist+xmin,yn*dist+ymin)))
                self.layerstor.temprasterpunktlyr.addFeature(nwFeature)
        self.layerstor.temprasterpunktlyr.commitChanges()
        self.layerstor.temprasterpunktlyr.updateExtents()
        if self.show_zwischenergenisse:
            QgsProject.instance().addMapLayer(self.layerstor.temprasterpunktlyr)
        # creating rectangles for better/faster calculation
        rectlist = []
        for xn in range(nRectWidth+1):
            for yn in range(nRectHeight+1):
                point_min=QgsPointXY(xn*dist*rectlist_factor+xmin,yn*dist*rectlist_factor+ymin)
                point_max=QgsPointXY((xn+1)*dist*rectlist_factor+xmin,(yn+1)*dist*rectlist_factor+ymin)
                rectlist.append(QgsRectangle(point_min,point_max))
        self.rectlist=rectlist

    def plusclicked(self):
        self.lv.fill()
        pass

    def minusclicked(self):
        print("miunss")
        print(self.table.tablewidget.selectedIndexes())
        print(self.table.tablewidget.selectedItems())
        to_del = []
        for ind in self.table.tablewidget.selectedIndexes():
            to_del.append(ind.row()-1)
            print(ind.row())
        to_del.sort(reverse=True)
        self.table.minus(to_del)

    def loadAttributes(self):
        field = self.dlg.flds_cb.currentText()
        fieldslist = []
        for feature in self.layerstor.punktlyr_in_extent.getFeatures():
            if feature[field] not in fieldslist:
                fieldslist.append(feature[field])
        fieldslist.sort()
        self.table.firstfill(fieldslist)

    def calc_charger(self):
        self.layerstor.chargerloclyr = QgsVectorLayer('Point?crs=%s' % self.crsstor.dest_crs.authid(), 'proposed Charger locations', 'memory')
        tempprovider = self.layerstor.chargerloclyr.dataProvider()
        self.layerstor.chargerloclyr.startEditing()
        tempprovider.addAttributes([QgsField("rank",QVariant.Double, "double", 10, 3)])
        self.layerstor.chargerloclyr.commitChanges()
        self.layerstor.chargerloclyr.startEditing()
        desired_n = int(self.dlg.n_charStations_le.text())
        min_distance = int(self.dlg.min_distance_le.text())
        excluded_area_list = [] # wenn ein Punkt gefunden wird, wird ein buffer mit mindest abstand drumgelegt, der kreis wird hier rein gelegt und alle punkte die in dem drin liegen , werden anschließend ignoriert
        class p_feature():
            def __init__(self,feature):
                self.feature = feature
            def __lt__(self, other):
                return(self.feature["score"] < other.feature["score"])
        feature_list= []
        for f in self.layerstor.temprasterpunktlyr.getFeatures():
            feature_list.append(p_feature(f))
        feature_list.sort(reverse=True)
        defined_positions =0
        for f in feature_list:
            if defined_positions == desired_n:
                break
            print([buffer.contains(f.feature.geometry().asPoint()) for buffer in excluded_area_list])
            if sum([buffer.contains(f.feature.geometry().asPoint()) for buffer in excluded_area_list]) ==0:
                defined_positions +=1
                excluded_area_list.append(f.feature.geometry().buffer(min_distance,-1))
                nwFeature = QgsVectorLayerUtils.createFeature(self.layerstor.chargerloclyr)
                nwFeature.setGeometry(f.feature.geometry())
                nwFeature["rank"] = defined_positions
                self.layerstor.chargerloclyr.addFeature(nwFeature)
        self.layerstor.chargerloclyr.commitChanges()
        self.layerstor.chargerloclyr.updateExtents()
        QgsProject.instance().addMapLayer(self.layerstor.chargerloclyr)


    def calc(self):
        selectedColumn = self.dlg.flds_cb.currentText()
        print(selectedColumn)
        print(selectedColumn=="")
        
        distance = int(self.dlg.heat_raster_le.text())
        currentExtent = self.iface.mapCanvas().extent()
        self.createRasterPoints(currentExtent, distance)
        min_distance = int(self.dlg.min_distance_le.text())
        observed_distance = 1.5*min_distance
        #for everyrasterpoints create buffer double min_distance
        start_time = time.time()
        i=0
        self.layerstor.temprasterpunktlyr.startEditing()
        dataProvider = self.layerstor.temprasterpunktlyr.dataProvider()
        print(len(self.rectlist))
        for rect in self.rectlist:
            print(len([point for point in self.layerstor.temprasterpunktlyr.getFeatures() if rect.contains(point.geometry().asPoint())]))
            print(len([point for point in self.layerstor.punktlyr_in_extent.getFeatures() if rect.buffered(observed_distance).contains(point.geometry().asPoint())]))
            for rasterpoint in [point for point in self.layerstor.temprasterpunktlyr.getFeatures() if rect.contains(point.geometry().asPoint())]:
                value = 0.0
                for poipoint in [point for point in self.layerstor.punktlyr_in_extent.getFeatures() if rect.buffered(observed_distance).contains(point.geometry().asPoint())]:
                    if selectedColumn=="":
                        diff = observed_distance - poipoint.geometry().distance(rasterpoint.geometry())
                        if diff > 0:
                            value+=diff
                    else:
                        if poipoint[selectedColumn] in self.table.list_arg():
                            diff = observed_distance - poipoint.geometry().distance(rasterpoint.geometry())
                            if diff > 0:
                                value+=diff*self.table.arg_value(poipoint[selectedColumn])
                                self.table.arg_value(poipoint[selectedColumn])

                dataProvider.changeAttributeValues({rasterpoint.id():{0:value/observed_distance}})


            # for rPoint in self.layerstor.temprasterpunktlyr.getFeatures():
            #     buff=rPoint.geometry().buffer(3*min_distance,10)
            #     i+=1
            #     for poi in self.layerstor.punktlyr_in_extent.getFeatures():
            #         print(buff.contains(poi.geometry().asPoint()))
            #break
        self.layerstor.temprasterpunktlyr.commitChanges()
        end_time = time.time()
        print("total time taken this loop: ", end_time - start_time)
        print("for %s points" %str(i))
        self.dlg.n_charStations_le.setEnabled(True)
        self.dlg.calc_charger_pb.setEnabled(True)


    def attribute_select_state_changed(self):
        self.show_attribute_select(self.dlg.attribute_select_cb.checkState())

    def zwischenergebnisse_state_changed(self):
        self.show_zwischenergenisse = not self.show_zwischenergenisse

    def wertigkeit_state_changed(self):
        self.show_wertigkeit(self.dlg.wertigkeit_cb.checkState()/2) #div 2 because wertigkeit combobox gives 2 or 0 is no bool 1 or 0 is
        print("checkState")
        print(self.dlg.wertigkeit_cb.checkState()/2==True)

    def show_wertigkeit(self,state):
        self.table.show_wertigkeit(state)

    
    def show_attribute_select(self,state):
        if state: #if selected
            self.dlg.attribute_tw.setVisible(True)
            self.dlg.plusminuswidget.setVisible(True)
            self.dlg.label_spalte_Selektion.setVisible(True)
            self.dlg.flds_cb.setVisible(True)
            self.dlg.wertigkeit_cb.setVisible(True)
            self.dlg.setMinimumHeight(800)
            self.dlg.resize(705,800)
        else:
            self.dlg.attribute_tw.setHidden(True)
            self.dlg.plusminuswidget.setHidden(True)
            self.dlg.label_spalte_Selektion.setHidden(True)
            self.dlg.flds_cb.setHidden(True)
            self.dlg.wertigkeit_cb.setHidden(True)
            self.dlg.setMinimumHeight(370)
            self.dlg.resize(705,370)
        

    def run(self):
        """Run method that performs all the real work"""
        class layerstorage():
            name = "class"
        class crsstorage():
            name = "class"

        class listview(QDialog):
            name="class"
            def __init__(self,table):
                super().__init__()
                self.table = table
                self.title="Hinzufügen"
                self.top=600
                self.left=200
                self.width=350
                self.height=450

                self.initWindow()

            def initWindow(self):
                self.addButton=QPushButton("Hinzufügen", self)
                self.closeButton=QPushButton("Schließen", self)
                self.listWidget=QListWidget(self)
                self.listWidget.move(50,50)
                self.listWidget.resize(250,350)
                self.addButton.move(100,410)
                self.addButton.clicked.connect(self.add)
                self.closeButton.move(220,410)
                self.closeButton.clicked.connect(self.closing)

                self.setWindowTitle(self.title)
                self.setGeometry(self.top, self.left, self.width, self.height)
            
            def fill(self):
                self.listWidget.clear()
                if self.table.missingattr !=[]:
                    self.listWidget.addItems(self.table.missingattr)
                self.show()

            def add(self):
                print([li.text() for li in self.listWidget.selectedItems()])
                self.table.add([li.text() for li in self.listWidget.selectedItems()])
                self.fill()
                print("ok")

            def closing(self):
                self.close()

        class tableview():
            def __init__(self,tablewidget):
                self.tablewidget = tablewidget
                self.tablewidget.setColumnCount(2)
                self.missingattr = []
                #self.tablewidget.setColumnWidth(0,int(self.tablewidget.width()*0.75))
                #self.tablewidget.setColumnWidth(1,int(self.tablewidget.width()*0.35))
                self.tablewidget.itemChanged.connect(self.savetable)
                self.if_show_wertigkeit = False
                self.firstfill_happend = False
                
            def firstfill(self,fieldlist):
                self.fieldlist = fieldlist
                self.table = pd.DataFrame({"Attribute":self.fieldlist, "Wertigkeit":[1]*len(self.fieldlist)})
                self.missingattr.clear()
                self.firstfill_happend = True
                self.show_wertigkeit(False)
            
            def clear(self):
                self.tablewidget.itemChanged.disconnect()
                self.tablewidget.clear()
                self.tablewidget.itemChanged.connect(self.savetable)

            def list_arg(self):
                return(list(self.table["Attribute"]))
            
            def arg_value(self,arg):
                return(float(self.table[self.table["Attribute"] == arg]["Wertigkeit"]))

            def show_wertigkeit(self,state):
                self.if_show_wertigkeit = state
                if self.firstfill_happend:
                    if self.if_show_wertigkeit:
                        self.tablewidget.setColumnWidth(0,int(self.tablewidget.width()*0.63))
                        self.tablewidget.setColumnWidth(1,int(self.tablewidget.width()*0.30))
                    else:
                        self.tablewidget.setColumnWidth(0,int(self.tablewidget.width()*0.830))
                        self.tablewidget.setColumnWidth(1,int(self.tablewidget.width()*0.03))
                        self.table["Wertigkeit"].values[:] = 1
                    self.loadtable()

            def loadtable(self):
                self.tablewidget.itemChanged.disconnect()
                self.tablewidget.clear()
                self.tablewidget.setRowCount(len(self.table)+1)
                self.table = self.table.sort_values(by="Attribute")
                for coln, colname in enumerate(self.table.columns):
                    if coln ==0 or self.if_show_wertigkeit == True:
                        itm = QTableWidgetItem(colname)
                        itm.setFlags(Qt.ItemIsEnabled)
                        self.tablewidget.setItem(0,coln,itm)

                for r, attr in enumerate(self.table["Attribute"].tolist()):
                    wert = self.table["Wertigkeit"].tolist()[r]
                    itm = QTableWidgetItem(attr)
                    itm.setFlags(Qt.ItemIsEnabled) # cann't be changed
                    itm.setFlags(Qt.ItemIsSelectable)
                    self.tablewidget.setItem(r+1,0,itm)
                    # print("if_show_wertigkeit")
                    # print(self.if_show_wertigkeit)
                    if self.if_show_wertigkeit == True:
                        self.tablewidget.setItem(r+1,1,QTableWidgetItem(str(wert)))
                self.tablewidget.itemChanged.connect(self.savetable)
            
            def minus(self,to_del):
                self.missingattr += [self.table["Attribute"].tolist()[i] for i in to_del]
                self.missingattr.sort()
                #print(self.missingattr)
                self.table = self.table.drop([self.table.index[i] for i in to_del])
                self.loadtable()
            
            def add(self,to_add):
                for li in to_add:
                    print(li)
                    self.table = self.table.append({"Attribute":li,"Wertigkeit":1}, ignore_index=True)
                    self.missingattr.pop(self.missingattr.index(li))
                self.loadtable()

            def savetable(self,item):
                attr=self.tablewidget.item(item.row(),0).text()
                self.table.loc[self.table["Attribute"]==attr,"Wertigkeit"] = int(item.text())
                self.loadtable()
            
        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = HeatMap_PointExtracterDialog()

        self.dlg.title.setText("Git import_function")

        layerlist = QgsProject.instance().mapLayers().values()
        self.dlg.pnktlyr_cb.clear()
        self.dlg.pnktlyr_cb.addItems([""]+[lay.name() for lay in layerlist])

        self.dlg.pnktlyr_cb.currentIndexChanged.connect(self.loadColumn)
        self.dlg.flds_cb.currentIndexChanged.connect(self.loadAttributes)
        self.dlg.run_pb.clicked.connect(self.calc)
        self.dlg.plus_pb.clicked.connect(self.plusclicked)
        self.dlg.minus_pb.clicked.connect(self.minusclicked)
        self.dlg.attribute_select_cb.stateChanged.connect(self.attribute_select_state_changed)
        self.dlg.zwischenergebnisse_cb.stateChanged.connect(self.zwischenergebnisse_state_changed)
        self.dlg.wertigkeit_cb.stateChanged.connect(self.wertigkeit_state_changed)
        self.dlg.calc_charger_pb.clicked.connect(self.calc_charger)
        self.layerstor = layerstorage()
        self.crsstor = crsstorage()
        self.table = tableview(self.dlg.attribute_tw)
        self.lv = listview(self.table)
        self.show_attribute_select(False)
        
        self.show_zwischenergenisse = False
        #deactivate chargercalc-dialog until Things are calculated
        self.dlg.n_charStations_le.setEnabled(False)
        self.dlg.calc_charger_pb.setEnabled(False)

        self.dlg.heat_raster_le.setText("20")
        self.dlg.min_distance_le.setText("100")
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
