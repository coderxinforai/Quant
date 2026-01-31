import axios, { type CancelTokenSource } from 'axios';
import apiClient from './client';
import type { KLineResponse } from '../types/kline';

// 存储当前的取消令牌
let cancelTokenSource: CancelTokenSource | null = null;

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
    // 取消之前的请求
    if (cancelTokenSource) {
      cancelTokenSource.cancel('新的K线数据请求已发起');
    }

    // 创建新的取消令牌
    cancelTokenSource = axios.CancelToken.source();

    const response = await apiClient.get<KLineResponse>('/kline/data', {
      params: {
        code,
        start_date: startDate,
        end_date: endDate,
        adj_type: adjType,
      },
      cancelToken: cancelTokenSource.token,
    });

    return response.data;
  },
};
