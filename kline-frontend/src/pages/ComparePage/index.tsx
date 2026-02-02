import { useState } from 'react';
import { message, DatePicker, Radio, Space } from 'antd';
import dayjs, { Dayjs } from 'dayjs';
import { MultiStockSelector } from '../../components/MultiStockSelector';
import { PeriodSelector } from '../../components/PeriodSelector';
import { CompareChart } from '../../components/CompareChart';
import type { CompareSeriesData, CompareDataItem } from '../../components/CompareChart';
import { LogPanel } from '../../components/LogPanel';
import { klineApi } from '../../api/kline';
import type { Stock } from '../../types/stock';
import { logger } from '../../store/useLogStore';
import './index.css';

const { RangePicker } = DatePicker;

type CompareMode = 'change' | 'price';

export const ComparePage: React.FC = () => {
  const [selectedCodes, setSelectedCodes] = useState<string[]>([]);
  const [selectedStocks, setSelectedStocks] = useState<Stock[]>([]);
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(6, 'month'),
    dayjs(),
  ]);
  const [period, setPeriod] = useState<string>('day');
  const [compareMode, setCompareMode] = useState<CompareMode>('change');
  const [loading, setLoading] = useState(false);
  const [chartSeries, setChartSeries] = useState<CompareSeriesData[]>([]);

  const handleStockChange = (codes: string[], stocks: Stock[]) => {
    logger.info(`对比页面: 股票已选择 - ${codes.length} 只`, codes);
    setSelectedCodes(codes);
    setSelectedStocks(stocks);

    // 自动查询数据
    if (codes.length > 0) {
      fetchCompareData(codes, stocks);
    } else {
      setChartSeries([]);
    }
  };

  const fetchCompareData = async (
    codes?: string[],
    stocks?: Stock[],
    prd?: string,
    mode?: CompareMode,
    range?: [Dayjs, Dayjs]
  ) => {
    const codesToUse = codes || selectedCodes;
    const stocksToUse = stocks || selectedStocks;
    const periodToUse = prd || period;
    const modeToUse = mode !== undefined ? mode : compareMode;
    const rangeToUse = range || dateRange;

    if (codesToUse.length === 0) {
      logger.warning('对比页面: 未选择股票，终止查询');
      return;
    }

    logger.info(
      `对比页面: 开始获取对比数据 - ${codesToUse.length} 只股票, 周期: ${periodToUse}, 模式: ${modeToUse}`
    );

    const startDate = rangeToUse[0].format('YYYY-MM-DD');
    const endDate = rangeToUse[1].format('YYYY-MM-DD');

    logger.info(`对比页面: 日期范围 - ${startDate} ~ ${endDate}`);

    setLoading(true);
    try {
      // 并行查询所有股票的数据
      const promises = codesToUse.map((code) =>
        klineApi.getKLineData(code, startDate, endDate, 'none', periodToUse)
      );

      logger.info('对比页面: 并行调用API获取多股数据...');
      const responses = await Promise.all(promises);

      logger.info('对比页面: 所有API响应已接收');

      // 处理返回的数据
      const series: CompareSeriesData[] = [];

      for (let i = 0; i < responses.length; i++) {
        const response = responses[i];
        const stock = stocksToUse[i];

        if (response.code === 0 && response.data.klines.length > 0) {
          const klines = response.data.klines;

          // 计算数据
          let data: CompareDataItem[];
          if (modeToUse === 'change') {
            // 涨跌幅模式：基准价为第一天的收盘价
            const basePrice = klines[0].close;
            data = klines.map((k) => ({
              date: k.date,
              value: ((k.close - basePrice) / basePrice) * 100,
            }));
          } else {
            // 价格模式：直接使用收盘价
            data = klines.map((k) => ({
              date: k.date,
              value: k.close,
            }));
          }

          series.push({
            code: stock.code,
            name: stock.name,
            data,
          });

          logger.info(`对比页面: ${stock.name} (${stock.code}) 数据已处理 - ${klines.length} 条`);
        } else {
          logger.warning(`对比页面: ${stock.name} (${stock.code}) 数据获取失败或为空`);
        }
      }

      setChartSeries(series);
      logger.success(`对比页面: 成功加载 ${series.length} 只股票的对比数据`);

      if (series.length > 0) {
        message.success(`已加载 ${series.length} 只股票的对比数据`);
      } else {
        message.warning('所有股票数据均为空');
      }
    } catch (error: any) {
      logger.error('对比页面: 获取对比数据异常', {
        message: error.message,
        response: error.response?.data,
      });
      message.error(error.response?.data?.detail || '获取对比数据失败');
    } finally {
      setLoading(false);
      logger.info('对比页面: 查询完成');
    }
  };

  const handlePeriodChange = (val: string) => {
    setPeriod(val);
    if (selectedCodes.length > 0) {
      fetchCompareData(undefined, undefined, val);
    }
  };

  const handleCompareModeChange = (val: CompareMode) => {
    setCompareMode(val);
    if (selectedCodes.length > 0) {
      fetchCompareData(undefined, undefined, undefined, val);
    }
  };

  const handleDateRangeChange = (dates: [Dayjs, Dayjs] | null) => {
    if (dates) {
      setDateRange(dates);
      if (selectedCodes.length > 0) {
        fetchCompareData(undefined, undefined, undefined, undefined, dates);
      }
    }
  };

  return (
    <div className="compare-page">
      <div className="compare-header">
        <h1>多股对比</h1>
      </div>

      <div className="compare-toolbar">
        <div className="toolbar-row">
          <span className="selector-label">选择股票：</span>
          <MultiStockSelector
            value={selectedCodes}
            onChange={handleStockChange}
            maxCount={5}
          />
          <span className="selector-hint">
            {loading
              ? '加载中...'
              : selectedCodes.length > 0
              ? `已选择 ${selectedCodes.length} 只股票`
              : '请选择股票进行对比（最多5只）'}
          </span>
        </div>

        <div className="toolbar-row">
          <Space size="large" wrap>
            <div className="toolbar-item">
              <span className="selector-label">日期范围：</span>
              <RangePicker
                value={dateRange}
                onChange={(dates) => handleDateRangeChange(dates as [Dayjs, Dayjs] | null)}
                format="YYYY-MM-DD"
                size="small"
                allowClear={false}
              />
            </div>

            <div className="toolbar-item">
              <span className="selector-label">周期：</span>
              <PeriodSelector
                value={period}
                onChange={handlePeriodChange}
              />
            </div>

            <div className="toolbar-item">
              <span className="selector-label">对比模式：</span>
              <Radio.Group
                value={compareMode}
                onChange={(e) => handleCompareModeChange(e.target.value)}
                size="small"
              >
                <Radio.Button value="change">涨跌幅 (%)</Radio.Button>
                <Radio.Button value="price">价格</Radio.Button>
              </Radio.Group>
            </div>
          </Space>
        </div>
      </div>

      <div className="compare-chart-container">
        <CompareChart
          series={chartSeries}
          loading={loading}
          mode={compareMode}
          title={compareMode === 'change' ? '涨跌幅对比' : '价格对比'}
        />
      </div>

      {/* 日志面板 */}
      <LogPanel />
    </div>
  );
};
