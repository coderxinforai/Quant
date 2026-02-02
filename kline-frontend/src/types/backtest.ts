/**
 * 回测相关类型定义
 */

/**
 * 策略参数定义
 */
export interface StrategyParam {
  name: string;
  label: string;
  type: string;
  default: number;
  min?: number;
  max?: number;
  step?: number;
}

/**
 * 策略定义
 */
export interface StrategyDefinition {
  id: string;
  name: string;
  description: string;
  params: StrategyParam[];
}

/**
 * 回测请求
 */
export interface BacktestRequest {
  code: string;
  start_date: string;
  end_date: string;
  strategy_id: string;
  strategy_params: Record<string, number>;
  initial_capital: number;
  position_ratio: number;
}

/**
 * 交易记录
 */
export interface TradeRecord {
  date: string;
  code: string;
  name: string;
  action: 'buy' | 'sell';
  price: number;
  shares: number;
  amount: number;
  commission: number;
  reason: string;
}

/**
 * 持仓信息
 */
export interface PositionInfo {
  code: string;
  name: string;
  shares: number;
  avg_price: number;
  current_price: number;
  market_value: number;
  cost: number;
  profit: number;
  profit_pct: number;
}

/**
 * 每日持仓
 */
export interface DailyPosition {
  date: string;
  cash: number;
  market_value: number;
  total_value: number;
  positions: PositionInfo[];
}

/**
 * 回测绩效指标
 */
export interface BacktestMetrics {
  total_return: number;
  annual_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  profit_loss_ratio: number;
  total_trades: number;
  win_trades: number;
  loss_trades: number;
  buy_hold_return?: number;
  excess_return?: number;
}

/**
 * 资金曲线数据点
 */
export interface EquityCurvePoint {
  date: string;
  value: number;
}

/**
 * 回测结果数据
 */
export interface BacktestData {
  stock_code: string;
  stock_name: string;
  start_date: string;
  end_date: string;
  strategy_name: string;
  strategy_params: Record<string, number>;
  initial_capital: number;
  final_capital: number;
  metrics: BacktestMetrics;
  daily_records: DailyPosition[];
  trades: TradeRecord[];
  equity_curve: EquityCurvePoint[];
  buy_hold_curve?: EquityCurvePoint[];
}

/**
 * 回测响应
 */
export interface BacktestResponse {
  code: number;
  message: string;
  data: BacktestData;
}

/**
 * 策略列表响应
 */
export interface StrategyListResponse {
  code: number;
  message: string;
  data: StrategyDefinition[];
}
