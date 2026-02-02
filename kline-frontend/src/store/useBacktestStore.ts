/**
 * 回测状态管理
 */
import { create } from 'zustand';
import type {
  StrategyDefinition,
  BacktestData,
  BacktestRequest
} from '../types/backtest';

interface BacktestState {
  // 策略列表
  strategies: StrategyDefinition[];
  setStrategies: (strategies: StrategyDefinition[]) => void;

  // 回测配置
  config: Partial<BacktestRequest>;
  setConfig: (config: Partial<BacktestRequest>) => void;

  // 回测结果
  result: BacktestData | null;
  setResult: (result: BacktestData | null) => void;

  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;

  // 重置
  reset: () => void;
}

const defaultConfig: Partial<BacktestRequest> = {
  initial_capital: 100000,
  position_ratio: 0.8,
  strategy_params: {}
};

export const useBacktestStore = create<BacktestState>((set) => ({
  strategies: [],
  setStrategies: (strategies) => set({ strategies }),

  config: defaultConfig,
  setConfig: (config) => set((state) => ({
    config: { ...state.config, ...config }
  })),

  result: null,
  setResult: (result) => set({ result }),

  loading: false,
  setLoading: (loading) => set({ loading }),

  reset: () => set({
    config: defaultConfig,
    result: null,
    loading: false
  })
}));
