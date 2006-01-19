#! /usr/bin/env python2

import sys, os, types, platform
import Pyro.core
import Pyro.naming

import SettingsService
import process

ERROR = 0
LINUX = 1
WIN = 2
WINXP = 3
MACOS = 4
MACOSX = 5
HPUX = 6
AIX = 7
SOLARIS = 8

if os.name == 'nt':
    import win32api, win32event, win32serviceutil, win32service, win32security, ntsecuritycon

PORT = 8712

if os.name == 'nt':
    def AdjustPrivilege(priv, enable):
        htoken = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                ntsecuritycon.TOKEN_ADJUST_PRIVILEGES | ntsecuritycon.TOKEN_QUERY)
        id = win32security.LookupPrivilegeValue(None, priv)
        if enable:
            newPrivileges = [(id, ntsecuritycon.SE_PRIVILEGE_ENABLED)]
        else:
            newPrivileges = [(id, 0)]
        win32security.AdjustTokenPrivileges(htoken, 0, newPrivileges)

class ClusterServer(Pyro.core.ObjBase):
   def __init__(self):
      Pyro.core.ObjBase.__init__(self)

   def registerInitialServices(self):
      # Register initial services
      self.mServices = {}
      settings = SettingsService.SettingsService()
      self.getDaemon().connect(settings)
      self.mServices["Settings"] = settings.getProxy()
      self.mProcess = None

   def test(self):
      print "Test"

   def getService(self, name):
      return self.mServices[name]

   def stopCommand(self):
      if not None == self.mProcess:
         return self.mProcess.kill()

   def isCommandRunning(self):
      try:
         # poll to see if is process still running
         if sys.platform.startswith("win"):
            timeout = 0
         else:
            timeout = os.WNOHANG
         self.mProcess.wait(timeout)
      except process.ProcessError, ex:
         if ex.errno == process.ProcessProxy.WAIT_TIMEOUT:
            return True
         else:
            raise
      return False

   def runCommand(self, command):
      if not None == self.mProcess and self.isCommandRunning():
         print "Command already running."
         return False
      else:
         self.mProcess = process.ProcessProxy(command)
         return True

   def getOutput(self):
      if not None == self.mProcess:
         return self.mProcess.stdout.readline()

if os.name == 'nt':
   class vrjclusterserver(win32serviceutil.ServiceFramework):
      _svc_name_ = "InfiscapeClusterControlService"
      _svc_display_name_ = "Infiscape Cluster Control Server"

      def __init__(self, args):
         win32serviceutil.ServiceFramework.__init__(self, args)
         #self.sfcServer = BaseSfcServer(('0.0.0.0', PORT), 0)

      def SvcStop(self):
         import servicemanager
         self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
         # Shutdown Server
         #self.sfcServer.server_close()
         # Log a 'stopped message to the event log.
         servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STOPPED,
                               (self._svc_display_name_, 'Stopped'))
         self.ReportServiceStatus(win32service.SERVICE_STOPPED)

      def SvcDoRun(self):
         import servicemanager
         # Log a 'started' message to the event log.
         servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STARTED,
                               (self._svc_display_name_, 'Started'))
         try:
            RunServer()
         except:
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                               servicemanager.PYS_SERVICE_STARTED,
                               (self._svc_display_name_, 'error'))


def RunServer():
   Pyro.core.initServer()
   daemon = Pyro.core.Daemon()
   cluster_server = ClusterServer()
   uri = daemon.connect(cluster_server, "cluster_server")
   cluster_server.registerInitialServices()

   print "The daemon runs on port:",daemon.port
   print "The object's uri is:",uri

   try:
      daemon.requestLoop()
   except:
      print "Unregistering Pyro objects"
      daemon.shutdown(True)

def daemonize (stdin='/dev/null', stdout='/dev/null', stderr=None, pidfile=None):
   """This forks the current process into a daemon. The stdin, stdout,
   and stderr arguments are file names that will be opened and be used
   to replace the standard file descriptors in sys.stdin, sys.stdout,
   and sys.stderr. These arguments are optional and default to /dev/null.
   Note that stderr is opened unbuffered, so if it shares a file with
   stdout then interleaved output may not appear in the order that you
   expect.
   """
   # Do first fork.
   try:
      pid = os.fork()
      if pid > 0:
         sys.exit(0) # Exit first parent.
   except OSError, e:
      sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
      sys.exit(1)

   # Decouple from parent environment.
   os.chdir("/")
   os.umask(0)
   os.setsid()

   # Do second fork.
   try:
      pid = os.fork()
      if pid > 0:
         sys.exit(0) # Exit second parent.
   except OSError, e:
      sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
      sys.exit(1)

   # Process is now a daemon!

   # Open file descriptors
   if not stderr:
      stderr = stdout
   si = file(stdin, 'r')
   so = file(stdout, 'a+')
   se = file(stderr, 'a+', 0)

   # Redirect standard file descriptors.
   os.dup2(si.fileno(), sys.stdin.fileno())
   os.dup2(so.fileno(), sys.stdout.fileno())
   os.dup2(se.fileno(), sys.stderr.fileno())

   if pidfile:
      pf = file(pidfile, 'w+')
      pf.write('%d\n' % os.getpid())
      pf.close()

if __name__ == '__main__':
   if '-debug' in sys.argv:
      # For debugging, it is handy to be able to run the servers
      # without being a service on Windows or a daemon on Linux.
      RunServer()
   elif os.name == 'nt':
      # Install as a Windows Service on NT
      win32serviceutil.HandleCommandLine(vrjclusterserver)
   elif platform.system() == 'Linux':
      if '-log' in sys.argv:
         log = '/var/log/vrjclusterserver.log'
      else:
         log = '/dev/null'

      # Run as a daemon on Linux
      daemonize(pidfile='/var/run/vrjclusterserver.pid', stdout=log)

      # Now that we've successfully forked as a daemon, run the server
      RunServer()
