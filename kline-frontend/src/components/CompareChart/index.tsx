import { useEffect, useRef, memo } from 'react';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import { Skeleton, Empty } from 'antd';
import { logger } from '../../store/useLogStore';

export interface CompareDataItem {
  date: string;
  value: number;
}

export interface CompareSeriesData {
  code: string;
  name: string;
  data: CompareDataItem[];
}

interface CompareChartProps {
  series: CompareSeriesData[];
  loading?: boolean;
  mode?: 'change' | 'price'; // 对比模式：涨跌幅 或 价格
  title?: string;
}

export const CompareChart: React.FC<CompareChartProps> = memo(({
  series,
  loading = false,
  mode = 'change',
  title = '多股对比',
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<ECharts | undefined>(undefined);

  useEffect(() => {
    logger.info(`对比图表: 数据更新 - ${series.length} 只股票, 模式: ${mode}`);

    if (!chartRef.current) {
      logger.warning('对比图表: chartRef为空');
      return;
    }

    // 初始化ECharts实例
    if (!chartInstance.current) {
      logger.info('对比图表: 初始化ECharts实例');
      chartInstance.current = echarts.init(chartRef.current);
    }

    // 设置图表选项
    if (series.length > 0 && series.some(s => s.data.length > 0)) {
      logger.info(`对比图表: 渲染图表 - ${series.length} 条曲线`);

      // 提取所有日期（使用第一个序列的日期作为基准）
      const dates = series[0]?.data.map(item => item.date) || [];

      // 构建ECharts series配置
      const echartsSeries = series.map((s) => ({
        name: `${s.name} (${s.code})`,
        type: 'line',
        data: s.data.map(item => item.value),
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
        },
      }));

      const option = {
        title: {
          text: title,
          left: 'center',
          textStyle: {
            fontSize: 18,
            fontWeight: 'bold',
          },
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
          },
          formatter: (params: any) => {
            if (!params || params.length === 0) return '';
            const date = params[0].axisValue;
            let result = `<div style="font-weight: bold; margin-bottom: 8px;">${date}</div>`;
            params.forEach((param: any) => {
              const value = param.value;
              const formattedValue = mode === 'change'
                ? `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
                : value.toFixed(2);
              const color = value >= 0 ? '#ef5350' : '#26a69a';
              result += `<div style="margin: 4px 0;">
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:${param.color};"></span>
                <span style="font-weight: 500;">${param.seriesName}:</span>
                <span style="margin-left: 8px; color: ${mode === 'change' ? color : '#333'}; font-weight: bold;">${formattedValue}</span>
              </div>`;
            });
            return result;
          },
        },
        legend: {
          data: echartsSeries.map(s => s.name),
          top: 35,
          left: 'center',
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',
          top: 80,
          containLabel: true,
        },
        xAxis: {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLabel: {
            formatter: (value: string) => {
              // 格式化日期显示（只显示月-日）
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            },
            rotate: 45,
          },
        },
        yAxis: {
          type: 'value',
          scale: true,
          axisLabel: {
            formatter: mode === 'change' ? '{value}%' : '{value}',
          },
          splitLine: {
            lineStyle: {
              type: 'dashed',
            },
          },
        },
        dataZoom: [
          {
            type: 'slider',
            show: true,
            start: 0,
            end: 100,
            bottom: 20,
          },
          {
            type: 'inside',
            start: 0,
            end: 100,
          },
        ],
        series: echartsSeries,
      };

      chartInstance.current.setOption(option, true);
      logger.success('对比图表: 渲染完成');
    } else {
      logger.info('对比图表: 数据为空，不渲染');
    }

    // 窗口resize时重绘
    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [series, mode, title]);

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

  if (series.length === 0 || series.every(s => s.data.length === 0)) {
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
    prevProps.mode === nextProps.mode &&
    prevProps.title === nextProps.title &&
    prevProps.series.length === nextProps.series.length &&
    prevProps.series.every((s, i) =>
      s.code === nextProps.series[i]?.code &&
      s.data.length === nextProps.series[i]?.data.length
    )
  );
});
