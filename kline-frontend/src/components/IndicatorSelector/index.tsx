import { Checkbox } from 'antd';
import { memo } from 'react';
import type { CheckboxValueType } from 'antd/es/checkbox/Group';

interface IndicatorSelectorProps {
  value: string[];
  onChange: (values: string[]) => void;
}

const indicatorOptions = [
  { label: 'MA', value: 'ma' },
  { label: 'MACD', value: 'macd' },
  { label: 'KDJ', value: 'kdj' },
  { label: 'RSI', value: 'rsi' },
  { label: 'BOLL', value: 'boll' },
];

export const IndicatorSelector: React.FC<IndicatorSelectorProps> = memo(({ value, onChange }) => {
  const handleChange = (checkedValues: CheckboxValueType[]) => {
    onChange(checkedValues as string[]);
  };

  return (
    <Checkbox.Group
      options={indicatorOptions}
      value={value}
      onChange={handleChange}
    />
  );
});

IndicatorSelector.displayName = 'IndicatorSelector';
