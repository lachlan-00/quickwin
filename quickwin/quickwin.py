#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" quickrdp: Python rdp launcher
    ----------------Authors----------------
    Lachlan de Waard <lachlan.00@gmail.com>
    ----------------Licence----------------
    GNU General Public License version 3

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import configparser
import gi
import os
import subprocess
import sys

gi.require_version('Gtk', '3.0')

# noinspection PyPep8
from gi.repository import Gtk
# noinspection PyPep8
from gi.repository import Gdk
# noinspection PyPep8
from xdg.BaseDirectory import xdg_config_dirs

CONFIG = xdg_config_dirs[0] + '/quickwin.conf'
UI_FILE = '/usr/share/quickwin/main.ui'
ICON_DIR = '/usr/share/icons/gnome/'
TRAY_ICON = '/usr/share/pixmaps/quickwin.png'
CUSTOM_ICON = None
USER_HOME = os.getenv('HOME')
QUICK_STORE = USER_HOME + '/.local/share/quickwin'
CUSTOM_PATH = None
CUSTOM_TITLE = None
WINDOWOPEN = False
WINDOWSPOSITION = None

# get custom options from launch arguments
for arguments in sys.argv:
    if arguments[:3] == '/f:':
        print('\nUsing different launch folder: ' + arguments[3:] + '\n')
        CUSTOM_PATH = arguments[3:]
    if arguments[:3] == '/t:':
        print('\nUsing different window title ' + arguments[3:] + '\n')
        CUSTOM_TITLE = arguments[3:]
    if arguments[:3] == '/i:':
        print('\nUsing a custom icon ' + arguments[3:] + '\n')
        CUSTOM_ICON = arguments[3:]
    if arguments[:3] == '/c:':
        print('\nUsing different config location: ' + arguments[3:] + '\n')
        CONFIG = arguments[3:]


def checkconfig():
    """ create a default config if not available """
    if not os.path.isfile(CONFIG):
        conffile = open(CONFIG, "w")
        conffile.write('[conf]\nhome = ' + QUICK_STORE + '\n' +
                       'root_x = \n' +
                       'root_y = \n' +
                       'width = \n' +
                       'height = \n')
        conffile.close()
    else:
        conf = configparser.RawConfigParser()
        conf.read(CONFIG)
        if not conf.has_section('home'):
            conf.add_section('home')
        if not conf.has_section('root_x'):
            conf.add_section('root_x')
        if not conf.has_section('root_y'):
            conf.add_section('root_y')
        if not conf.has_section('width'):
            conf.add_section('width')
        if not conf.has_section('height'):
            conf.add_section('height')
    return


