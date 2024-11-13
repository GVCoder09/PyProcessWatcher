# -*- coding: utf-8 -*-
'''
application
=======
'''

from datetime import datetime
import os
import sys

# pylint: disable=no-name-in-module
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import (QApplication,
                             QTableView,
                             QMainWindow,
                             QMenu,
                             QAction,
                             QFileDialog,
                             QMessageBox,
                             QProgressBar,
                             QLabel)
import pythoncom

from process_monitor import ProcessMonitor
from config import CONFIG


class Monitor(QThread):

    date_signal = pyqtSignal(list)

    def __init__(self, action):
        super().__init__()

        self._action = action

    def logger(self, string):
        '''Write a log string to a file.

        The file is located in the `CONFIG.DIR_LOGS` directory and is named
        'PyProcessWatcher_<current date>.txt'. If the directory does not
        exist, it will be created.

        Args:
            string (str): The string to write to the log file.
        '''

        if not os.path.exists(CONFIG.DIR_LOGS):
            os.mkdir(CONFIG.DIR_LOGS)

        with open(f'{CONFIG.DIR_LOGS}/PyProcessWatcher_{datetime.today().strftime('%d-%m-%Y')}',
                  'a', encoding='utf-8') as log:
            log.write(string+'\n')

    def run(self):
        '''
        Overriden method from QThread. Is executed when the thread is started.

        In this method, an infinite loop is used to update the ProcessMonitor
        object and send the data to the main thread. When the logging is enabled,
        the data is also written to a file.
        '''

        pythoncom.CoInitialize()  # pylint: disable=no-member

        monitor = ProcessMonitor(self._action)

        while True:
            monitor.update()

            self.date_signal.emit([monitor.timestamp,
                                   monitor.creation_date,
                                   monitor.event_type,
                                   monitor.name,
                                   monitor.executable_path,
                                   monitor.process_id,
                                   monitor.owner,
                                   monitor.privileges,
                                   monitor.handle_count,
                                   monitor.parent_process_id,
                                   monitor.thread_count])

            if CONFIG.LOGGING:
                self.logger(f'{monitor.timestamp} {monitor.event_type}'
                            + f' {monitor.name} {monitor.executable_path} {monitor.process_id}')


class TableWidget(QTableView):

    def __init__(self) -> None:
        super().__init__()

        self.current_row = 0

        self.item_model = QStandardItemModel(self)
        self.item_model.setHorizontalHeaderLabels(['Timestamp',
                                                   'Creation date',
                                                   'Event type',
                                                   'Name',
                                                   'Path',
                                                   'PID',
                                                   'Owner',
                                                   'Privileges',
                                                   'Handle count',
                                                   'Parent PID',
                                                   'Thread count'])
        self.setModel(self.item_model)
        self.setSortingEnabled(True)
        self.sortByColumn(0, 0)

    def add_event(self, args):

        self.item_model.setRowCount(self.current_row)

        for index, arg in enumerate(args):
            label = QStandardItem(str(arg))
            label.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.item_model.setItem(self.current_row, index, label)
            if index != 4:
                self.resizeColumnToContents(index)
        self.scrollToBottom()

        self.current_row += 1


class Application(QMainWindow):

    def __init__(self) -> None:
        super().__init__()

        self.init_dirs()
        self.init_files()
        self.init_config()

        self.table = TableWidget()

        self.init_ui()

        self.start_monitors()

    def init_dirs(self):
        '''Initialize directories'''

        CONFIG.SELF_PATH = os.path.abspath('.')

        os.makedirs(CONFIG.DATA_DIR, exist_ok=True)

        try:
            os.chdir(sys._MEIPASS)  # pylint: disable=protected-access
        except AttributeError:
            pass

    def init_files(self):
        '''Initialize files'''

        if not os.path.exists(os.path.join(CONFIG.DATA_DIR, CONFIG.FILE_CONFIG)):
            CONFIG.user_config_create()

    def init_config(self):
        '''Initialize configurations'''

        CONFIG.user_config_load()

        if not CONFIG.DIR_LOGS:
            CONFIG['LOGGING'] = False

    def init_ui(self):
        '''Initialize the user interface components'''

        self.setCentralWidget(self.table)

        self.action_quit = QAction("&Exit", self,
                                   shortcut="Ctrl+Q",
                                   triggered=QApplication.exit)

        self.action_start = QAction("Start monitoring", self,
                                    triggered=self.start_monitors)
        self.action_stop = QAction("Stop monitoring", self,
                                   triggered=self.stop_monitors)

        self.action_logging = QAction("&Logging", self,
                                      checkable=True,
                                      shortcut="Ctrl+L",
                                      triggered=self.logging)
        self.action_folder = QAction("Select logs folder...", self,
                                     triggered=self.set_logs_dir)

        self.action_help = QAction("About &program", self,
                                   shortcut="f1",
                                   triggered=lambda: QMessageBox.about(
                                       self, "О программе", CONFIG.DESCRIPTION))

        if not CONFIG.DIR_LOGS:
            self.action_logging.setEnabled(False)
        else:
            self.action_logging.setChecked(CONFIG.LOGGING)

        self.menu_file = QMenu("&File", self)
        self.menu_file.addAction(self.action_quit)

        self.menu_watcher = QMenu("&Watcher", self)
        self.menu_watcher.addAction(self.action_start)
        self.menu_watcher.addAction(self.action_stop)
        self.menu_watcher.addSeparator()
        self.menu_watcher.addAction(self.action_logging)
        self.menu_watcher.addAction(self.action_folder)

        self.menu_help = QMenu("&Help", self)
        self.menu_help.addAction(self.action_help)

        self.menuBar().addMenu(self.menu_file)
        self.menuBar().addMenu(self.menu_watcher)
        self.menuBar().addMenu(self.menu_help)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)
        self.status_label = QLabel()

        self.statusBar().addWidget(self.status_label)
        self.statusBar().addWidget(self.progress_bar, 1)

        QApplication.setStyle('Windows')
        QApplication.setPalette(QApplication.style().standardPalette())

        icon = QIcon()
        icon.addFile(CONFIG.APP_ICON)

        self.setWindowIcon(icon)
        self.setWindowTitle(f'{CONFIG.APP_NAME}, version {CONFIG.VERSION}')

    def start_monitors(self):
        '''Start monitoring processes for creation and deletion events'''

        self.creation = Monitor('creation')
        self.creation.date_signal.connect(self.table.add_event)
        self.creation.start()

        self.deletion = Monitor('deletion')
        self.deletion.date_signal.connect(self.table.add_event)
        self.deletion.start()

        self.status_label.setText('WATCHING IN PROGRESS')
        self.progress_bar.setMaximum(0)

    def stop_monitors(self):
        '''Stop monitoring processes for creation and deletion events'''

        self.creation.terminate()
        self.deletion.terminate()

        self.status_label.setText('WATCHING STOPPED')
        self.progress_bar.setMaximum(1)

    def logging(self):
        '''Start or stop logging'''

        if self.action_logging.isChecked():
            CONFIG['LOGGING'] = True
            self.status_label.setText('LOGGING IS START')
        else:
            CONFIG['LOGGING'] = False
            self.status_label.setText('LOGGING IS STOP')

    def set_logs_dir(self):
        '''Select logs folder'''

        dir = QFileDialog.getExistingDirectory(
            self, 'Select logs folder', 'C:\\')

        if dir:
            CONFIG['DIR_LOGS'] = dir
            self.action_logging.setEnabled(True)


if __name__ == '__main__':

    app = QApplication(sys.argv)

    a = Application()
    a.showMaximized()

    sys.exit(app.exec_())
