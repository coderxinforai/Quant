import { Select } from 'antd';
import { useState, useCallback } from 'react';
import { stockApi } from '../../api/stock';
import type { Stock } from '../../types/stock';
import { logger } from '../../store/useLogStore';
import { debounce } from 'lodash-es';

interface MultiStockSelectorProps {
  value: string[];
  onChange: (codes: string[], stocks: Stock[]) => void;
  maxCount?: number;
}

export const MultiStockSelector: React.FC<MultiStockSelectorProps> = ({
  value,
  onChange,
  maxCount = 5,
}) => {
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [stocksMap, setStocksMap] = useState<Map<string, Stock>>(new Map());

  const searchStocks = async (keyword: string) => {
    if (!keyword || keyword.length < 1) {
      setStocks([]);
      return;
    }

    setLoading(true);
    try {
      logger.info(`多股选择器: 搜索 "${keyword}"`);
      const response = await stockApi.getStockList(keyword, 50);
      logger.success(`多股选择器: 搜索到 ${response.data.items.length} 只股票`);
      setStocks(response.data.items);

      // 更新股票映射表
      const newMap = new Map(stocksMap);
      response.data.items.forEach(stock => {
        newMap.set(stock.code, stock);
      });
      setStocksMap(newMap);
    } catch (error) {
      logger.error('多股选择器: 搜索股票失败', error);
      setStocks([]);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = useCallback(
    debounce((keyword: string) => {
      searchStocks(keyword);
    }, 300),
    []
  );

  const handleSearch = (keyword: string) => {
    debouncedSearch(keyword);
  };

  const handleChange = (selectedCodes: string[]) => {
    logger.info(`多股选择器: 已选择 ${selectedCodes.length} 只股票`, selectedCodes);

    // 从映射表中获取完整的股票信息
    const selectedStocksList = selectedCodes
      .map(code => stocksMap.get(code))
      .filter((stock): stock is Stock => stock !== undefined);

    onChange(selectedCodes, selectedStocksList);
  };

  return (
    <Select
      mode="multiple"
      showSearch
      value={value}
      placeholder={`请选择股票（最多${maxCount}只）`}
      filterOption={false}
      onSearch={handleSearch}
      onChange={handleChange}
      loading={loading}
      options={stocks.map((stock) => ({
        label: `${stock.code} ${stock.name}`,
        value: stock.code,
      }))}
      maxCount={maxCount}
      style={{ width: '100%', minWidth: 300 }}
      size="small"
      allowClear
    />
  );
};
