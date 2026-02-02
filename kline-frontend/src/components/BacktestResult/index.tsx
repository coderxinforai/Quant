/**
 * 回测结果展示
 */
import { Card, Row, Col, Statistic, Table, Empty } from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  DollarOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import ReactECharts from 'echarts-for-react';
import type { BacktestData, TradeRecord } from '../../types/backtest';

interface BacktestResultProps {
  result: BacktestData | null;
}

export const BacktestResult: React.FC<BacktestResultProps> = ({ result }) => {
  if (!result) {
    return (
      <Card>
        <Empty description="暂无回测结果" />
      </Card>
    );
  }

  const { metrics, equity_curve, trades, stock_name, strategy_name, buy_hold_curve } = result;

  // 资金曲线图表配置
  const equityChartOption = {
    title: {
      text: `${stock_name} - ${strategy_name} 资金曲线`,
      left: 'center',
      textStyle: { fontSize: 14 }
    },
    legend: {
      data: ['策略收益', '买入持有'],
      top: 30
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach((item: any) => {
          result += `${item.seriesName}: ¥${item.value.toLocaleString()}<br/>`;
        });
        return result;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 50,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: equity_curve.map(p => p.date),
      boundaryGap: false
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`
      }
    },
    series: [
      {
        name: '策略收益',
        type: 'line',
        data: equity_curve.map(p => p.value),
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: metrics.total_return >= 0 ? '#ff4d4f' : '#52c41a'
        },
        areaStyle: {
          color: metrics.total_return >= 0
            ? {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(255, 77, 79, 0.3)' },
                  { offset: 1, color: 'rgba(255, 77, 79, 0.05)' }
                ]
              }
            : {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(82, 196, 26, 0.3)' },
                  { offset: 1, color: 'rgba(82, 196, 26, 0.05)' }
                ]
              }
        }
      },
      ...(buy_hold_curve ? [{
        name: '买入持有',
        type: 'line',
        data: buy_hold_curve.map(p => p.value),
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: '#1890ff',
          type: 'dashed'
        }
      }] : [])
    ]
  };

  // 交易记录表格列
  const tradeColumns: ColumnsType<TradeRecord> = [
    {
      title: '日期',
      dataIndex: 'date',
      key: 'date',
      width: 100
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 60,
      render: (action: string) => (
        <span style={{ color: action === 'buy' ? '#ff4d4f' : '#52c41a' }}>
          {action === 'buy' ? '买入' : '卖出'}
        </span>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      width: 80,
      align: 'right',
      render: (price: number) => `¥${price.toFixed(2)}`
    },
    {
      title: '数量',
      dataIndex: 'shares',
      key: 'shares',
      width: 80,
      align: 'right',
      render: (shares: number) => shares.toLocaleString()
    },
    {
      title: '金额',
      dataIndex: 'amount',
      key: 'amount',
      width: 100,
      align: 'right',
      render: (amount: number) => `¥${amount.toLocaleString()}`
    },
    {
      title: '手续费',
      dataIndex: 'commission',
      key: 'commission',
      width: 80,
      align: 'right',
      render: (commission: number) => `¥${commission.toFixed(2)}`
    },
    {
      title: '原因',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* 绩效指标 */}
      <Card title="绩效指标" size="small">
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="总收益率"
              value={metrics.total_return}
              precision={2}
              suffix="%"
              valueStyle={{ color: metrics.total_return >= 0 ? '#cf1322' : '#3f8600' }}
              prefix={metrics.total_return >= 0 ? <RiseOutlined /> : <FallOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="年化收益率"
              value={metrics.annual_return}
              precision={2}
              suffix="%"
              valueStyle={{ color: metrics.annual_return >= 0 ? '#cf1322' : '#3f8600' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="最大回撤"
              value={metrics.max_drawdown}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="夏普比率"
              value={metrics.sharpe_ratio}
              precision={2}
              valueStyle={{ color: '#722ed1' }}
              prefix={<TrophyOutlined />}
            />
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={6}>
            <Statistic
              title="胜率"
              value={metrics.win_rate}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="盈亏比"
              value={metrics.profit_loss_ratio}
              precision={2}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="交易次数"
              value={metrics.total_trades}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="盈利/亏损"
              value={`${metrics.win_trades}/${metrics.loss_trades}`}
              valueStyle={{ color: '#595959' }}
              prefix={<DollarOutlined />}
            />
          </Col>
        </Row>
        {(metrics.buy_hold_return !== undefined || metrics.excess_return !== undefined) && (
          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col span={6}>
              <Statistic
                title="买入持有收益"
                value={metrics.buy_hold_return || 0}
                precision={2}
                suffix="%"
                valueStyle={{ color: (metrics.buy_hold_return || 0) >= 0 ? '#1890ff' : '#faad14' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="超额收益"
                value={metrics.excess_return || 0}
                precision={2}
                suffix="%"
                valueStyle={{
                  color: (metrics.excess_return || 0) > 0 ? '#52c41a' :
                         (metrics.excess_return || 0) < 0 ? '#ff4d4f' : '#595959'
                }}
                prefix={(metrics.excess_return || 0) > 0 ? <RiseOutlined /> :
                        (metrics.excess_return || 0) < 0 ? <FallOutlined /> : null}
              />
            </Col>
          </Row>
        )}
      </Card>

      {/* 资金曲线 */}
      <Card title="资金曲线" size="small">
        <ReactECharts
          option={equityChartOption}
          style={{ height: 300 }}
          notMerge={true}
          lazyUpdate={true}
        />
      </Card>

      {/* 交易记录 */}
      <Card title="交易记录" size="small">
        <Table
          columns={tradeColumns}
          dataSource={trades}
          rowKey={(record, index) => `${record.date}-${record.action}-${index}`}
          size="small"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
          scroll={{ x: 800 }}
        />
      </Card>
    </div>
  );
};
