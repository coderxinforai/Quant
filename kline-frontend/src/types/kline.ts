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

export interface KLineResponse {
  code: number;
  message: string;
  data: {
    stock_info: StockInfo;
    klines: KLine[];
    count: number;
  };
}
