import { Tabs } from 'antd';
import { KLinePage } from './pages/KLinePage';
import { ComparePage } from './pages/ComparePage';
import { BacktestPage } from './pages/BacktestPage';
import './App.css';

function App() {
  const items = [
    {
      key: 'kline',
      label: 'K线图',
      children: <KLinePage />,
    },
    {
      key: 'compare',
      label: '多股对比',
      children: <ComparePage />,
    },
    {
      key: 'backtest',
      label: '策略回测',
      children: <BacktestPage />,
    },
  ];

  return (
    <div className="app-container">
      <Tabs
        defaultActiveKey="kline"
        items={items}
        centered
        size="large"
        className="app-tabs"
      />
    </div>
  );
}

export default App;
