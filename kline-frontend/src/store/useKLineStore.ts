import { create } from 'zustand';
import type { KLine, StockInfo } from '../types/kline';

interface KLineStore {
  // 状态
  selectedStock: string | null;
  stockInfo: StockInfo | null;
  klineData: KLine[];
  loading: boolean;
  error: string | null;

  // Actions
  setSelectedStock: (code: string | null) => void;
  setStockInfo: (info: StockInfo | null) => void;
  setKLineData: (data: KLine[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  selectedStock: null,
  stockInfo: null,
  klineData: [],
  loading: false,
  error: null,
};

export const useKLineStore = create<KLineStore>((set) => ({
  ...initialState,

  setSelectedStock: (code) => set({ selectedStock: code }),
  setStockInfo: (info) => set({ stockInfo: info }),
  setKLineData: (data) => set({ klineData: data }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),
}));
