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


import elementtree.ElementTree as ET
from xml.dom.minidom import parseString
import Pyro.core
from Pyro.protocol import getHostname
import threading
import time, types, re, sys

from PyQt4 import QtCore, QtGui
from Queue import Queue

import copy
import socket

import modules.ClusterSettingsResource

ERROR = 0
LINUX = 1
WIN = 2
WINXP = 3
MACOS = 4
MACOSX = 5
HPUX = 6
AIX = 7
SOLARIS = 8

OsNameMap = {ERROR  : 'Error',
             LINUX  : 'Linux',
             WIN    : 'Windows',
             WINXP  : 'Windows XP',
             MACOS  : 'MacOS',
             MACOSX : 'MacOS X',
             HPUX   : 'HP UX',
             AIX    : 'AIX',
             SOLARIS : 'Solaris'}

class EnsembleModel(QtCore.QAbstractListModel):
   def __init__(self, ensemble, parent=None):
      QtCore.QAbstractListModel.__init__(self, parent)

      self.mEventManager = None
      self.mEnsemble = ensemble

      self.mIcons = {}
      self.mIcons[ERROR] = QtGui.QIcon(":/ClusterSettings/images/error2.png")
      self.mIcons[WIN] = QtGui.QIcon(":/ClusterSettings/images/win_xp.png")
      self.mIcons[WINXP] = QtGui.QIcon(":/ClusterSettings/images/win_xp.png")
      self.mIcons[LINUX] = QtGui.QIcon(":/ClusterSettings/images/linux2.png")

   def init(self, eventManager):
      self.mEventManager = eventManager

      # XXX: Should we manage this signal on a per node basis? We would have
      #      to make each node generate a signal when it's OS changed and
      #      listen for it here anyway.
      # Register to receive signals from all nodes about their current os.
      self.mEventManager.connect("*", "settings.os", self.onReportOs)

   def onReportOs(self, nodeId, os):
      try:
         print "onReportOs [%s] [%s]" % (nodeId, os)
         changed = False
         for node in self.mEnsemble.mNodes:
            if node.getIpAddress() == nodeId:
               if os != node.mPlatform:
                  node.mPlatform = os
                  changed = True

         if changed:
            # TODO: Only send changed signal when nodes really changed os.
            self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), QtCore.QModelIndex(), QtCore.QModelIndex())
      except Exception, ex:
         print "ERROR: ", ex

   def insertRows(self, row, count, parent):
      self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
      for i in xrange(count):
         new_element = ET.SubElement(self.mElement, "cluster_node", name="NewNode", hostname="NewNode")
         new_node = ClusterNode(new_element)
         self.mEnsemble.mNodes.insert(row, new_node);
      self.refreshConnections()
      self.endInsertRows()
      self.emit(QtCore.SIGNAL("rowsInserted(int, int)"), row, count)
      return True

   def removeRows(self, row, count, parent):
      self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
      self.emit(QtCore.SIGNAL("rowsAboutToBeRemoved(int, int)"), row, count)
      for i in xrange(count):
         node = self.mEnsemble.mNodes[row]

         # Remove node's element from XML tree.
         self.mElement.remove(node.mElement)
         # Remove node data structure
         self.mEnsemble.mNodes.remove(node)
      self.endRemoveRows()
      return True

   def removeNode(self, node):
      assert not None == node
      index = self.mEnsemble.mNodes.index(node)
      self.removeRow(index, QtCore.QModelIndex())

   def addNode(self):
      self.insertRow(self.rowCount())

   def data(self, index, role=QtCore.Qt.DisplayRole):
      """ Returns the data representation of each node in the cluster.
      """
      if not index.isValid():
         return QtCore.QVariant()

      # Get the cluster node we want data for.
      cluster_node = self.mEnsemble.getNode(index.row())

      # Return an icon representing the operating system.
      if role == QtCore.Qt.DecorationRole:
         return QtCore.QVariant(self.mIcons[cluster_node.mPlatform])
      # Return the name of the node.
      elif role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
         return QtCore.QVariant(str(cluster_node.getName()))
      elif role == QtCore.Qt.UserRole:
         return cluster_node
       
      return QtCore.QVariant()

   def rowCount(self, parent=QtCore.QModelIndex()):
      """ Returns the number of nodes in the current cluster configuration.
      """
      # If the parent is not valid, then we have no children.
      if parent.isValid():
         return 0
      else:
         return self.mEnsemble.getNumNodes()

   def setData(self, index, value, role):
      """ Doesn't do anything but provide a way to fire a dataChanged event
          for a given model index.
      """
      self.emit(QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"), index, index)
      self.emit(QtCore.SIGNAL("dataChanged(int)"), index.row())
      return True
