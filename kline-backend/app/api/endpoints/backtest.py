"""量化回测 API"""
from fastapi import APIRouter, HTTPException
import pandas as pd
from app.db.clickhouse import db_client
from app.services.kline_service import KLineService
from app.services.backtest import BacktestEngine, StrategyFactory, BacktestMetrics
from app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestData,
    BacktestMetricsData,
    TradeRecord,
    PositionInfo,
    DailyPosition,
    StrategyListResponse,
    StrategyDefinition,
    StrategyParam
)
from app.core.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/strategies", response_model=StrategyListResponse)
async def get_strategies():
    """获取策略列表"""
    try:
        strategy_defs = StrategyFactory.get_strategy_definitions()

        # 转换为 Pydantic 模型
        strategies = []
        for s in strategy_defs:
            params = [StrategyParam(**p) for p in s['params']]
            strategies.append(StrategyDefinition(
                id=s['id'],
                name=s['name'],
                description=s['description'],
                params=params
            ))

        return StrategyListResponse(data=strategies)

    except Exception as e:
        logger.error(f"获取策略列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    执行回测

    Args:
        request: 回测请求参数

    Returns:
        回测结果
    """
    logger.info(f"开始回测: {request.code}, 策略={request.strategy_id}, 日期={request.start_date}~{request.end_date}")

    try:
        # 获取K线数据
        kline_service = KLineService(db_client)

        kline_response = kline_service.get_kline(
            code=request.code,
            start_date=request.start_date,
            end_date=request.end_date,
            adj_type='after',  # 使用后复权
            period='day'
        )

        if len(kline_response.klines) == 0:
            raise HTTPException(status_code=404, detail="没有找到K线数据")

        # 转换为 DataFrame
        kline_data = []
        for k in kline_response.klines:
            kline_data.append({
                'date': k.date,
                'open': k.open,
                'close': k.close,
                'high': k.high,
                'low': k.low,
                'volume': k.volume
            })
        df = pd.DataFrame(kline_data)

        # 创建策略
        strategy = StrategyFactory.create_strategy(
            request.strategy_id,
            request.strategy_params
        )

        # 生成交易信号
        logger.info(f"生成交易信号: 策略={strategy.name}")
        signals = strategy.generate_signals(df)
        logger.info(f"生成了 {len(signals)} 个交易信号")

        # 调试：打印前几个信号和日期
        if signals:
            logger.info(f"首个信号: date={signals[0].date} (type={type(signals[0].date)}), action={signals[0].action}")
            logger.info(f"首个K线: date={df.iloc[0]['date']} (type={type(df.iloc[0]['date'])})")

        # 创建回测引擎
        engine = BacktestEngine(initial_capital=request.initial_capital)

        # 计算买入持有基准
        initial_price = df.iloc[0]['close']
        buy_hold_shares = int((request.initial_capital * 0.999) / initial_price / 100) * 100  # 扣除手续费后能买的股数
        buy_hold_curve = []  # 买入持有资金曲线

        # 执行回测
        signal_idx = 0
        for i, row in df.iterrows():
            date = row['date']
            close_price = row['close']

            # 更新持仓价格
            engine.update_prices(date, {request.code: close_price})

            # 检查是否有交易信号
            if signal_idx < len(signals) and signals[signal_idx].date == date:
                signal = signals[signal_idx]
                signal_idx += 1

                if signal.action == 'buy':
                    # 买入
                    if not engine.has_position(request.code):
                        # 计算买入数量
                        buy_amount = engine.cash * request.position_ratio
                        shares = int(buy_amount / close_price / 100) * 100  # 整百股

                        success = engine.buy(
                            date=date,
                            code=request.code,
                            name=kline_response.stock_info.name,
                            price=close_price,
                            shares=shares,
                            reason=signal.reason
                        )

                        if success:
                            logger.info(f"{date} 买入 {shares}股 @ {close_price:.2f} - {signal.reason}")

                elif signal.action == 'sell':
                    # 卖出
                    if engine.has_position(request.code):
                        pos = engine.get_current_position(request.code)
                        success = engine.sell(
                            date=date,
                            code=request.code,
                            name=kline_response.stock_info.name,
                            price=close_price,
                            shares=pos.shares,
                            reason=signal.reason
                        )

                        if success:
                            logger.info(f"{date} 卖出 {pos.shares}股 @ {close_price:.2f} - {signal.reason}")

            # 记录每日状态
            engine.record_daily(date)

            # 记录买入持有基准
            buy_hold_value = buy_hold_shares * close_price
            buy_hold_curve.append({
                "date": date,
                "value": buy_hold_value
            })

        # 计算买入持有基准收益率
        buy_hold_final_value = buy_hold_curve[-1]["value"] if buy_hold_curve else request.initial_capital
        buy_hold_return = (buy_hold_final_value - request.initial_capital) / request.initial_capital * 100

        # 计算绩效指标
        metrics = BacktestMetrics(
            daily_records=engine.daily_records,
            trades=engine.trades,
            initial_capital=request.initial_capital
        )

        # 构建响应
        final_value = engine.get_total_value()

        # 计算超额收益
        excess_return = metrics.total_return - buy_hold_return

        # 转换交易记录
        trade_records = [
            TradeRecord(
                date=t.date,
                code=t.code,
                name=t.name,
                action=t.action,
                price=t.price,
                shares=t.shares,
                amount=t.amount,
                commission=t.commission,
                reason=t.reason
            )
            for t in engine.trades
        ]

        # 转换每日持仓
        daily_positions = []
        for dr in engine.daily_records:
            positions = [
                PositionInfo(
                    code=p.code,
                    name=p.name,
                    shares=p.shares,
                    avg_price=p.avg_price,
                    current_price=p.current_price,
                    market_value=p.market_value,
                    cost=p.cost,
                    profit=p.profit,
                    profit_pct=p.profit_pct
                )
                for p in dr.positions
            ]
            daily_positions.append(DailyPosition(
                date=dr.date,
                cash=dr.cash,
                market_value=dr.market_value,
                total_value=dr.total_value,
                positions=positions
            ))

        # 构建资金曲线
        equity_curve = [
            {"date": dr.date, "value": dr.total_value}
            for dr in engine.daily_records
        ]

        # 构建绩效指标（包含基准对比）
        metrics_dict = metrics.to_dict()
        metrics_dict['buy_hold_return'] = round(buy_hold_return, 2)
        metrics_dict['excess_return'] = round(excess_return, 2)

        result = BacktestData(
            stock_code=request.code,
            stock_name=kline_response.stock_info.name,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy_name=strategy.name,
            strategy_params=request.strategy_params,
            initial_capital=request.initial_capital,
            final_capital=final_value,
            metrics=BacktestMetricsData(**metrics_dict),
            daily_records=daily_positions,
            trades=trade_records,
            equity_curve=equity_curve,
            buy_hold_curve=buy_hold_curve
        )

        logger.info(f"回测完成: 总收益率={metrics.total_return:.2f}%, 交易次数={len(trade_records)}")

        return BacktestResponse(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"回测失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