class QUICKWIN(object):
    """ load and launch *.desktop shortcuts. """

    def __init__(self):
        """ start quickrdp """
        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)
        self.builder.connect_signals(self)
        # get config info
        self.conf = configparser.RawConfigParser()
        checkconfig()
        self.conf.read(CONFIG)
        if CUSTOM_PATH:
            print('\nusing custom path')
            self.homefolder = CUSTOM_PATH
        else:
            self.homefolder = self.conf.get('conf', 'home')
        # backwards compatability for new config options
        self.current_dir = self.homefolder
        self.current_files = None
        self.filelist = None
        # Make a status icon
        # Set custom icon
        if CUSTOM_ICON:
            self.statusicon = Gtk.StatusIcon.new_from_file(CUSTOM_ICON)
        else:
            self.statusicon = Gtk.StatusIcon.new_from_file(TRAY_ICON)
        self.statusicon.connect('activate', self.status_clicked)
        self.statusicon.connect('popup-menu', self.right_click_event)
        if CUSTOM_TITLE:
            self.statusicon.set_tooltip_text(CUSTOM_TITLE)
        else:
            self.statusicon.set_tooltip_text("quickwin")
        # load main window items
        self.window = self.builder.get_object('main_window')
        self.addbutton = self.builder.get_object('addbutton')
        self.addimage = self.builder.get_object('addimage')
        self.settingsbutton = self.builder.get_object('settingsbutton')
        self.closemain = self.builder.get_object('closemain')
        # self.fileview = self.builder.get_object('fileview')
        self.contentlist = self.builder.get_object('filestore')
        self.contenttree = self.builder.get_object('fileview')
        # load add connection window items
        self.addwindow = self.builder.get_object('add_window')
        self.addentry = self.builder.get_object('addentry')
        self.addcommand = self.builder.get_object('cmdentry')
        self.saveaddbutton = self.builder.get_object('saveaddbutton')
        self.closeaddbutton = self.builder.get_object('closeaddbutton')
        # load config window items
        self.confwindow = self.builder.get_object('config_window')
        self.homeentry = self.builder.get_object('homeentry')
        self.applybutton = self.builder.get_object('applyconf')
        self.closebutton = self.builder.get_object('closeconf')
        # load popup window items
        self.popwindow = self.builder.get_object('popup_window')
        self.popbutton = self.builder.get_object('closepop')
        # create lists and connect actions
        self.connectui()
        self.listfiles(self.current_dir)
        self.run()

    def connectui(self):
        """ connect all the window wisgets """
        # main window actions
        self.window.connect('destroy', self.quit)
        self.window.connect('hide', self.save_position)
        self.window.connect('focus', self.save_position)
        self.window.connect('window-state-event', self.save_position)
        self.window.connect('button-release-event', self.save_position)
        self.window.connect('drag-end', self.save_position)
        self.settingsbutton.connect('clicked', self.showconfig)
        self.addbutton.connect('clicked', self.showaddconnection)
        self.closemain.connect('clicked', self.quit)
        # config window actions
        self.applybutton.connect('clicked', self.saveconf)
        self.closebutton.connect('clicked', self.closeconf)
        # add window actions
        self.saveaddbutton.connect('clicked', self.saveadd)
        self.closeaddbutton.connect('clicked', self.closeadd)
        # popup window actions
        self.popbutton.connect('clicked', self.closepop)
        # set up file and folder lists
        cell = Gtk.CellRendererText()
        filecolumn = Gtk.TreeViewColumn('Scripts and Launchers', cell, text=0)
        self.contenttree.connect('row-activated', self.loadselection)
        self.contenttree.connect('button-release-event', self.button)
        self.contenttree.append_column(filecolumn)
        self.contenttree.set_model(self.contentlist)
        if CUSTOM_TITLE:
            self.window.set_title(CUSTOM_TITLE)

        # list default dir on startup
        if not os.path.isdir(self.homefolder):
            os.makedirs(self.homefolder)
        return

    def run(self):
        """ show the main window and start the main GTK loop """
        self.set_position()
        Gtk.main()

    def button(self, actor, event):
        """ Catch mouse clicks"""
        if actor == self.contenttree:
            if Gdk.ModifierType.BUTTON2_MASK == event.get_state():
                print('middle click')
                return actor
            elif Gdk.ModifierType.BUTTON3_MASK == event.get_state():
                print('right click')
                return actor
        return

    def showme(self, *args):
        """ show a Gtk.Window """
        self.listfiles(self.current_dir)
        args[0].show()

    def hideme(self, *args):
        """ hide a Gtk.Window """
        self.listfiles(self.current_dir)
        args[0].hide()

    def right_click_event(self, icon, button, time):
        self.menu = Gtk.Menu()

        quit = Gtk.MenuItem()
        quit.set_label("Quit")

        quit.connect("activate", Gtk.main_quit)

        self.menu.append(quit)
        self.menu.show_all()

        def pos(self, button, menu, icon):
                return (Gtk.StatusIcon.position_menu(self, button, menu, icon))

        self.menu.popup(None, None, pos, self.statusicon, button, time)

    def status_clicked(self, status):
        """ hide and unhide the window when clicking the status icon """
        global WINDOWOPEN
        # Unhide the window
        #print(dir(self.statusicon))
        if not WINDOWOPEN:
            self.set_position()
            self.window.show()
            WINDOWOPEN = True
            # save window position
        elif WINDOWOPEN:
            self.delete_event(self, self.window)
        return status

    def set_position(self):
        """ move the main window to last known position """
        try:
            self.window.move(int(self.conf.get('conf', 'root_x')), int(self.conf.get('conf', 'root_y')))
            self.window.resize(int(self.conf.get('conf', 'width')), int(self.conf.get('conf', 'height')))
        except ValueError:
            # incorrect value for setting
            pass
        return

    def save_position(self, actor, event):
        """ save the main window position """
        self.conf.read(CONFIG)
        self.conf.set('conf', 'root_x', self.window.get_position().root_x)
        self.conf.set('conf', 'root_y', self.window.get_position().root_y)
        self.conf.set('conf', 'width', self.window.get_size().width)
        self.conf.set('conf', 'height', self.window.get_size().height)
        self.writeconf()
        self.conf.read(CONFIG)
        return

    def delete_event(self, window, event):
        """ Hide the window then the close button is clicked """
        global WINDOWOPEN
        # Don't delete; hide instead
        self.window.hide_on_delete()
        WINDOWOPEN = False
        return True

    def showconfig(self, actor):
        """ fill and show the config window """
        if actor == self.settingsbutton:
            self.homeentry.set_text(self.homefolder)
            self.showme(self.confwindow)
        return actor

    def showaddconnection(self, actor):
        """ show the add connection window """
        self.homeentry.set_text(self.homefolder)
        self.showme(self.addwindow)
        return actor

    def writeconf(self):
        """ write to conf file """
        conffile = open(CONFIG, "w")
        self.conf.write(conffile)
        conffile.close()
        return

    def saveconf(self, actor):
        """ save any config changes and update live settings"""
        if actor == self.applybutton:
            self.conf.read(CONFIG)
            self.conf.set('conf', 'home', self.homeentry.get_text())
            self.homefolder = self.homeentry.get_text()
            self.writeconf()
        return

    def saveadd(self, *args):
        """ save any config changes and update live settings"""
        print("SAVE ADD")
        print(self.addentry.get_text())
        print(self.addcommand.get_text())
        return args

    def closeconf(self, actor):
        """ hide the config window """
        if actor == self.closebutton:
            self.hideme(self.confwindow)
        return

    def closeadd(self, actor):
        """ refresh the file list and hide the config window """
        self.listfiles(self.current_dir)
        if actor == self.closeaddbutton:
            self.hideme(self.addwindow)
        return

    def closepop(self, actor):
        """ hide the error popup window """
        if actor == self.popbutton:
            self.hideme(self.popwindow)
        return

    def loadselection(self, *args):
        """ load selected files into tag editor """
        contenttree = args[0]
        model, fileiter = contenttree.get_selection().get_selected_rows()
        self.current_files = []
        for files in fileiter:
            if model[files][0] == '[No files found]':
                self.current_files = []
            else:
                tmp_file = os.path.join(self.current_dir, model[files][0])
                if os.access(tmp_file, os.X_OK):
                    self.current_files.append(tmp_file)
                else:
                    print(tmp_file + '\nIs not executable')
        if not self.current_files == []:
            print("Opening selected file")
            print(self.current_files)
            subprocess.Popen(self.current_files)
        else:
            print('relisting directory')
            self.listfiles(self.current_dir)
        return

    def quit(self, *args):
        """ stop the process thread and close the program"""
        # destroy windows and quit
        self.addwindow.destroy()
        self.confwindow.destroy()
        self.window.destroy()
        Gtk.main_quit(*args)
        return False

    def listfiles(self, srcpath):
        """ function to fill the file list column """
        self.current_files = []
        if CUSTOM_PATH:
            srcpath = CUSTOM_PATH
        try:
            files_dir = os.listdir(srcpath)
            files_dir.sort(key=lambda y: y.lower())
        except OSError:
            self.listfiles(self.homefolder)
            return
        # clear list if we have scanned before
        for items in self.contentlist:
            self.contentlist.remove(items.iter)
        # clear combobox before adding entries
        for items in self.contenttree:
            self.contenttree.remove(items.iter)
        # search the supplied directory for items
        for items in files_dir:
            test_executable = None
            tmp_file = self.current_dir + '/' + items
            test_file = os.path.isfile(tmp_file)
            if test_file:
                test_executable = os.access(tmp_file, os.X_OK)
            if not items[0] == '.' and test_file and test_executable:
                self.contentlist.append([items])
        if len(self.contentlist) == 0:
            self.contentlist.append(['[No files found]'])
        return


if __name__ == "__main__":
    QUICKWIN()
