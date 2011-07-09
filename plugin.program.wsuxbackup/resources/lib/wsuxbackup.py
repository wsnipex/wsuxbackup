# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


"""
    Plugin for Launching wsuxbackup.sh
"""

# main imports
import sys
import os
import xbmc
import xbmcgui
import xbmcplugin

import time
import re
import urllib

#BASE_PATH = os.getcwd()
_id="plugin.program.wsuxbackup"


try:
    from xbmcaddon import Addon

    # source path for launchers data
    PLUGIN_DATA_PATH = xbmc.translatePath(os.path.join( "special://profile/addon_data", _id))
    BASE_PATH = xbmc.translatePath(os.path.join("special://home/addons/", _id))
    #print "BASE_PATH: ", BASE_PATH
    BACKUP_SCRIPT = BASE_PATH + "/wsuxbackup"
    print "WSUXBACKUP: " + BACKUP_SCRIPT + " = " + BACKUP_SCRIPT 

    __settings__ = Addon( _id )
    __language__ = __settings__.getLocalizedString
    print "WSUXBACKUP: Mode AddOn ON"
    print "WSUXBACKUP: PLUGIN_DATA_PATH =" + PLUGIN_DATA_PATH
    #print "WSUXBACKUP: Settings", __settings__

except exception, e: 
    print e
    # source path for launchers data
    PLUGIN_DATA_PATH = xbmc.translatePath( os.path.join( "special://profile/plugin_data", "programs", sys.modules[ "__main__" ].__plugin__) )

    __settings__ = xbmcplugin
    __language__ = __language__
    print "WSUXBACKUP: Mode plugin ON"
    print "WSUXBACKUP: " + PLUGIN_DATA_PATH

# source path for launchers data
BASE_CURRENT_SOURCE_PATH = os.path.join( PLUGIN_DATA_PATH , "launchers.xml" )
SHORTCUT_FILE = os.path.join( PLUGIN_DATA_PATH , "shortcut.cut" )
#THUMBS_PATH = os.path.join( PLUGIN_DATA_PATH , "thumbs" )

REMOVE_COMMAND = "%%REMOVE%%"
ADD_COMMAND = "%%ADD%%"
#IMPORT_COMMAND = "%%IMPORT%%"
#SCAN_COMMAND = "%%SCAN%%"
RENAME_COMMAND = "%%RENAME%%"
#SET_THUMB_COMMAND = "%%SETTHUMB%%"
WAIT_TOGGLE_COMMAND = "%%WAIT_TOGGLE%%"
COMMAND_ARGS_SEPARATOR = "^^"
WRITECFG_COMMAND = "%%CFG%%"
#COMMAND_ARGS_SEPARATOR = "/"
#SEARCH_COMMAND = "%%SEARCH%%"#search
#SEARCH_ALL_COMMAND = "%%SEARCH_ALL%%"#search all

# breaks the plugin partly
# when using
# xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s/%s)" % (self._path, launcherName, search, SEARCH_COMMAND))
# for example
#pDialog = xbmcgui.DialogProgress()
#pDialog.create( sys.modules[ "__main__" ].__plugin__ )

BACKUP_SETTINGS = ["configfile", "destdir", "backupmbr", "backupparttable", "disk", "checkspace", "excludes", "backupmethod", "maxtarbackups", "maxrsyncbackups", "xbmcurl"]


