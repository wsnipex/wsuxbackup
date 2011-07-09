"""
    WSUXBackup Launcher Plugin
"""

# main imports
import sys
import os
import xbmcplugin


# plugin constants
__plugin__ = "WSUXBackup"
__author__ = "wsnipex"
__url__ = ""
__svn_url__ = ""
__credits__ = "JustSomeUser,CinPoU,leo212,Lior Tamam"
__version__ = "0.0.1"

_id='plugin.program.wsuxbackup'
_resdir = "special://home/addons/" + _id + "/resources"
sys.path.append( _resdir + "/lib")
sys.path.append( _resdir + "/lib/")
_resdir2 = os.getcwd() + "/.xbmc/addons/" +_id + "/resources"
sys.path.append( _resdir2 + "/lib")

#REMOTE_DBG = True
REMOTE_DBG = False 

# append pydev remote debugger
if REMOTE_DBG:
    sys.path.append( "/opt/xbmc/share/xbmc/system/python/Lib" )
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pydevd as pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('192.168.0.141', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        #sys.stderr.write("PYTHONPATH: " + str(sys.path))
        #sys.stderr.write(str(sys.path))
        sys.exit(1)


if ( __name__ == "__main__" ):
    sys.stderr.write("PYTHONPATH: " + str(sys.path))
    import wsuxbackup as plugin
    plugin.Main()
sys.modules.clear()