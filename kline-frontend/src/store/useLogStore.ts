import { create } from 'zustand';

export type LogLevel = 'info' | 'success' | 'warning' | 'error';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: any;
}

interface LogStore {
  logs: LogEntry[];
  maxLogs: number;
  addLog: (level: LogLevel, message: string, data?: any) => void;
  clearLogs: () => void;
}

export const useLogStore = create<LogStore>((set) => ({
  logs: [],
  maxLogs: 100,

  addLog: (level, message, data) => {
    const entry: LogEntry = {
      id: Date.now().toString() + Math.random(),
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      level,
      message,
      data,
    };

    // 同时输出到控制台
    const consoleMsg = `[${entry.timestamp}] [${level.toUpperCase()}] ${message}`;
    switch (level) {
      case 'error':
        console.error(consoleMsg, data);
        break;
      case 'warning':
        console.warn(consoleMsg, data);
        break;
      case 'success':
        console.log(`%c${consoleMsg}`, 'color: green', data);
        break;
      default:
        console.log(consoleMsg, data);
    }

    set((state) => ({
      logs: [...state.logs.slice(-state.maxLogs + 1), entry],
    }));
  },

  clearLogs: () => set({ logs: [] }),
}));

// 导出便捷方法
export const logger = {
  info: (message: string, data?: any) => useLogStore.getState().addLog('info', message, data),
  success: (message: string, data?: any) => useLogStore.getState().addLog('success', message, data),
  warning: (message: string, data?: any) => useLogStore.getState().addLog('warning', message, data),
  error: (message: string, data?: any) => useLogStore.getState().addLog('error', message, data),
};
