import { DatePicker } from 'antd';
import dayjs, { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

interface DateRangePickerProps {
  value?: [string, string];
  onChange?: (range: [string, string]) => void;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({ value, onChange }) => {
  const handleChange = (dates: null | [Dayjs | null, Dayjs | null]) => {
    if (dates && dates[0] && dates[1] && onChange) {
      const range: [string, string] = [
        dates[0].format('YYYY-MM-DD'),
        dates[1].format('YYYY-MM-DD'),
      ];
      onChange(range);
    }
  };

  const dayjsValue: [Dayjs, Dayjs] | undefined = value
    ? [dayjs(value[0]), dayjs(value[1])]
    : undefined;

  return (
    <RangePicker
      value={dayjsValue}
      onChange={handleChange}
      format="YYYY-MM-DD"
      style={{ width: 260 }}
    />
  );
};
