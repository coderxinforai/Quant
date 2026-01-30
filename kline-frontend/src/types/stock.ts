export interface Stock {
  code: string;
  name: string;
  records: number;
}

export interface StockListResponse {
  code: number;
  message: string;
  data: {
    items: Stock[];
    total: number;
  };
}
