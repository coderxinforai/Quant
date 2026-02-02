/**
 * 回测 API 客户端
 */
import apiClient from './client';
import type {
  BacktestRequest,
  BacktestResponse,
  StrategyListResponse
} from '../types/backtest';

export const backtestApi = {
  /**
   * 获取策略列表
   */
  async getStrategies(): Promise<StrategyListResponse> {
    const response = await apiClient.get<StrategyListResponse>('/backtest/strategies');
    return response.data;
  },

  /**
   * 执行回测
   */
  async runBacktest(request: BacktestRequest): Promise<BacktestResponse> {
    const response = await apiClient.post<BacktestResponse>('/backtest/run', request);
    return response.data;
  }
};
