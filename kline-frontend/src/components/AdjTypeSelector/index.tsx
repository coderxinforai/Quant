import { Radio } from 'antd';
import { memo } from 'react';

interface AdjTypeSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export const AdjTypeSelector: React.FC<AdjTypeSelectorProps> = memo(({ value, onChange }) => {
  return (
    <Radio.Group
      value={value}
      onChange={(e) => onChange(e.target.value)}
      optionType="button"
      size="small"
    >
      <Radio.Button value="none">不复权</Radio.Button>
      <Radio.Button value="after">后复权</Radio.Button>
      <Radio.Button value="before">前复权</Radio.Button>
    </Radio.Group>
  );
});

AdjTypeSelector.displayName = 'AdjTypeSelector';
