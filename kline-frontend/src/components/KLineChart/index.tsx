import { useEffect, useRef, memo } from 'react';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import type { KLine } from '../../types/kline';
import { getKLineOption } from './options';
import { Skeleton, Empty } from 'antd';
import { logger } from '../../store/useLogStore';

interface KLineChartProps {
  data: KLine[];
  stockName?: string;
  loading?: boolean;
  period?: string;
}

export const KLineChart: React.FC<KLineChartProps> = memo(({
  data,
  stockName = 'K线图',
  loading = false,
  period = 'day'
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<ECharts | undefined>(undefined);

  useEffect(() => {
    logger.info(`K线图: 数据更新 - ${data.length} 条数据, 股票: ${stockName}`);

    if (!chartRef.current) {
      logger.warning('K线图: chartRef为空');
      return;
    }

    // 初始化ECharts实例
    if (!chartInstance.current) {
      logger.info('K线图: 初始化ECharts实例');
      chartInstance.current = echarts.init(chartRef.current);
    }

    // 设置图表选项
    if (data.length > 0) {
      logger.info(`K线图: 渲染图表 - 日期范围 ${data[0].date} ~ ${data[data.length - 1].date}`);
      const option = getKLineOption(data, stockName, period);
      chartInstance.current.setOption(option, true);
      logger.success('K线图: 渲染完成');
    } else {
      logger.info('K线图: 数据为空，不渲染');
    }

    // 窗口resize时重绘
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, stockName, period]);

  // 组件卸载时销毁实例
  useEffect(() => {
    return () => {
      chartInstance.current?.dispose();
    };
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '20px' }}>
        <Skeleton active paragraph={{ rows: 12 }} />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div style={{
        width: '100%',
        height: '600px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Empty description="暂无数据" />
      </div>
    );
  }

  return <div ref={chartRef} style={{ width: '100%', height: '600px' }} />;
}, (prevProps, nextProps) => {
  // 自定义比较函数，优化渲染性能
  return (
    prevProps.loading === nextProps.loading &&
    prevProps.stockName === nextProps.stockName &&
    prevProps.period === nextProps.period &&
    prevProps.data.length === nextProps.data.length &&
    prevProps.data[0]?.date === nextProps.data[0]?.date &&
    prevProps.data[prevProps.data.length - 1]?.date === nextProps.data[nextProps.data.length - 1]?.date
  );
});
