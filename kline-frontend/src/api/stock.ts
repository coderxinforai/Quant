import apiClient from './client';
import type { StockListResponse } from '../types/stock';

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
};
