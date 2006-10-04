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

import os
import os.path
import popen2
import pwd
import re


def changeToUser(uid, gid):
   # NOTE: os.setgid() must be called first or else we will get an "operation
   # not permitted" error.
   os.setgid(gid)
   os.setuid(uid)

def changeToUserName(userName):
   pw_entry = pwd.getpwnam(userName)
   changeToUser(pw_entry[2], pw_entry[3])

def getUserXauthFile(userName):
   pw_entry = pwd.getpwnam(userName)
   user_home = pw_entry[5]
   return os.path.join(user_home, '.Xauthority')

def addAuthority(user, xauthCmd, xauthFile):
   '''
   Pulls the X authority key from the named file and adds it to the named
   user's .Xauthority file if necessary. A tuple containing the the display
   name (suitable for use as the value of the DISPLAY environment variable)
   and a boolean value indicating whether the user's .Xauthority file had to
   be updated is returned. If this boolean value is True, then it should be
   assumed that the user is logged on to the local workstation, and the
   authority should not be removed later using removeAuthority().
   '''
   # Pull out the system X authority key. It will be the first line of the
   # output from running 'xauth list'.
   (child_stdout, child_stdin) = \
      popen2.popen2('%s -f %s list' % (xauthCmd, xauthFile))
   host_str = '%s/unix' % os.environ['HOSTNAME']
   line = child_stdout.readline()
   child_stdout.close()
   child_stdin.close()

   key_str = re.sub('#ffff##', host_str, line)
   display_key_re = re.compile(r'\s*(\S+)\s+(\S+)\s+(\S+)\s*')
   key_match = display_key_re.match(key_str)
   key = (key_match.group(1), key_match.group(2), key_match.group(3))
   print key

   (child_stdout, child_stdin) = \
      popen2.popen2('%s -f %s list' % (xauthCmd, getUserXauthFile(user)))
   lines = child_stdout.readlines()
   child_stdout.close()
   child_stdin.close()

   has_key = False

   for l in lines:
      key_match = display_key_re.match(l)
      user_key = (key_match.group(1), key_match.group(2), key_match.group(3))
      if user_key == key:
         has_key = True
         break

   print "has_key =", has_key

   if not has_key:
      pid = os.fork()
      if pid == 0:
         # Run the xauth(1) command as the user.
         changeToUserName(user)
         os.execl(xauthCmd, xauthCmd, '-f', getUserXauthFile(user), 'add',
                  key[0], key[1], key[2])

      # Wait on the child to complete.
      os.waitpid(pid, 0)

   return (key[0], has_key)

def removeAuthority(user, xauthCmd, displayName):
   '''
   Removes the named display from the given user's .Xauthority file.

   NOTE: This relies upon the user running maestrod to have write access to
         the named user's .Xauthority file.
   '''
   pid = os.fork()
   if pid == 0:
      # Run the xauth(1) command as the named user.
      changeToUserName(user)
      os.execl(xauthCmd, xauthCmd, '-f', getUserXauthFile(user), 'remove',
               displayName)

   # Wait on the child to complete.
   os.waitpid(pid, 0)
