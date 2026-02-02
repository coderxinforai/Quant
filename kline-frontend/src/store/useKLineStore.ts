import { create } from 'zustand';
import type { KLine, StockInfo, IndicatorData } from '../types/kline';

interface KLineStore {
  // 状态
  selectedStock: string | null;
  stockInfo: StockInfo | null;
  klineData: KLine[];
  loading: boolean;
  error: string | null;
  adjType: string;
  period: string;
  tradeDate: string | null;
  indicators: string[];
  indicatorData: IndicatorData | null;

  // Actions
  setSelectedStock: (code: string | null) => void;
  setStockInfo: (info: StockInfo | null) => void;
  setKLineData: (data: KLine[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setAdjType: (type: string) => void;
  setPeriod: (period: string) => void;
  setTradeDate: (date: string | null) => void;
  setIndicators: (indicators: string[]) => void;
  setIndicatorData: (data: IndicatorData | null) => void;
  reset: () => void;
}

const initialState = {
  selectedStock: null,
  stockInfo: null,
  klineData: [],
  loading: false,
  error: null,
  adjType: 'none' as string,
  period: 'day' as string,
  tradeDate: null as string | null,
  indicators: [] as string[],
  indicatorData: null as IndicatorData | null,
};

export const useKLineStore = create<KLineStore>((set) => ({
  ...initialState,

  setSelectedStock: (code) => set({ selectedStock: code }),
  setStockInfo: (info) => set({ stockInfo: info }),
  setKLineData: (data) => set({ klineData: data }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setAdjType: (type) => set({ adjType: type }),
  setPeriod: (period) => set({ period }),
  setTradeDate: (date) => set({ tradeDate: date }),
  setIndicators: (indicators) => set({ indicators }),
  setIndicatorData: (data) => set({ indicatorData: data }),
  reset: () => set(initialState),
}));
