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
    adjType: string = 'none',
    period: string = 'day',
    indicators: string[] = []
  ): Promise<KLineResponse> {
    // 取消之前的请求
    if (cancelTokenSource) {
      cancelTokenSource.cancel('新的K线数据请求已发起');
    }

    // 创建新的取消令牌
    cancelTokenSource = axios.CancelToken.source();

    const params: any = {
      code,
      start_date: startDate,
      end_date: endDate,
      adj_type: adjType,
      period,
    };

    if (indicators.length > 0) {
      params.indicators = indicators.join(',');
    }

    const response = await apiClient.get<KLineResponse>('/kline/data', {
      params,
      cancelToken: cancelTokenSource.token,
    });

    return response.data;
  },

  /**
   * 获取分钟级K线数据
   */
  async getMinuteKLineData(
    code: string,
    tradeDate: string,
    interval: number = 1,
    adjType: string = 'none'
  ): Promise<KLineResponse> {
    // 取消之前的请求
    if (cancelTokenSource) {
      cancelTokenSource.cancel('新的分钟K线数据请求已发起');
    }

    // 创建新的取消令牌
    cancelTokenSource = axios.CancelToken.source();

    const response = await apiClient.get<KLineResponse>('/kline/minute', {
      params: {
        code,
        trade_date: tradeDate,
        interval,
        adj_type: adjType,
      },
      cancelToken: cancelTokenSource.token,
    });

    return response.data;
  },
};
