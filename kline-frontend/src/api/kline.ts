import apiClient from './client';
import type { KLineResponse } from '../types/kline';

export const klineApi = {
  /**
   * 获取K线数据
   */
  async getKLineData(
    code: string,
    startDate: string,
    endDate: string,
    adjType: string = 'none'
  ): Promise<KLineResponse> {
    const response = await apiClient.get<KLineResponse>('/kline/data', {
      params: {
        code,
        start_date: startDate,
        end_date: endDate,
        adj_type: adjType,
      },
    });
    return response.data;
  },
};
