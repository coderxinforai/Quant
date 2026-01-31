import { useState, useCallback, memo } from 'react';
import { Select } from 'antd';
import { stockApi } from '../../api/stock';
import type { Stock } from '../../types/stock';
import { debounce } from 'lodash-es';
import { logger } from '../../store/useLogStore';

interface StockSelectorProps {
  value?: string;
  onChange?: (code: string, stock: Stock) => void;
}

export const StockSelector: React.FC<StockSelectorProps> = memo(({ value, onChange }) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);

  // 搜索股票（防抖）
  const searchStocks = useCallback(
    debounce(async (keyword: string) => {
      logger.info(`开始搜索股票: "${keyword}"`);

      if (!keyword) {
        logger.info('搜索关键词为空，清空列表');
        setStocks([]);
        return;
      }

      setLoading(true);
      try {
        const response = await stockApi.getStockList(keyword, 50);
        logger.success(`搜索到 ${response.data.items.length} 只股票`);
        setStocks(response.data.items);
      } catch (error) {
        logger.error('搜索股票失败', error);
        setStocks([]);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  const handleChange = (code: string) => {
    const stock = stocks.find((s) => s.code === code);
    logger.info(`选择股票: ${code}`, stock);
    if (stock && onChange) {
      onChange(code, stock);
    }
  };

  return (
    <Select
      showSearch
      value={value}
      placeholder="请输入股票代码或名称搜索"
      style={{ width: 300 }}
      loading={loading}
      filterOption={false}
      onSearch={searchStocks}
      onChange={handleChange}
      options={stocks.map((stock) => ({
        label: `${stock.code} ${stock.name}`,
        value: stock.code,
      }))}
    />
  );
});
