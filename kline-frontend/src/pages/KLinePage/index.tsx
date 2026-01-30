import { useEffect } from 'react';
import { message } from 'antd';
import { StockSelector } from '../../components/StockSelector';
import { KLineChart } from '../../components/KLineChart';
import { LogPanel } from '../../components/LogPanel';
import { useKLineStore } from '../../store/useKLineStore';
import { klineApi } from '../../api/kline';
import type { Stock } from '../../types/stock';
import { logger } from '../../store/useLogStore';
import './index.css';

export const KLinePage: React.FC = () => {
  const {
    selectedStock,
    stockInfo,
    klineData,
    loading,
    setSelectedStock,
    setStockInfo,
    setKLineData,
    setLoading,
  } = useKLineStore();

  const handleStockChange = (code: string, stock: Stock) => {
    logger.info(`主页面: 股票已选择 - ${code} ${stock.name}`);
    setSelectedStock(code);
    setStockInfo({ code: stock.code, name: stock.name });
    // 选择股票后自动查询数据
    fetchKLineData(code);
  };

  const fetchKLineData = async (code?: string) => {
    const stockCode = code || selectedStock;

    if (!stockCode) {
      logger.warning('主页面: 未选择股票，终止查询');
      return;
    }

    logger.info(`主页面: 开始获取K线数据 - ${stockCode}`);

    // 查询所有可用数据（从2010年到2025年底）
    const startDate = '2010-01-01';
    const endDate = '2025-12-31';

    logger.info(`主页面: 查询参数 - 股票:${stockCode}, 日期:${startDate}~${endDate}`);

    setLoading(true);
    try {
      logger.info('主页面: 调用API获取K线数据...');
      const response = await klineApi.getKLineData(
        stockCode,
        startDate,
        endDate,
        'none'
      );

      logger.info('主页面: API响应', { code: response.code, count: response.data?.count });

      if (response.code === 0) {
        setKLineData(response.data.klines);
        setStockInfo(response.data.stock_info);
        logger.success(`主页面: 成功加载 ${response.data.count} 个交易日数据`);

        if (response.data.klines.length > 0) {
          const firstDate = response.data.klines[0].date;
          const lastDate = response.data.klines[response.data.klines.length - 1].date;
          message.success(`已加载 ${response.data.count} 个交易日数据 (${firstDate} ~ ${lastDate})`);
        }
      } else {
        logger.error('主页面: API返回错误', response);
        message.error(response.message || '加载失败');
      }
    } catch (error: any) {
      logger.error('主页面: 获取K线数据异常', {
        message: error.message,
        response: error.response?.data,
      });
      message.error(error.response?.data?.detail || '获取K线数据失败');
    } finally {
      setLoading(false);
      logger.info('主页面: 查询完成');
    }
  };

  // 组件挂载时的日志
  useEffect(() => {
    logger.info('主页面: 组件已挂载');
    logger.info(`主页面: 初始状态 - 股票:${selectedStock || '未选择'}`);
  }, []);

  return (
    <div className="kline-page">
      <div className="kline-header">
        <h1>股票K线图系统</h1>
      </div>

      <div className="kline-toolbar">
        <div className="stock-selector-wrapper">
          <span className="selector-label">选择股票：</span>
          <StockSelector value={selectedStock || undefined} onChange={handleStockChange} />
          <span className="selector-hint">
            {loading ? '加载中...' : selectedStock ? `已选择 ${stockInfo?.name || ''}` : '请输入股票代码或名称搜索'}
          </span>
        </div>
      </div>

      <div className="kline-chart-container">
        <KLineChart
          data={klineData}
          stockName={stockInfo ? `${stockInfo.name} (${stockInfo.code})` : 'K线图'}
          loading={loading}
        />
      </div>

      {/* 日志面板 */}
      <LogPanel />
    </div>
  );
};
