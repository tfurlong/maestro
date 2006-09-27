# Maestro is Copyright (C) 2006 by Infiscape
#
# Original Author: Aron Bierbaum
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

import sys, os, platform

import util.EventManager
import re

ps_regex = re.compile(r"^(\S+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S.+:\d+\s+\d+)\s+(\S.*)")

class ProcessManagementService:
   def __init__(self):
      if "win32" == sys.platform:
         from util import wmi
         self.mWMIConnection = wmi.WMI()
      else:
         pass

   def init(self, eventManager, settings):
      self.mEventManager = eventManager
      self.mEventManager.connect("*", "process.get_procs", self.onGetProcs)
      self.mEventManager.connect("*", "process.terminate_proc", self.onTerminateProc)

   def onGetProcs(self, nodeId, avatar):
      """ Slot that returns a process list to the calling maestro client.

          @param nodeId: IP address of maestro client that sent event.
          @param avatar: System avatar that represents the remote user.
      """
      procs = self._getProcs()
      self.mEventManager.emit(nodeId, "process.procs", (procs,))

   def onTerminateProc(self, nodeId, avatar, pid):
      """ Slot that terminates the process that has the given pid.

          @param nodeId: IP address of maestro client that sent event.
          @param avatar: System avatar that represents the remote user.
          @param pid: Process ID of the process to terminate.
      """
      if "win32" == sys.platform:
         from util import wmi
         print "Trying to terminate process: ", pid
         for process in self.mWMIConnection.Win32_Process(ProcessId=pid):
            print "Terminating: %s %s" % (process.ProcessId, process.Name)
            process.Terminate()
      else:
         os.system('kill ' + str(pid))

   def _getProcs(self):
      if "win32" == sys.platform:
         from util import wmi
         procs = []
         time_str = ""
         for process in self.mWMIConnection.Win32_Process():
            (domain, return_value, user) = process.GetOwner()
            if process.CreationDate is not None:
               creation_date = wmi.to_time(process.CreationDate)
               time_str = "%02d/%02d/%d %02d:%02d:%02d" % (creation_date[1],
                  creation_date[2], creation_date[0], creation_date[3],
                  creation_date[4], creation_date[5])
            procs.append((process.Name, process.ProcessId,
               process.ParentProcessId, user, time_str,
               process.CommandLine))
         return procs
      else:
         procs = []
         (stdin, stdout_stderr) = os.popen4("ps -NU root -Nu root -o comm,pid,ppid,user,lstart,args h")
         for l in stdout_stderr.readlines():
            match_obj = ps_regex.match(l)
            if match_obj is not None:
               procs.append(match_obj.groups())
         return procs

if __name__ == "__main__":
   p = ProcessManagementService()
   p._getProcs()
