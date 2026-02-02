import type { EChartsOption } from 'echarts';
import type { KLine } from '../../types/kline';

export const getKLineOption = (data: KLine[], stockName: string, period: string = 'day'): EChartsOption => {
  // 提取数据
  const dates = data.map((d) => d.date);
  const klineData = data.map((d) => [d.open, d.close, d.low, d.high]);
  const volumeData = data.map((d) => d.volume);

  // 周期标签映射
  const periodLabel: Record<string, string> = {
    '1min': '1分钟',
    '5min': '5分钟',
    '15min': '15分钟',
    '30min': '30分钟',
    '60min': '60分钟',
    day: '日K',
    week: '周K',
    month: '月K',
    year: '年K',
  };

  // 判断是否为分钟K线
  const isMinutePeriod = period.includes('min');

  return {
    title: {
      text: `${stockName} - ${periodLabel[period] || '日K'}`,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
      formatter: (params: any) => {
        const param = params[0];
        if (!param) return '';

        const index = param.dataIndex;
        const kline = data[index];

        return `
          <div style="padding: 8px;">
            <div><b>${kline.date}</b></div>
            <div>开: ${kline.open.toFixed(2)}</div>
            <div>收: ${kline.close.toFixed(2)}</div>
            <div>高: ${kline.high.toFixed(2)}</div>
            <div>低: ${kline.low.toFixed(2)}</div>
            <div>量: ${(kline.volume / 10000).toFixed(0)}万</div>
          </div>
        `;
      },
    },
    grid: [
      {
        left: '10%',
        right: '10%',
        top: '15%',
        height: '50%',
      },
      {
        left: '10%',
        right: '10%',
        top: '70%',
        height: '15%',
      },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLabel: {
          show: false,
        },
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLabel: {
          // 分钟K线显示时间，日K及以上显示日期
          formatter: isMinutePeriod
            ? (value: string) => {
                // 分钟K线格式: "2024-01-15 09:35:00" -> "09:35"
                const parts = value.split(' ');
                if (parts.length > 1) {
                  const timePart = parts[1];
                  return timePart.substring(0, 5); // HH:mm
                }
                return value;
              }
            : undefined,
        },
      },
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: {
          show: true,
        },
      },
      {
        scale: true,
        gridIndex: 1,
        splitLine: {
          show: false,
        },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: isMinutePeriod ? 0 : 80,  // 分钟K线显示全部，日K及以上显示最近20%
        end: 100,
        minSpan: 5,
        maxSpan: 100,
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: isMinutePeriod ? 0 : 80,
        end: 100,
        bottom: 10,
        height: 20,
        minSpan: 5,
        maxSpan: 100,
        handleSize: '120%',
        textStyle: {
          fontSize: 12,
        },
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a',
        },
      },
      {
        name: '成交量',
        type: 'bar',
        data: volumeData,
        xAxisIndex: 1,
        yAxisIndex: 1,
        itemStyle: {
          color: (params: any) => {
            const index = params.dataIndex;
            if (index === 0) return '#26a69a';
            return data[index].close >= data[index].open ? '#ef5350' : '#26a69a';
          },
        },
      },
    ],
  };
};
