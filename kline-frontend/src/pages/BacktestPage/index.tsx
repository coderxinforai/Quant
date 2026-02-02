/**
 * 回测页面
 */
import { useEffect, useState, useRef } from 'react';
import { Card, Row, Col, Button, DatePicker, message, Space } from 'antd';
import { PlayCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import { StockSelector } from '../../components/StockSelector';
import { StrategyPanel } from '../../components/StrategyPanel';
import { BacktestResult } from '../../components/BacktestResult';
import { useBacktestStore } from '../../store/useBacktestStore';
import { backtestApi } from '../../api/backtest';
import { stockApi } from '../../api/stock';
import { logger } from '../../store/useLogStore';
import type { Stock } from '../../types/stock';

const { RangePicker } = DatePicker;

export const BacktestPage: React.FC = () => {
  const {
    strategies,
    setStrategies,
    config,
    setConfig,
    result,
    setResult,
    loading,
    setLoading,
    reset
  } = useBacktestStore();

  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs] | null>(null);
  const resultRef = useRef<HTMLDivElement>(null);

  // 加载策略列表
  useEffect(() => {
    const loadStrategies = async () => {
      try {
        logger.info('回测页面: 加载策略列表');
        const response = await backtestApi.getStrategies();
        setStrategies(response.data);
        logger.success(`回测页面: 加载了 ${response.data.length} 个策略`);
      } catch (error) {
        logger.error('回测页面: 加载策略列表失败', error);
        message.error('加载策略列表失败');
      }
    };

    loadStrategies();
  }, [setStrategies]);

  const handleStockChange = async (code: string, stock: Stock) => {
    setSelectedStock(stock);
    setConfig({ code });
    logger.info('回测页面: 选择股票', { code, name: stock.name });

    // 查询股票的数据时间范围
    try {
      const response = await stockApi.getStockDateRange(code);
      if (response.data.start_date && response.data.end_date) {
        const startDate = dayjs(response.data.start_date);
        const endDate = dayjs(response.data.end_date);
        setDateRange([startDate, endDate]);
        setConfig({
          start_date: response.data.start_date,
          end_date: response.data.end_date
        });
        logger.info('回测页面: 设置日期范围', {
          start: response.data.start_date,
          end: response.data.end_date
        });
      }
    } catch (error) {
      logger.error('回测页面: 获取日期范围失败', error);
    }
  };

  const handleDateRangeChange = (dates: null | [Dayjs | null, Dayjs | null]) => {
    if (dates && dates[0] && dates[1]) {
      setDateRange([dates[0], dates[1]]);
      setConfig({
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD')
      });
    }
  };

  const handleRunBacktest = async () => {
    // 验证必填项
    if (!config.code) {
      message.warning('请选择股票');
      return;
    }
    if (!config.strategy_id) {
      message.warning('请选择策略');
      return;
    }
    if (!config.start_date || !config.end_date) {
      message.warning('请选择日期范围');
      return;
    }

    setLoading(true);
    logger.info('回测页面: 开始回测', config);

    try {
      const response = await backtestApi.runBacktest({
        code: config.code,
        start_date: config.start_date,
        end_date: config.end_date,
        strategy_id: config.strategy_id!,
        strategy_params: config.strategy_params || {},
        initial_capital: config.initial_capital || 100000,
        position_ratio: config.position_ratio || 0.8
      });

      setResult(response.data);
      logger.success('回测页面: 回测完成', {
        total_return: response.data.metrics.total_return,
        trades: response.data.trades.length
      });
      message.success(`回测完成！总收益率: ${response.data.metrics.total_return.toFixed(2)}%`);

      // 滚动到结果区域
      setTimeout(() => {
        resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (error: any) {
      logger.error('回测页面: 回测失败', error);
      message.error(error.response?.data?.detail || '回测失败');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    reset();
    setSelectedStock(null);
    setDateRange(null);
    logger.info('回测页面: 重置配置');
  };

  return (
    <div style={{ padding: 16 }}>
      <Row gutter={16}>
        {/* 左侧：配置面板 */}
        <Col span={8}>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {/* 股票选择 */}
            <Card title="股票选择" size="small">
              <StockSelector
                value={config.code}
                onChange={handleStockChange}
              />
              {selectedStock && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                  {selectedStock.name} ({selectedStock.code})
                </div>
              )}
            </Card>

            {/* 日期范围 */}
            <Card title="回测周期" size="small">
              <RangePicker
                value={dateRange}
                onChange={handleDateRangeChange}
                format="YYYY-MM-DD"
                style={{ width: '100%' }}
                placeholder={['开始日期', '结束日期']}
                disabledDate={(current) => current && current > dayjs().endOf('day')}
              />
            </Card>

            {/* 策略配置 */}
            <StrategyPanel />

            {/* 操作按钮 */}
            <Card size="small">
              <Space style={{ width: '100%', justifyContent: 'center' }}>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleRunBacktest}
                  loading={loading}
                  size="large"
                >
                  运行回测
                </Button>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleReset}
                  disabled={loading}
                  size="large"
                >
                  重置
                </Button>
              </Space>
            </Card>
          </Space>
        </Col>

        {/* 右侧：回测结果 */}
        <Col span={16} ref={resultRef}>
          <div style={{ maxHeight: 'calc(100vh - 100px)', overflowY: 'auto' }}>
            <BacktestResult result={result} />
          </div>
        </Col>
      </Row>
    </div>
  );
};
