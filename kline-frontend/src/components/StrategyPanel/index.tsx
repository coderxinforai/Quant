/**
 * 策略配置面板
 */
import { Card, Form, Select, InputNumber, Row, Col, Typography, Divider } from 'antd';
import { useEffect, useState } from 'react';
import type { StrategyDefinition } from '../../types/backtest';
import { useBacktestStore } from '../../store/useBacktestStore';

const { Title, Text } = Typography;

export const StrategyPanel: React.FC = () => {
  const { strategies, config, setConfig } = useBacktestStore();
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyDefinition | null>(null);
  const [form] = Form.useForm();

  // 选择策略时更新
  useEffect(() => {
    if (config.strategy_id) {
      const strategy = strategies.find(s => s.id === config.strategy_id);
      setSelectedStrategy(strategy || null);

      // 设置默认参数
      if (strategy) {
        const defaultParams: Record<string, number> = {};
        strategy.params.forEach(p => {
          defaultParams[p.name] = p.default;
        });
        setConfig({ strategy_params: defaultParams });
        form.setFieldsValue(defaultParams);
      }
    }
  }, [config.strategy_id, strategies, setConfig, form]);

  const handleStrategyChange = (strategyId: string) => {
    setConfig({ strategy_id: strategyId });
  };

  const handleParamChange = (paramName: string, value: number | null) => {
    if (value !== null) {
      setConfig({
        strategy_params: {
          ...config.strategy_params,
          [paramName]: value
        }
      });
    }
  };

  const handleCapitalChange = (value: number | null) => {
    if (value !== null) {
      setConfig({ initial_capital: value });
    }
  };

  const handlePositionRatioChange = (value: number | null) => {
    if (value !== null) {
      setConfig({ position_ratio: value });
    }
  };

  return (
    <Card title="策略配置" size="small">
      <Form form={form} layout="vertical" size="small">
        {/* 策略选择 */}
        <Form.Item label="选择策略" required>
          <Select
            value={config.strategy_id}
            onChange={handleStrategyChange}
            placeholder="请选择回测策略"
            options={strategies.map(s => ({
              label: s.name,
              value: s.id,
              description: s.description
            }))}
            optionRender={(option) => (
              <div>
                <div>{option.data.label}</div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {option.data.description}
                </Text>
              </div>
            )}
          />
        </Form.Item>

        {/* 策略参数 */}
        {selectedStrategy && selectedStrategy.params.length > 0 && (
          <>
            <Divider orientation="left" style={{ margin: '12px 0' }}>
              <Text type="secondary">策略参数</Text>
            </Divider>
            <Row gutter={16}>
              {selectedStrategy.params.map(param => (
                <Col span={12} key={param.name}>
                  <Form.Item
                    label={param.label}
                    name={param.name}
                    initialValue={param.default}
                  >
                    <InputNumber
                      min={param.min}
                      max={param.max}
                      step={param.step || 1}
                      style={{ width: '100%' }}
                      onChange={(value) => handleParamChange(param.name, value)}
                    />
                  </Form.Item>
                </Col>
              ))}
            </Row>
          </>
        )}

        {/* 回测设置 */}
        <Divider orientation="left" style={{ margin: '12px 0' }}>
          <Text type="secondary">回测设置</Text>
        </Divider>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item label="初始资金" tooltip="回测的初始本金（元）">
              <InputNumber
                value={config.initial_capital}
                min={10000}
                max={10000000}
                step={10000}
                style={{ width: '100%' }}
                formatter={(value) => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value?.replace(/¥\s?|(,*)/g, '') as unknown as number}
                onChange={handleCapitalChange}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item label="仓位比例" tooltip="单次买入使用的可用资金比例">
              <InputNumber
                value={config.position_ratio}
                min={0.1}
                max={1}
                step={0.1}
                style={{ width: '100%' }}
                formatter={(value) => `${(value! * 100).toFixed(0)}%`}
                parser={(value) => (parseFloat(value?.replace('%', '') || '0') / 100) as number}
                onChange={handlePositionRatioChange}
              />
            </Form.Item>
          </Col>
        </Row>
      </Form>
    </Card>
  );
};