class Main:
    BASE_CACHE_PATH = xbmc.translatePath(os.path.join( "special://profile/Thumbnails", "Pictures" ))
    launchers = {}

    ''' initializes plugin and run the required action
        arguments:
            argv[0] - the path of the plugin (supplied by XBMC)
            argv[1] - the handle of the plugin (supplied by XBMC)
            argv[2] - one of the following (__language__( 30000 ) and 'rom' can be any launcher name or rom name created with the plugin) :
                /launcher - open the specific launcher (if exists) and browse its roms
                            if the launcher is standalone - run it.
                /launcher/%%REMOVE%% - remove the launcher
                /launcher/%%ADD%% - add a new rom (open wizard)
                /launcher/%%WAIT_TOGGLE%% - toggle wait state 
                /%%ADD%% - add a new launcher (open wizard)
                
                (blank)     - open a list of the available launchers. if no launcher exists - open the launcher creation wizard.
    '''                        
    def __init__(self):
        # store an handle pointer
        self._handle = int(sys.argv[1])
        #print self._handle
                    
        self._path = sys.argv[0]
        
        # get users preference
        self._get_settings()
        print "WSUXBACKUP: Settings =", self.settings
        self._load_launchers(self.get_xml_source())

        # if a commmand is passed as parameter
        param = sys.argv[2]
        #self._log("orig param: " + param)
        if param:
            #print "param: ", param
            param = param[1:]
            self._log("param: " + param)
            tmp = param.split("/")
    
            if (param == ADD_COMMAND):
                self._add_backup()
                       
            elif (len(tmp) > 1):
                #tmp = param.split("/")
                launcher = tmp[0]
                command = tmp[1]
                #self._log("command: " + command)
                #self._log("backup: " + launcher)
            
                if (command == REMOVE_COMMAND):
                    # check if it is a single rom or a launcher
                    if (not os.path.dirname(launcher)):
                        self._remove_launcher(launcher)
                    else:
                        self._remove_rom(os.path.dirname(launcher), os.path.basename(launcher))
                elif (command == RENAME_COMMAND):
                    if (not os.path.dirname(launcher)):
                        self._log("renaming" + launcher)
                        self._rename_launcher(launcher)
                elif (command == WRITECFG_COMMAND):
                    self._write_configfile(launcher)
            else:
                self._run_launcher(param)
        else:
            # otherwise get the list of the programs in the current folder
            if (not self._get_launchers()):
                # if no launcher found - attempt to add a new one
                #if (self._add_new_launcher()):
                if (self._add_backup()):
                    self._get_launchers()
                else:
                    xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=False , cacheToDisc=False)
                    
    def _log(self, message):
        sys.stderr.write("WSUXBACKUP: " + str(message))
        
    def _remove_launcher(self, launcherName):
        dialog = xbmcgui.Dialog()
        ret = dialog.yesno(__language__( 30000 ), __language__( 30010 ) % launcherName)
        if (ret):
            self.launchers.pop(launcherName)
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
            

    def _rename_launcher(self, launcherName):
        print "launchername: " + self.launchers[launcherName]["name"]
        keyboard = xbmc.Keyboard(self.launchers[launcherName]["name"], __language__( 30025 ))
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            self.launchers[launcherName]["name"] = keyboard.getText()
            self._save_launchers()
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
            
    def _run_launcher(self, launcherName):
        if (self.launchers.has_key(launcherName)):
            launcher = self.launchers[launcherName]
            if (os.environ.get( "OS", "xbox" ) == "xbox"):
                #xbmc.executebuiltin('XBMC.Runxbe(' + launcher["application"] + ')')
                self._log("ERROR: Xbox is not supported")
            else:
                if (sys.platform == 'win32'):
                    self._log("ERROR: windows is not supported")
#                    if (launcher["wait"] == "true"):
#                        cmd = "System.ExecWait"
#                    else:
#                        cmd = "System.Exec"
#                    #this minimizes xbmc some apps seems to need it
#                    xbmc.executehttpapi("Action(199)")
#                    xbmc.executebuiltin("%s(\\\"%s\\\" \\\"%s\\\")" % (cmd, launcher["application"], launcher["args"]))
#                    #this brings xbmc back
#                    xbmc.executehttpapi("Action(199)")
                elif (sys.platform.startswith('linux')):
#                    #this minimizes xbmc some apps seems to need it
#                    xbmc.executehttpapi("Action(199)")
                    os.system("%s %s" % (launcher["application"], launcher["args"]))
