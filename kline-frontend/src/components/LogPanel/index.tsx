import { useState } from 'react';
import { Button, Badge } from 'antd';
import { useLogStore } from '../../store/useLogStore';
import type { LogLevel } from '../../store/useLogStore';
import './index.css';

export const LogPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { logs, clearLogs } = useLogStore();

  const getLevelColor = (level: LogLevel): string => {
    switch (level) {
      case 'error':
        return '#ff4d4f';
      case 'warning':
        return '#faad14';
      case 'success':
        return '#52c41a';
      default:
        return '#1890ff';
    }
  };

  const getLevelText = (level: LogLevel): string => {
    switch (level) {
      case 'error':
        return '错误';
      case 'warning':
        return '警告';
      case 'success':
        return '成功';
      default:
        return '信息';
    }
  };

  return (
    <>
      {/* 悬浮按钮 */}
      <div className="log-panel-button">
        <Badge count={logs.length} overflowCount={99}>
          <Button
            type="primary"
            shape="circle"
            size="large"
            onClick={() => setIsOpen(!isOpen)}
          >
            📋
          </Button>
        </Badge>
      </div>

      {/* 日志面板 */}
      {isOpen && (
        <div className="log-panel">
          <div className="log-panel-header">
            <h3>系统日志 ({logs.length})</h3>
            <div>
              <Button size="small" onClick={clearLogs} style={{ marginRight: 8 }}>
                清空
              </Button>
              <Button size="small" onClick={() => setIsOpen(false)}>
                关闭
              </Button>
            </div>
          </div>
          <div className="log-panel-content">
            {logs.length === 0 ? (
              <div className="log-empty">暂无日志</div>
            ) : (
              logs.map((log) => (
                <div key={log.id} className="log-entry">
                  <span className="log-timestamp">{log.timestamp}</span>
                  <span
                    className="log-level"
                    style={{ color: getLevelColor(log.level) }}
                  >
                    [{getLevelText(log.level)}]
                  </span>
                  <span className="log-message">{log.message}</span>
                  {log.data && (
                    <pre className="log-data">
                      {JSON.stringify(log.data, null, 2)}
                    </pre>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </>
  );
};
