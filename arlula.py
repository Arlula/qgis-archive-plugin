# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Arlula
                                 A QGIS plugin
 arlula
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-06-01
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Arlula
        email                : adamhammo99@gmail.com
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
# imports
from .resources import *
from .arlula_dialog import ArlulaDialog
from qgis.PyQt.QtWidgets import QAction, QTableWidgetItem
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, QFileInfo, QDir, QDate
from qgis.core import QgsMessageLog, QgsProject, QgsRasterLayer
from pyproj import Proj, transform
import os
import sys
import shutil
import platform
from io import BytesIO
import json
import arlulacore
import PIL.Image
import requests

py_version = sys.version.split(' ')[0]
os_version = platform.platform()
def_ua = "qgis-plugin " + '1.0.0' + " python " + py_version + " OS " + os_version

# Default message to display on GUI
DEFAULT_STATUS = "No pending requests"

# filetypes that can be added to QGIS as a layer
VALID_LAYERS = ["img_tiff"]

class Arlula:
    """QGIS Plugin Implementation."""

    # Set global variables for the package
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
            'Arlula_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&arlula')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        ### Set GUI vars and defaults ###
        # Global
        self.tab = 0
        self.tabs = ['Search', 'Order imagery', 'Get resource']
        
        # Search form
        self.start_date = QDate(2021,1,1)
        self.end_date = QDate(2021,1,1)
        self.res = 'vhigh'
        self.lat = -33.87
        self.long = 151.21
        self.south = -33.87
        self.east = 151.21
        self.north = -33.87
        self.west = 151.21
        self.key = None
        self.secret = None
        self.resmap = {
            'Very High (<0.5m)': 'vhigh',
            'High (0.5m-1m)': 'high',
            'Medium (1m-5m)': 'med',
            'Low (5m-20m)': 'low',
            'Very Low (>20m)': 'vlow'
        }
        self.search_results = []
        
        # Get resource
        self.files = []
        self.coords = True
        self.box = False
        self.orders = []
        self.selected_orders = []
        self.resources = []
        self.selected_resources = []
        self.download_folder = QFileInfo(QgsProject.instance().fileName()).dir().absolutePath()
        self.add_resource = False
        
        # Order imagery
        self.webhook = None
        self.email = None
        self.webhooks = []
        self.emails = []
        self.seats = 1
        self.eula = False
        self.price = 0
        
        # Finally change directory to the plugin folder for downloads
        os.chdir(self.plugin_dir)

    ### Default initialisation functions ###

    # noinspection PyMethodMayBeStatic [UNUSED]
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Arlula', message)

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

        icon_path = ':/plugins/arlula/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Arlula'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&arlula'),
                action)
            self.iface.removeToolBarIcon(action)

        for f in self.files:
            os.remove(f)

    ### Search functionality ###

    def search(self):
        # Interact with GUI
        QgsMessageLog.logMessage('Changing button', 'Arlula')
        self.dlg.searchButton.setText("Loading...")
        self.dlg.searchButton.setEnabled(False)
        self.dlg.resultTable.setRowCount(0)
        self.dlg.status.setText("Searching the Arlula archive...")

        # Force GUI to refresh
        QCoreApplication.processEvents()

        QgsMessageLog.logMessage('Searching', 'Arlula')
        
        # Query the Arlula API
        arlula_session = arlulacore.Session(self.key, self.secret, user_agent=def_ua)
        if self.coords:
            res = arlulacore.Archive(arlula_session).search(
                start=self.start_date.toString('yyyy-MM-dd'),
                end=self.end_date.toString('yyyy-MM-dd'),
                res=self.res,
                lat=self.lat,
                long=self.long
            )
            QgsMessageLog.logMessage(str(self.lat), 'Arlula')
            QgsMessageLog.logMessage(str(self.long), 'Arlula')
        elif self.box:
            res = arlulacore.Archive(arlula_session).search(
                start=self.start_date.toString('yyyy-MM-dd'),
                end=self.end_date.toString('yyyy-MM-dd'),
                res=self.res,
                south=self.south,
                north=self.north,
                east=self.east,
                west=self.west
            )
            QgsMessageLog.logMessage(str(self.north), 'Arlula')
            QgsMessageLog.logMessage(str(self.south), 'Arlula')
            QgsMessageLog.logMessage(str(self.east), 'Arlula')
            QgsMessageLog.logMessage(str(self.west), 'Arlula')
        QgsMessageLog.logMessage("Found {} results".format(len(res)), 'Arlula')
        
        # Populate the table
        self.search_results = res
        for row in res:
            n = self.dlg.resultTable.rowCount()
            self.dlg.resultTable.insertRow(n)
            self.dlg.resultTable.setItem(n, 0, QTableWidgetItem(row.supplier))
            self.dlg.resultTable.setItem(n, 1, QTableWidgetItem(row.date[:10]))
            self.dlg.resultTable.setItem(
                n, 2, QTableWidgetItem(str(row.resolution)))
            self.dlg.resultTable.setItem(n, 3, QTableWidgetItem(
                str(row.area)))
            self.dlg.resultTable.setItem(
                n, 4, QTableWidgetItem("$"+str(row.price.base/100)))
            self.dlg.resultTable.setItem(
                n, 5, QTableWidgetItem(str(row.cloud)+"%"))
            self.dlg.resultTable.setItem(n, 6, QTableWidgetItem(row.thumbnail))
            self.dlg.resultTable.setItem(
                n, 7, QTableWidgetItem(json.dumps(row.bounding)))
            self.dlg.resultTable.setItem(n, 8, QTableWidgetItem("Add layer"))
            self.dlg.resultTable.setItem(n, 9, QTableWidgetItem("Place order"))

        # Reset the GUI
        self.dlg.searchButton.setText("Search")
        self.dlg.status.setText(DEFAULT_STATUS)
        self.dlg.searchButton.setEnabled(True)

    # Function to add thumbnail jpg to qgis layers
    def add_layer(self, item):
        self.dlg.status.setText("Adding thumbnail layer...")
        QCoreApplication.processEvents()
        
        # Get the thumbnail url and specify filenames
        url = self.dlg.resultTable.item(item.row(), 6).text()
        imgname = url.split('/')[-1].split('=')[-1].split('.')[0]
        tfpath = imgname + '-converted.tiff'
        lypath = imgname + '-geo.tiff'
        self.files.append(tfpath)
        self.files.append(lypath)
        QgsMessageLog.logMessage(url, 'Arlula')
        
        # Get the JPG thumbnail and save it down as TIFF
        r = requests.get(url)
        img = PIL.Image.open(BytesIO(r.content))
        img.save(tfpath)

        # Find corner coordinates of thumbnail
        bounding = json.loads(self.dlg.resultTable.item(item.row(), 7).text())
        left = bounding[0][1]
        right = bounding[0][1]
        top = bounding[0][0]
        bottom = bounding[0][0]
        for coord in bounding:
            if coord[1] < left:
                left = coord[1]
            elif coord[1] > right:
                right = coord[1]
            if coord[0] < bottom:
                bottom = coord[0]
            elif coord[0] > top:
                top = coord[0]

        # Add coordinates to TIFF metadata
        call = f'gdal_translate -of GTiff -a_ullr {left} {top} {right} {bottom} -a_srs EPSG:4326 {tfpath} {lypath}'
        QgsMessageLog.logMessage('Executing {}'.format(call), 'Arlula')
        os.system(call)

        # Add TIFF to layers
        rlayer = QgsRasterLayer(lypath, imgname)

        QgsProject.instance().addMapLayer(rlayer)
        self.dlg.status.setText(DEFAULT_STATUS)


    def table_click_handler(self, val):
        # Function to handle clicking of the search results table
        if val.column() == 8:
            self.add_layer(val)
        elif val.column() == 9:
            self.render_order_tab(val)

    ### Get resource functionality ###

    def list_orders(self):
        # Function to list available orders
        self.dlg.status.setText("Retrieving account orders...")
        self.dlg.orderList.clear()
        QCoreApplication.processEvents()
        QgsMessageLog.logMessage('Listing orders', 'Arlula')
        
        # Query API
        arlula_session = arlulacore.Session(self.key, self.secret, user_agent=def_ua)
        self.orders = arlulacore.Orders(arlula_session).list()
        
        # Populate GUI list
        for i,order in enumerate(self.orders):
            self.dlg.orderList.insertItem(i, f"{order.id} {order.supplier} {order.status}")
        self.dlg.status.setText(DEFAULT_STATUS)
    
    def list_resources(self):
        # Function to list available resources from one selected orders
        QgsMessageLog.logMessage('Listing resources', 'Arlula')
        self.resources = []
        self.dlg.resourceList.clear()
        
        # Get resources from API and place in a list
        arlula_session = arlulacore.Session(self.key, self.secret, user_agent=def_ua)
        for order in self.selected_orders:
            order_id = order.text().split(' ')[0]
            self.dlg.status.setText(f"Retrieving resources for order {order_id}...")
            QCoreApplication.processEvents()
            self.dlg.orderLabel.setText(order_id)
            order_details = arlulacore.Orders(arlula_session).get(id=order_id)
            for x in order_details.resources :
                self.resources.append(x)
                
        # Populate GUI list
        for i,r in enumerate(self.resources):
            self.dlg.resourceList.insertItem(i, f"{r.type} {r.name}")
        self.dlg.status.setText(DEFAULT_STATUS)

    def progress_callback(self):
        # A generator to pass to the download helper
        # Allows for download progress bar to update
        while True :
            progress = yield
            if progress is None :
                progress = 0
                
            # Set the progress bar and update the GUI
            self.dlg.progressBar.setValue(progress*100)
            QCoreApplication.processEvents()

    def download_resources(self):
        # Function to download selected resources
        arlula_session = arlulacore.Session(self.key, self.secret, user_agent=def_ua)
        i = 1
        
        # For each resource, call the download helper
        for resource in self.selected_resources:
            pc = self.progress_callback()
            resource_id = self.resources[resource[0].row()].id
            resource_name = resource[1].text().split(' ')[1]
            resource_type = resource[1].text().split(' ')[0]
            self.dlg.status.setText(f"Downloading {resource_name} (File {i})")
            QCoreApplication.processEvents()
            arlulacore.Orders(arlula_session).get_resource(resource_id, filepath=self.download_folder+"/"+resource_name, suppress=True, progress_generator=pc)
            
            # Add as layer if valid filetype and box checked
            if resource_type in VALID_LAYERS and self.add_resource:
                rlayer = QgsRasterLayer(self.download_folder+"/"+resource_name, resource_name)
                QgsProject.instance().addMapLayer(rlayer)
            i+=1
        self.dlg.status.setText(DEFAULT_STATUS)

    def get_resources(self):
        self.download_resources()
        
    
    ### Order functionality ###
        
    def render_order_tab(self, item):
        # Function to render the selected order
        self.current_order_details = self.search_results[item.row()]
        self.dlg.tabWidget.setCurrentIndex(1)
        
        # Set order details table
        self.dlg.imageDetails.setHtml(f"""<h6>Imagery details</h6>
                                      See the <a href="https://arlula.com/documentation/">API documentation</a> for more information on each parameter.<br/><br/>
                                      View the thumbnail <a href="{self.current_order_details.thumbnail}">here</a>.
                                      <table border='1'>
                                      <tr><th>Parameter</th><th>Value</th><tr>
                                      <tr><td>Supplier</td><td>{self.current_order_details.supplier}</td></tr>
                                      <tr><td>Date</td><td>{self.current_order_details.date}</td></tr>
                                      <tr><td>Center (long, lat)</td><td>{(self.current_order_details.center.long,self.current_order_details.center.lat)}</td></tr>
                                      <tr><td>Bounding box (long,lat)</td><td>{self.current_order_details.bounding}</td></tr>
                                      <tr><td>Area</td><td>{self.current_order_details.area}</td></tr>
                                      <tr><td>Overlap area</td><td>{self.current_order_details.overlap.area}</td></tr>
                                      <tr><td>Overlap percent</td><td>{self.current_order_details.overlap.percent}</td></tr>
                                      <tr><td>Fulfillment time</td><td>{self.current_order_details.fulfillmentTime}</td></tr>
                                      <tr><td>Resolution</td><td>{self.current_order_details.resolution}</td></tr>
                                      <tr><td>Cloud</td><td>{self.current_order_details.cloud}</td></tr>
                                      <tr><td>Annotations</td><td>{self.current_order_details.annotations}</td></tr>
                                      </table>""")
        
        # See if we need to limit the seats
        max_seats = 0
        limit_seats = True
        if self.current_order_details.price.seats != None :
            for seatrng in self.current_order_details.price.seats :
                if seatrng.max > max_seats:
                    max_seats = seatrng.max
                if seatrng.max == 0 :
                    limit_seats = False
                    
            if limit_seats:
                self.dlg.seats.setRange(1, max_seats)
            else:
                self.dlg.seats.setRange(1, 999999999)
        
        self.dlg.orderImgLabel.setText(f"Ordering scene {self.current_order_details.sceneID}")
        self.dlg.eulaLabel.setText(f"I agree to the <a href=\"{self.current_order_details.eula}\">End User Licence Agreement</a>")
        self.recalc_price()

    def order_img(self):
        # Function to submit order
        
        # Check eula compliance
        if not self.eula:
            self.dlg.status.setText("EULA must be agreed to")
            return
        
        # Submit order
        self.dlg.status.setText(f"Ordering image {self.current_order_details.id}")
        arlula_session = arlulacore.Session(self.key, self.secret, user_agent=def_ua)
        arlulacore.Archive(arlula_session).order(
            id=self.current_order_details.id,
            eula=self.current_order_details.eula,
            seats=self.seats,
            webhooks=self.webhooks,
            emails=self.emails
            )
        
        self.dlg.status.setText('Order placed')

    def recalc_price(self):
        # Recalculate the price (called on seats change)
        px_obj = self.current_order_details.price
            
        px = px_obj.base
        
        # Calc price
        if px_obj.seats != None :
            for seatrng in px_obj.seats:
                if seatrng.min <= self.seats <= seatrng.max:
                    px+=seatrng.additional
                    break
                if seatrng.min <= self.seats and seatrng.max == 0 :
                    px+=seatrng.additional
                    break
            
        # Convert from US cents to USD
        px /= 100
        
        self.dlg.price.setText(f"Price: ${round(px,2)} USD")
        
    ### Variable setter functions ###

    def change_start_date(self, val):
        self.start_date = val

    def change_end_date(self, val):
        self.end_date = val

    def change_res(self, val):
        self.res = self.resmap[val]

    def change_lat(self, val):
        self.lat = val

    def change_long(self, val):
        self.long = val

    def change_sth(self, val):
        self.south = val

    def change_nth(self, val):
        self.north = val

    def change_est(self, val):
        self.east = val

    def change_wst(self, val):
        self.west = val

    def change_key(self, val):
        self.key = val

    def change_secret(self, val):
        self.secret = val

    def toggle_coord(self):
        self.coords = not self.coords

    def toggle_box(self):
        self.box = not self.box

    def change_tab(self, ix):
        self.tab = ix
        if self.tabs[ix] == 'Get resource' :
            if self.key is not None and self.secret is not None :
                self.list_orders()

    def change_orders(self):
        self.selected_orders = self.dlg.orderList.selectedItems()
        
    def change_resources(self):
        self.selected_resources = zip(self.dlg.resourceList.selectionModel().selectedIndexes(), self.dlg.resourceList.selectedItems())

    def change_resource_folder(self, folder):
        self.download_folder = QDir(folder).absolutePath()

    def change_add_resource(self, state):
        self.add_resource = state==2

    def change_webhook(self, val):
        self.webhook = val
        
    def change_email(self, val):
        self.email = val
        
    def add_webhook(self):
        if self.webhook == '' or self.webhook is None :
            return
        self.webhooks.append(self.webhook)
        self.dlg.webhookList.insertItem(len(self.webhooks)-1, self.webhook)
        self.webhook = None
        self.dlg.webhookIn.setText('')

    def add_email(self):
        if self.email == '' or self.email is None :
            return
        self.emails.append(self.email)
        self.dlg.emailList.insertItem(len(self.emails)-1, self.email)
        self.email = None
        self.dlg.emailIn.setText('')
        
    def change_seats(self, val):
        self.seats = val
        self.recalc_price()

    def toggle_eula(self):
        self.eula = not self.eula
            
    def run(self):
        """Main function"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = ArlulaDialog()
            
            
            # Add listeners to each of the inputs

            # Search tab
            self.dlg.searchButton.clicked.connect(self.search)
            self.dlg.start_date.dateChanged.connect(self.change_start_date)
            self.dlg.end_date.dateChanged.connect(self.change_end_date)
            self.dlg.res.currentTextChanged.connect(self.change_res)
            self.dlg.lat.valueChanged.connect(self.change_lat)
            self.dlg.long_2.valueChanged.connect(self.change_long)
            self.dlg.south.valueChanged.connect(self.change_sth)
            self.dlg.north.valueChanged.connect(self.change_nth)
            self.dlg.east.valueChanged.connect(self.change_est)
            self.dlg.west.valueChanged.connect(self.change_wst)
            self.dlg.key.textChanged.connect(self.change_key)
            self.dlg.secret.textChanged.connect(self.change_secret)
            self.dlg.coord_btn.toggled.connect(self.toggle_coord)
            self.dlg.box_btn.toggled.connect(self.toggle_box)
            self.dlg.resultTable.itemClicked.connect(self.table_click_handler)
                        
            # Get resource tab
            self.dlg.tabWidget.currentChanged.connect(self.change_tab)
            self.dlg.listButton.clicked.connect(self.list_orders)
            self.dlg.orderList.itemSelectionChanged.connect(self.change_orders)
            self.dlg.selectOrder.clicked.connect(self.list_resources)
            self.dlg.resourceList.itemSelectionChanged.connect(self.change_resources)
            self.dlg.selectResource.clicked.connect(self.download_resources)
            self.dlg.resourceFolder.fileChanged.connect(self.change_resource_folder)
            self.dlg.resourceFolder.setFilePath(self.download_folder)
            self.dlg.addResource.stateChanged.connect(self.change_add_resource)
            
            # Order imagery tab
            self.dlg.webhookIn.textChanged.connect(self.change_webhook)
            self.dlg.emailIn.textChanged.connect(self.change_email)
            self.dlg.webhookAdd.clicked.connect(self.add_webhook)
            self.dlg.emailAdd.clicked.connect(self.add_email)
            self.dlg.seats.valueChanged.connect(self.change_seats)
            self.dlg.eulaAgree.toggled.connect(self.toggle_eula)
            self.dlg.sendOrder.clicked.connect(self.order_img)
            
            QgsMessageLog.logMessage(
                f'Plugin loaded in {os.getcwd()}', 'Arlula')
            QgsMessageLog.logMessage(
                f'CRS: {QgsProject.instance().crs().authid()}')

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            QgsMessageLog.logMessage('Plugin closed', 'Arlula')
