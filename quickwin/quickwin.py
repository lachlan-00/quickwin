#!/usr/bin/env python
#-*- coding: utf-8 -*-

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

import os
import ConfigParser
import subprocess
import sys

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib

from xdg.BaseDirectory import xdg_config_dirs


# quit if using python3
if sys.version[0] == 3:
    raise Exception('not python3 compatible, please use python 2.x')


CONFIG = xdg_config_dirs[0] + '/quickwin.conf'
UI_FILE = '/usr/share/quickwin/main.ui'
ICON_DIR = '/usr/share/icons/gnome/'
USER_HOME = os.getenv('HOME')
QUICK_STORE = USER_HOME + '/.local/share/quickwin'

#        while Gtk.events_pending():
#            Gtk.main_iteration()
#        return destin


class QUICKWIN(object):
    """ load and launch rdesktop shortcuts. """
    def __init__(self):
        """ start quickrdp """
        self.builder = Gtk.Builder()
        self.builder.add_from_file(UI_FILE)
        self.builder.connect_signals(self)
        # get config info
        self.checkconfig()
        self.conf = ConfigParser.RawConfigParser()
        self.conf.read(CONFIG)
        self.homefolder = self.conf.get('conf', 'home')
        # backwards compatability for new config options
        self.current_dir = self.homefolder
        self.current_files = None
        self.filelist = None
        # load main window items
        self.window = self.builder.get_object('main_window')
        self.addbutton = self.builder.get_object('addbutton')
        self.addimage = self.builder.get_object('addimage')
        self.settingsbutton = self.builder.get_object('settingsbutton')
        self.closemain = self.builder.get_object('closemain')
        self.fileview = self.builder.get_object('fileview')
        self.contentlist = self.builder.get_object('filestore')
        self.contenttree = self.builder.get_object('fileview')
        self.popmenu = self.builder.get_object('popmenu')
        # load add connection window items
        self.addwindow = self.builder.get_object('add_window')
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
        self.successwindow = self.builder.get_object('success_window')
        self.successbutton = self.builder.get_object('closesuccess')
        # create lists and connect actions
        self.loadlists()
        self.connectui()
        self.listfiles(self.current_dir)
        self.run()

    def connectui(self):
        """ connect all the window wisgets """
        # main window actions
        self.window.connect('destroy', self.quit)
        self.window.connect('key-release-event', self.shortcatch)
        self.settingsbutton.connect('clicked', self.showconfig)
        self.addbutton.connect('clicked', self.showaddconnection)
        self.closemain.connect('clicked', self.quit)
        #images
        self.addimage.set_from_file(ICON_DIR + '16x16/actions/add.png')
        # config window actions
        self.applybutton.connect('clicked', self.saveconf)
        self.closebutton.connect('clicked', self.closeconf)
        # add window actions
        self.saveaddbutton.connect('clicked', self.saveadd)
        self.closeaddbutton.connect('clicked', self.closeadd)
        # popup window actions
        self.popbutton.connect('clicked', self.closepop)
        self.successbutton.connect('clicked', self.closesuccess)
        # set up file and folder lists
        cell = Gtk.CellRendererText()
        filecolumn = Gtk.TreeViewColumn('Windows Servers', cell, text=0)
        self.fileview.connect('row-activated', self.loadselection)
        self.fileview.connect('button-release-event', self.button)
        self.contenttree.append_column(filecolumn)
        self.contenttree.set_model(self.contentlist)

        # list default dir on startup
        if not os.path.isdir(self.homefolder):
            os.makedirs(self.homefolder)
        return

    def run(self):
        """ show the main window and start the main GTK loop """
        self.window.set_position(Gtk.Align.END)
        self.showme(self.window)
        Gtk.main()

    def button(self, actor, event):
        """ Catch mouse clicks"""
        print('activate')
        #if Gdk.ModifierType.BUTTON1_MASK == event.get_state():
        #    # not used for loading
        #    # require double clicks self.loadselection()
        if Gdk.ModifierType.BUTTON2_MASK == event.get_state():
            print 'middle click'
        elif Gdk.ModifierType.BUTTON3_MASK == event.get_state():
            print 'right click'
            #self.popmenu.popup()
        return

    def showme(self, *args):
        """ show a Gtk.Window """
        args[0].show()

    def hideme(self, *args):
        """ hide a Gtk.Window """
        args[0].hide()
        self.listfiles(self.current_dir)

    def loadlists(self):
        """ create/empty all the lists used for tagging """
        print "NO LISTS"
        return

    def showconfig(self, *args):
        """ fill and show the config window """
        self.homeentry.set_text(self.homefolder)
        self.showme(self.confwindow)
        return

    def showaddconnection(self, *args):
        """ show the add connection window """
        self.homeentry.set_text(self.homefolder)
        self.showme(self.addwindow)
        return

    def saveconf(self, *args):
        """ save any config changes and update live settings"""
        self.conf.read(CONFIG)
        self.conf.set('conf', 'home', self.homeentry.get_text())
        self.homefolder = self.homeentry.get_text()
        # write to conf file
        conffile = open(CONFIG, "w")
        self.conf.write(conffile)
        conffile.close()
        return

    def saveadd(self, *args):
        """ save any config changes and update live settings"""
        print "SAVE ADD"
        return

    def checkconfig(self):
        """ create a default config if not available """
        if not os.path.isfile(CONFIG):
            conffile = open(CONFIG, "w")
            conffile.write('[conf]\nhome = ' + QUICK_STORE + '\n')
            conffile.close()
        return

    def closeconf(self, *args):
        """ hide the config window """
        self.hideme(self.confwindow)
        return

    def closeadd(self, *args):
        """ hide the config window """
        self.hideme(self.addwindow)
        return

    def closeerror(self, *args):
        """ hide the error window """
        self.popwindow.destroy()
        Gtk.main_quit(*args)
        raise Exception('Please install python-eyed3')
        return

    def closepop(self, *args):
        """ hide the error popup window """
        self.hideme(self.popwindow)
        return

    def closesuccess(self, *args):
        """ hide the organise completed window """
        self.hideme(self.successwindow)
        return

    def loadselection(self, *args):
        """ load selected files into tag editor """
        model, fileiter = self.contenttree.get_selection().get_selected_rows()
        self.current_files = []
        for files in fileiter:
            if model[files][0] == '[No RDP shortcuts found]':
                self.current_files = []
            else:
                tmp_file = self.current_dir + '/' + model[files][0]
                self.current_files.append(tmp_file)
        if not self.current_files == []:
            print "OPEN RDP CONNECTION"
            subprocess.Popen(self.current_files)
        else:
            print 'relisting directory'
            self.listfiles(self.current_dir)
        return

    def gohome(self, *args):
        """ go to the defined home folder """
        self.clearopenfiles()
        self.listfolder(self.homefolder)

    def goback(self, *args):
        """ go back the the previous directory """
        back_dir = os.path.dirname(self.current_dir)
        self.clearopenfiles()
        self.listfolder(back_dir)
        return

    def keypress(self, actor, event):
        """ capture backspace key for folder navigation """
        if event.get_keycode()[1] == 22:
            self.goback()

    def shortcatch(self, actor, event):
        """ capture keys for shortcuts """
        test_mask = (event.state & Gdk.ModifierType.CONTROL_MASK ==
                     Gdk.ModifierType.CONTROL_MASK)
        if event.get_state() and test_mask:
            if event.get_keycode()[1] == 39:
                self.savetags()
            if event.get_keycode()[1] == 46:
                self.loadselection()
            if event.get_keycode()[1] == 56:
                self.goback()
            if event.get_keycode()[1] == 43:
                self.gohome()


    def entrycatch(self, actor, event):
        """ capture key presses to activate checkboxes """
        movement_keys = [22, 23, 36, 37, 50, 62, 64, 65, 66,
                         105, 108, 110, 111, 112, 113,
                         114, 115, 116, 117, 118, 119]
        test_mask = (event.state & Gdk.ModifierType.CONTROL_MASK ==
                     Gdk.ModifierType.CONTROL_MASK)

    def quit(self, *args):
        """ stop the process thread and close the program"""
        self.addwindow.destroy()
        self.confwindow.destroy()
        self.window.destroy()
        Gtk.main_quit(*args)
        return False


    def clearopenfiles(self):
        """ clear the tags ui when changing folder """
        count = 0
        while count < len(self.uibuttons):
            self.uibuttons[count][0].set_active(False)
            self.uibuttons[count][1].set_text('')
            count = count + 1
        return

    def listfiles(self, *args):
        """ function to fill the file list column """
        self.current_files = []
        try:
            files_dir = os.listdir(self.current_dir)
            files_dir.sort(key=lambda y: y.lower())
        except OSError:
            self.gohome()
        # clear list if we have scanned before
        for items in self.contentlist:
            self.contentlist.remove(items.iter)
        # clear combobox before adding entries
        for items in self.contenttree:
            self.contenttree.remove(items.iter)
        # search the supplied directory for items
        for items in files_dir:
            test_file = os.path.isfile(self.current_dir + '/' + items)
            if not items[0] == '.' and test_file:
                self.contentlist.append([items])
        if len(self.contentlist) == 0:
            self.contentlist.append(['[No RDP shortcuts found]'])
        return


if __name__ == "__main__":
    GLib.threads_init()
    QUICKWIN()