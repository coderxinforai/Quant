export interface KLine {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
  amount: number;
}

export interface StockInfo {
  code: string;
  name: string;
}

export interface IndicatorData {
  ma?: { [key: string]: (number | null)[] };   // ma5, ma10, ma20, ma60
  macd?: { dif: (number | null)[]; dea: (number | null)[]; macd: (number | null)[] };
  kdj?: { k: (number | null)[]; d: (number | null)[]; j: (number | null)[] };
  rsi?: { [key: string]: (number | null)[] };  // rsi6, rsi12, rsi24
  boll?: { mid: (number | null)[]; upper: (number | null)[]; lower: (number | null)[] };
}

export interface KLineResponse {
  code: number;
  message: string;
  data: {
    stock_info: StockInfo;
    klines: KLine[];
    count: number;
    period?: string;
    indicators?: IndicatorData;
  };
}