#                    #this brings xbmc back
#                    xbmc.executehttpapi("Action(199)")
#                elif (sys.platform.startswith('darwin')):
#                    #this minimizes xbmc some apps seems to need it
#                    xbmc.executehttpapi("Action(199)")
#                    os.system("\"%s\" %s" % (launcher["application"], launcher["args"]))
#                    #this brings xbmc back
#                    xbmc.executehttpapi("Action(199)")
                else:
                    pass;
                    # unsupported platform
                             


    ''' get an xml data from an xml file '''
    def get_xml_source(self):
        try:
            usock = open(BASE_CURRENT_SOURCE_PATH, 'r')
            # read source
            xmlSource = usock.read()
            # close socket
            usock.close()
            ok = True
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % (self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ],)
            ok = False
        if ( ok ):
            # return the xml string without \n\r (newline)
            return xmlSource.replace("\n","").replace("\r","")
        else:
            return ""

    def _save_launchers (self):
        # make settings directory if doesn't exists
        if (not os.path.isdir(os.path.dirname(BASE_CURRENT_SOURCE_PATH))):
            os.makedirs(os.path.dirname(BASE_CURRENT_SOURCE_PATH));
            
        usock = open( BASE_CURRENT_SOURCE_PATH, 'w' )
        usock.write("<?xml version=\"1.0\" encoding=\"utf-8\" standalone=\"yes\"?>\n")
        usock.write("<launchers>\n")
        for launcherIndex in self.launchers:
            launcher = self.launchers[launcherIndex]
            usock.write("\t<launcher>\n")
            usock.write("\t\t<name>"+launcher["name"]+"</name>\n")
            usock.write("\t\t<application>"+launcher["application"]+"</application>\n")
            usock.write("\t\t<args>"+launcher["args"]+"</args>\n")
            #usock.write("\t\t<rompath>"+launcher["rompath"]+"</rompath>\n")
            #usock.write("\t\t<romext>"+launcher["romext"]+"</romext>\n")
            #usock.write("\t\t<thumb>"+launcher["thumb"]+"</thumb>\n")
            usock.write("\t\t<wait>"+launcher["wait"]+"</wait>\n")
            #usock.write("\t\t<roms>\n")
#            for romIndex in launcher["roms"]:
#                romdata = launcher["roms"][romIndex]
#                usock.write("\t\t\t<rom>\n")
#                usock.write("\t\t\t\t<name>"+romdata["name"]+"</name>\n")
#                usock.write("\t\t\t\t<filename>"+romdata["filename"]+"</filename>\n")
#                usock.write("\t\t\t\t<thumb>"+romdata["thumb"]+"</thumb>\n")
#                usock.write("\t\t\t</rom>\n")
#            usock.write("\t\t</roms>\n")
            usock.write("\t</launcher>\n")            
        usock.write("</launchers>")
        usock.close()
        
    ''' read the list of launchers and roms from launchers.xml file '''
    def _load_launchers( self , xmlSource):
        launchers = re.findall( "<launcher>(.*?)</launcher>", xmlSource )
        print "Launcher: found %d launchers" % ( len(launchers) )
        for launcher in launchers:
            name = re.findall( "<name>(.*?)</name>", launcher )
            application = re.findall( "<application>(.*?)</application>", launcher )
            args = re.findall( "<args>(.*?)</args>", launcher )
            wait = re.findall( "<wait>(.*?)</wait>", launcher )

            if len(name) > 0 : name = name[0]
            else: name = "unknown"

            if len(application) > 0 : application = application[0]
            else: application = ""

            if len(args) > 0 : args = args[0]
            else: args = ""

            if len(wait) > 0: wait = wait[0]
            else: wait = ""
           

            # prepare launcher object data
            launcherdata = {}
            launcherdata["name"] = name
            launcherdata["application"] = application
            launcherdata["args"] = args
            launcherdata["wait"] = wait
            # add launcher to the launchers list (using name as index)
            self.launchers[name] = launcherdata
    
    def _get_launchers( self ):
        if (len(self.launchers) > 0):
            for key in sorted(self.launchers.iterkeys()):
                #self._add_launcher(self.launchers[key]["name"], self.launchers[key]["application"], self.launchers[key]["rompath"], self.launchers[key]["romext"], self.launchers[key]["thumb"], self.launchers[key]["wait"], self.launchers[key]["roms"], len(self.launchers))
                self._add_launcher(self.launchers[key]["name"], self.launchers[key]["application"], self.launchers[key]["wait"], len(self.launchers))
                #self._add_backup(self.launchers[key]["name"], self.launchers[key]["application"], self.launchers[key]["wait"], len(self.launchers))
            xbmcplugin.endOfDirectory( handle=int( self._handle ), succeeded=True, cacheToDisc=False )
            return True   
        else:
            return False


