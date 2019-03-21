# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
'''
进程模块
'''

import ctypes
import win32process
import win32con
import win32api
import win32security
import time
import pywintypes

from qt4c import wintypes

INVALID_HANDLE_VALUE = -1

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    '''
    
    :desc: The PROCESS_MEMORY_COUNTERS structure contains the memory statistics for a process.
    '''
    _fields_ = [
        ('cb', ctypes.c_ulong),
        ('PageFaultCount', ctypes.c_ulong),
        ('PeakWorkingSetSize', ctypes.c_ulong),
        ('WorkingSetSize', ctypes.c_ulong),
        ('QuotaPeakPagedPoolUsage', ctypes.c_ulong),
        ('QuotaPagedPoolUsage', ctypes.c_ulong),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_ulong),
        ('QuotaNonPagedPoolUsage', ctypes.c_ulong),
        ('PagefileUsage', ctypes.c_ulong),
        ('PeakPagefileUsage', ctypes.c_ulong)]
    
def getMememoryUsage(pid=None):
    '''获取进程内存数值
    
    :type pid: int 
    :param pid: 进程Id，默认值为None，代表自身进程pid
    :rtype: int
    :requires: 内存使用,以KB为单位
    '''
    if pid is None:
        pid = win32process.GetCurrentProcessId()
        
    if win32process.GetProcessVersion(pid) <= 0:
        return 0
    
    pmc = PROCESS_MEMORY_COUNTERS()

    
    hProcess = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid).Detach()
    pmc = win32process.GetProcessMemoryInfo(hProcess)
    #内存使用(KB)
    nWorkingSetSize = pmc['WorkingSetSize'] / 1024
    win32api.CloseHandle(hProcess)
    return nWorkingSetSize

class Process(object):
    '''进程类
    '''
    def __init__(self, pid):
        self._pid = pid
    
    @property
    def ProcessName(self):
        TH32CS_SNAPPROCESS = 0x00000002
        pe = wintypes.PROCESSENTRY32() 
        hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe.dwSize = ctypes.sizeof(wintypes.PROCESSENTRY32)
        if not ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
            win32api.CloseHandle(hSnapshot)
            return None
        
        while 1:
            if pe.th32ProcessID == self._pid:
                win32api.CloseHandle(hSnapshot)
                return pe.szExeFile
            
            if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                break
            
        win32api.CloseHandle(hSnapshot)
        return None
    
#    @property
#    def CreatedTime(self):
#        pass
    
    @property
    def Live(self):
        return (win32process.GetProcessVersion(self._pid) > 0)
    
    @property
    def ProcessId(self):
        return self._pid
    
    def waitForQuit(self, timeout=10, interval=0.5):
        '''在指定的时间内等待退出
        
        :return: 如果在指定的时间内退出，返回True；否则返回False
        '''
        if not self.Live:
            return True
        
        from qt4c import util
        from qt4c.exceptions import TimeoutError
        try: 
            util.Timeout(timeout, interval).waitObjectProperty(self, "Live", False)
        except TimeoutError:
            return False
        return True
    
    def _adjustProcessPrivileges(self):
        """提升权限"""
        hCurPro = win32process.GetCurrentProcess()
        hToken = win32security.OpenProcessToken(hCurPro, win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY)
        luid = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
        if luid:
            newState = [(luid, win32security.SE_PRIVILEGE_ENABLED),]
            win32security.AdjustTokenPrivileges(hToken, 0, newState)
        win32api.CloseHandle(hToken)
    
    def terminate(self):
        '''终止进程
        '''
        from qt4c.wincontrols import TrayNotifyBar
        tb = TrayNotifyBar()
        item = tb[self._pid]
        if item:
            try:
                item.destroy()
            except pywintypes.error as e:
                if e[0] != 1460:
                    raise e
            
        self._adjustProcessPrivileges()
        try:
            hProcess = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, self._pid).Detach()
            win32process.TerminateProcess(hProcess, 0)
            win32api.CloseHandle(hProcess)
        except:
            pass
    
    @property
    def ChildProcesses(self):
        '''
        返回进程的所有子进程列表（不包括孙子进程）
        '''
        processes = []
        TH32CS_SNAPPROCESS = 0x00000002
        pe = wintypes.PROCESSENTRY32() 
        hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe.dwSize = ctypes.sizeof(wintypes.PROCESSENTRY32)
        if not ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
            win32api.CloseHandle(hSnapshot)
            return None
        
        while 1:
            if pe.th32ParentProcessID == self._pid:
                processes.append(Process(pe.th32ProcessID))
            if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                break
            
        win32api.CloseHandle(hSnapshot)
        return processes
        
class ProcessSet(object):
    '''进程集合
    '''
    def __init__(self, processes):
        self._processes = processes
        
    def terminate(self):
        '''终止进程
        '''
        for process in self._processes:
            process.terminate()
    
#    def sort(self):
#        """按照进程创建时间排序"""
#        pass
    
    def waitForQuit(self, timeout=10, interval=0.5):
        '''在指定的时间内等待一系列进程退出
        
        :return: 如果在指定的时间内所有进程退出，返回True；否则返回False
        '''
        if not self._processes:
            return True
        processes = self._processes[:]
        while timeout > 0:
            if not processes:
                return True 
            for process in processes:
                if not process.Live:
                    processes.remove(process)
            timeout = timeout - interval
            time.sleep(interval)
        return False
    
    @property
    def Count(self):
        return len(self._processes)
        
    @property
    def ProcessIds(self):
        '''返回PID列表
        '''
        rlt = []
        for process in self._processes:
            rlt.append(process.ProcessId)
        return rlt
        
class ProcessFactory(object):
    '''进程工厂
    '''
    @staticmethod
    def getProcesses(processName):
        processes = []
        
        TH32CS_SNAPPROCESS = 0x00000002
        pe = wintypes.PROCESSENTRY32() 
        hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if INVALID_HANDLE_VALUE == hSnapshot:
            return processes
        pe.dwSize = ctypes.sizeof(wintypes.PROCESSENTRY32)
        if not ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
            win32api.CloseHandle(hSnapshot)
            return ProcessSet(processes)
        
        while 1:
            if pe.szExeFile.upper() == processName.upper():
                processes.append(Process(pe.th32ProcessID))
            
            if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                break
        win32api.CloseHandle(hSnapshot)
        return ProcessSet(processes)
    
    @staticmethod
    def getProcessesByExePath(ExePath):
        """
        获取符合指定EXE文件完整路径的进程
        """
        processName = ExePath[ExePath.rfind('\\')+1:]
        processIds = ProcessFactory.getProcesses(processName).ProcessIds
        processes = []
        for processId in processIds:
            TH32CS_SNAPMODULE = 0x00000008
            hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, processId)
            if INVALID_HANDLE_VALUE == hSnapshot:
                return ProcessSet(processes)
            me = wintypes.MODULEENTRY32() 
            me.dwSize = ctypes.sizeof(wintypes.MODULEENTRY32)
            if not ctypes.windll.kernel32.Module32First(hSnapshot, ctypes.byref(me)):
                win32api.CloseHandle(hSnapshot)
                continue
            if me.szExePath.decode('gbk').upper() == ExePath.decode('utf8').upper():
                processes.append(Process(me.th32ProcessID))
            win32api.CloseHandle(hSnapshot)
        return ProcessSet(processes)
    
    @staticmethod
    def getProcess(processId):
        return Process(processId)
    
if __name__ == '__main__':
    pass
