import apiClient from './client';

export interface CompareData {
  stocks: Array<{
    code: string;
    name: string;
    dates: string[];
    values: number[];
  }>;
  dates: string[];
  series: Array<{
    name: string;
    data: number[];
  }>;
}

export interface CompareResponse {
  code: number;
  message: string;
  data: CompareData;
}

export const compareApi = {
  /**
   * 获取多股票对比数据
   */
  async getCompareData(
    codes: string[],
    startDate: string,
    endDate: string,
    period: string = 'day',
    mode: string = 'change_pct'
  ): Promise<CompareResponse> {
    const response = await apiClient.get<CompareResponse>('/compare/data', {
      params: {
        codes: codes.join(','),
        start_date: startDate,
        end_date: endDate,
        period,
        mode,
      },
    });

    return response.data;
  },
};