#    def _report_hook( self, count, blocksize, totalsize ):
#         percent = int( float( count * blocksize * 100) / totalsize )
#         msg1 = __language__( 30033 )  % ( os.path.split( self.url )[ 1 ], )
#         pDialog.update( percent, msg1 )
#         if ( pDialog.iscanceled() ): raise
        
#    def _scan_launcher(self, launchername):
#        self._search_thumb(launchername, "")
#        self._save_launchers()


        
    def _add_launcher(self, name, cmd, wait, total) :
        commands = []
        path = ""
        if (path == ""):
            folder = False
            icon = "DefaultProgram.png"
        else:
            folder = True
            icon = "DefaultFolder.png"
            commands.append((__language__( 30106 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, ADD_COMMAND) , ))
        commands.append((__language__( 30107 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, RENAME_COMMAND) , ))
        commands.append((__language__( 30101 ), "XBMC.RunPlugin(%s?%s)" % (self._path, ADD_COMMAND) , ))
        commands.append((__language__( 30104 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, REMOVE_COMMAND) , ))
        commands.append((__language__( 30105 ), "XBMC.RunPlugin(%s?%s/%s)" % (self._path, name, WRITECFG_COMMAND) , ))
        
        listitem = xbmcgui.ListItem( name, iconImage=icon )
        listitem.addContextMenuItems( commands )
        xbmcplugin.addDirectoryItem( handle=int( self._handle ), url="%s?%s"  % (self._path, name), listitem=listitem, isFolder=folder, totalItems=total)


    def _add_backup(self):
        #filter = ""
        app = BACKUP_SCRIPT 
        self._log("Using Backup Script: " + app)
        #app = xbmcgui.Dialog().browse(1,__language__( 30023 ),"files",filter)
        if (app):
            argkeyboard = xbmc.Keyboard("", __language__( 30024 ))
            argkeyboard.doModal()
            if (argkeyboard.isConfirmed()):
                args = argkeyboard.getText();
                title = os.path.basename(app).split(".")[0].capitalize()
                keyboard = xbmc.Keyboard(title, __language__( 30025 ))
                keyboard.doModal()
                if (keyboard.isConfirmed()):
                    title = keyboard.getText()                    
                    # prepare launcher object data
                    launcherdata = {}
                    launcherdata["name"] = title
                    launcherdata["application"] = app
                    launcherdata["args"] = args
                    launcherdata["wait"] = "false" 
                                                        
                    # add launcher to the launchers list (using name as index)
                    self.launchers[title] = launcherdata
                    self._save_launchers()

                    xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % (self._path))
                    return True

        

    def _toggle_wait(self, launcher):
        # toggle wait state
        if (self.launchers[launcher]["wait"] == "true"):
            self.launchers[launcher]["wait"] = "false"
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30029 )  ))
            #xbmcgui.Dialog().ok(__language__( 30000 ), __language__( 30029 ))
        else:
            self.launchers[launcher]["wait"] = "true"
            xbmc.executebuiltin("XBMC.Notification(%s,%s, 6000)" % (__language__( 30000 ), __language__( 30030 )  ))
            #xbmcgui.Dialog().ok(__language__( 30000 ), __language__( 30030 ))
        self._save_launchers()

                                
    def _get_settings(self):
        self.settings = {}

        try:
            for i in BACKUP_SETTINGS:
                self.settings[i] = __settings__.getSetting(self._handle,i)
        except:
            for i in BACKUP_SETTINGS:
                self.settings[i] = __settings__.getSetting(i)


    def _write_configfile(self, name):
        __settings__.openSettings(_id)
        # get newly created config
        self._get_settings
        
        cfgname = os.path.join(PLUGIN_DATA_PATH, self.settings["configfile"]).replace(" ", "")
        self._log("writing Config File: " + cfgname)
        
        try:
            f=open(cfgname, "w")
            
        except exception, e:
            self._log("Error opening" + cfgname )
            return False
        
        if (f):
            for k, v in self.settings.iteritems():
                line=k + "=" + '"' + v + '"' + "\n"
                f.writelines(line)
        return True
        
        
        
