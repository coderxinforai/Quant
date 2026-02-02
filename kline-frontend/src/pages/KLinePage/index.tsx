import { useEffect } from 'react';
import { message, DatePicker } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { StockSelector } from '../../components/StockSelector';
import { AdjTypeSelector } from '../../components/AdjTypeSelector';
import { PeriodSelector } from '../../components/PeriodSelector';
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
    adjType,
    period,
    tradeDate,
    setSelectedStock,
    setStockInfo,
    setKLineData,
    setLoading,
    setAdjType,
    setPeriod,
    setTradeDate,
  } = useKLineStore();

  const handleStockChange = (code: string, stock: Stock) => {
    logger.info(`主页面: 股票已选择 - ${code} ${stock.name}`);
    setSelectedStock(code);
    setStockInfo({ code: stock.code, name: stock.name });
    // 选择股票后自动查询数据
    fetchKLineData(code);
  };

  const fetchKLineData = async (code?: string, adj?: string, prd?: string, date?: string) => {
    const stockCode = code || selectedStock;
    const adjTypeToUse = adj !== undefined ? adj : adjType;
    const periodToUse = prd !== undefined ? prd : period;
    const tradeDateToUse = date !== undefined ? date : tradeDate;

    if (!stockCode) {
      logger.warning('主页面: 未选择股票，终止查询');
      return;
    }

    // 判断是否为分钟级周期
    const isMinutePeriod = periodToUse.includes('min');

    if (isMinutePeriod) {
      // 分钟级K线：需要指定交易日期
      if (!tradeDateToUse) {
        // 默认使用最近交易日（今天或最近的工作日）
        const today = dayjs();
        const defaultDate = today.format('YYYY-MM-DD');
        setTradeDate(defaultDate);
        logger.info(`主页面: 分钟K线未指定日期，使用默认日期: ${defaultDate}`);
        return;
      }

      logger.info(`主页面: 开始获取分钟K线数据 - ${stockCode}, 日期:${tradeDateToUse}`);

      const interval = parseInt(periodToUse.replace('min', ''));
      logger.info(`主页面: 查询参数 - 股票:${stockCode}, 日期:${tradeDateToUse}, 周期:${interval}分钟, 复权:${adjTypeToUse}`);

      setLoading(true);
      try {
        logger.info('主页面: 调用API获取分钟K线数据...');
        const response = await klineApi.getMinuteKLineData(
          stockCode,
          tradeDateToUse,
          interval,
          adjTypeToUse
        );

        logger.info('主页面: API响应', { code: response.code, count: response.data?.count });

        if (response.code === 0) {
          setKLineData(response.data.klines);
          setStockInfo(response.data.stock_info);
          logger.success(`主页面: 成功加载 ${response.data.count} 个分钟K线数据`);

          message.success(`已加载 ${response.data.count} 个${interval}分钟K线数据 (${tradeDateToUse})`);
        } else {
          logger.error('主页面: API返回错误', response);
          message.error(response.message || '加载失败');
        }
      } catch (error: any) {
        logger.error('主页面: 获取分钟K线数据异常', {
          message: error.message,
          response: error.response?.data,
        });
        message.error(error.response?.data?.detail || '获取分钟K线数据失败');
      } finally {
        setLoading(false);
        logger.info('主页面: 查询完成');
      }
    } else {
      // 日/周/月/年K线
      logger.info(`主页面: 开始获取K线数据 - ${stockCode}`);

      // 查询所有可用数据（从2000年到2025年底）
      const startDate = '2000-01-01';
      const endDate = '2025-12-31';

      logger.info(`主页面: 查询参数 - 股票:${stockCode}, 日期:${startDate}~${endDate}, 复权:${adjTypeToUse}, 周期:${periodToUse}`);

      setLoading(true);
      try {
        logger.info('主页面: 调用API获取K线数据...');
        const response = await klineApi.getKLineData(
          stockCode,
          startDate,
          endDate,
          adjTypeToUse,
          periodToUse
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
        <div className="stock-selector-wrapper" style={{ marginTop: '12px' }}>
          <span className="selector-label">周期：</span>
          <PeriodSelector
            value={period}
            onChange={(val) => {
              setPeriod(val);
              // 如果切换到分钟周期，需要设置默认日期
              if (val.includes('min') && !tradeDate) {
                const defaultDate = dayjs().format('YYYY-MM-DD');
                setTradeDate(defaultDate);
              }
              if (selectedStock) {
                fetchKLineData(selectedStock, adjType, val, tradeDate || undefined);
              }
            }}
          />
          {period.includes('min') && (
            <>
              <span className="selector-label" style={{ marginLeft: '20px' }}>交易日期：</span>
              <DatePicker
                value={tradeDate ? dayjs(tradeDate) : null}
                onChange={(date: Dayjs | null) => {
                  const dateStr = date ? date.format('YYYY-MM-DD') : null;
                  setTradeDate(dateStr);
                  if (selectedStock && dateStr) {
                    fetchKLineData(selectedStock, adjType, period, dateStr);
                  }
                }}
                format="YYYY-MM-DD"
                size="small"
              />
            </>
          )}
          <span className="selector-label" style={{ marginLeft: '20px' }}>复权方式：</span>
          <AdjTypeSelector
            value={adjType}
            onChange={(val) => {
              setAdjType(val);
              if (selectedStock) {
                fetchKLineData(selectedStock, val, period, tradeDate || undefined);
              }
            }}
          />
        </div>
      </div>

      <div className="kline-chart-container">
        <KLineChart
          data={klineData}
          stockName={stockInfo ? `${stockInfo.name} (${stockInfo.code})` : 'K线图'}
          loading={loading}
          period={period}
        />
      </div>

      {/* 日志面板 */}
      <LogPanel />
    </div>
  );
};
