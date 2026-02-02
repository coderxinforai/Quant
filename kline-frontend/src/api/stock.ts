import apiClient from './client';
import type { StockListResponse } from '../types/stock';

export interface DateRangeResponse {
  code: number;
  message: string;
  data: {
    start_date: string | null;
    end_date: string | null;
  };
}

export const stockApi = {
  /**
   * 获取股票列表
   */
  async getStockList(keyword?: string, limit: number = 50): Promise<StockListResponse> {
    const params: any = { limit };
    if (keyword) {
      params.keyword = keyword;
    }
    const response = await apiClient.get<StockListResponse>('/stocks/list', { params });
    return response.data;
  },

  /**
   * 获取股票的数据时间范围
   */
  async getStockDateRange(code: string): Promise<DateRangeResponse> {
    const response = await apiClient.get<DateRangeResponse>('/stocks/date-range', {
      params: { code }
    });
    return response.data;
  },
};
