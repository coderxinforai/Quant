import dayjs from 'dayjs';

/**
 * 格式化日期为 YYYY-MM-DD
 */
export const formatDate = (date: Date | string): string => {
  return dayjs(date).format('YYYY-MM-DD');
};

/**
 * 获取N天前的日期
 */
export const getDaysAgo = (days: number): string => {
  return dayjs().subtract(days, 'day').format('YYYY-MM-DD');
};

/**
 * 获取今天日期
 */
export const getToday = (): string => {
  return dayjs().format('YYYY-MM-DD');
};

/**
 * 获取默认日期范围（最近3个月）
 */
export const getDefaultDateRange = (): [string, string] => {
  return [getDaysAgo(90), getToday()];
};
