import { Radio } from 'antd';
import { memo } from 'react';

interface PeriodSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

const periods = [
  { label: '1分', value: '1min' },
  { label: '5分', value: '5min' },
  { label: '15分', value: '15min' },
  { label: '30分', value: '30min' },
  { label: '60分', value: '60min' },
  { label: '日K', value: 'day' },
  { label: '周K', value: 'week' },
  { label: '月K', value: 'month' },
  { label: '年K', value: 'year' },
];

export const PeriodSelector: React.FC<PeriodSelectorProps> = memo(({ value, onChange }) => {
  return (
    <Radio.Group
      value={value}
      onChange={(e) => onChange(e.target.value)}
      optionType="button"
      size="small"
    >
      {periods.map((p) => (
        <Radio.Button key={p.value} value={p.value}>
          {p.label}
        </Radio.Button>
      ))}
    </Radio.Group>
  );
});

PeriodSelector.displayName = 'PeriodSelector';
