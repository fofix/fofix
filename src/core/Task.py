#####################################################################
# -*- coding: iso-8859-1 -*-                                        #
#                                                                   #
# Frets on Fire                                                     #
# Copyright (C) 2006 Sami Kyöstilä                                  #
#				2013 FoFiX Team                                     #
#                                                                   #
# This program is free software; you can redistribute it and/or     #
# modify it under the terms of the GNU General Public License       #
# as published by the Free Software Foundation; either version 2    #
# of the License, or (at your option) any later version.            #
#                                                                   #
# This program is distributed in the hope that it will be useful,   #
# but WITHOUT ANY WARRANTY; without even the implied warranty of    #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the     #
# GNU General Public License for more details.                      #
#                                                                   #
# You should have received a copy of the GNU General Public License #
# along with this program; if not, write to the Free Software       #
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,        #
# MA  02110-1301, USA.                                              #
#####################################################################

class Task(object):
    def __init__(self):
        pass

    def started(self):
        pass

    def stopped(self):
        pass

    def run(self, ticks):
        pass

class TaskEngine(object):
    def __init__(self, engine):
        
        self.engine = engine
        
        # self.tasks contains a list of dictionaries.
        # each contain: task instance, synced or not, and paused or not
        self.tasks = []
        self.currentTask = None
        
    
    def checkTask(self, task):
        ''' Check if a task exists '''
        
        for taskData in self.tasks:
            if taskData['task'] is task:
                return True
        
        return False
    
    def addTask(self, task, synced = True):
        ''' Add a task '''
        
        if not self.checkTask(task):
            self.tasks.append({'task': task, 'synced': synced, 'paused': False})
            task.started()
    
    def removeTask(self, task):
        ''' Remove a task '''
        
        for taskData in self.tasks:
            if taskData['task'] is task:
                self.tasks.remove(taskData)
                task.stopped()
                break
    
    def pauseTask(self, task):
        ''' Pause a task '''

        for taskData in self.tasks:
            if taskData['task'] is task:
                taskData['paused'] = True
                break
    
    def resumeTask(self, task):
        ''' Resume a paused task '''
        
        for taskData in self.tasks:
            if taskData['task'] is task:
                taskData['paused'] = False
                break
    
    def runTask(self, task, tick=0):
            self.currentTask = task
            task.run(tick)
            self.currentTask = None
    
    def run(self):
        ''' Run one cycle of the task scheduler engine.'''
        if not self.tasks:
            return False
        
        # Synced tasks
        for taskData in self.tasks:
            if taskData['paused'] or not taskData['synced']:
                continue
            
            self.runTask(taskData['task'], tick=self.engine.tickDelta)

        # Unsynced tasks
        for taskData in self.tasks:
            if taskData['paused']or taskData['synced']:
                continue
            
            self.runTask(taskData['task'])
        return True
