"""
交通查询工具

调用交通规划协调器（Subagents 主 Agent）。
路线1 节点应通过本模块调用，勿在 graph/nodes 内直连 HTTP 或 MCP。
"""

from __future__ import annotations

from langchain_core.tools import tool
from loguru import logger

from app.agents.transport.coordinator import (
    run_transport_coordinator,
    run_transport_coordinator_async,
)
from app.agents.transport.driving_subagent import run_driving_subagent, run_driving_subagent_async
from app.agents.transport.flight_subagent import run_flight_subagent, run_flight_subagent_async
from app.agents.transport.train_subagent import run_train_subagent, run_train_subagent_async

def fetch_flight_info(origin: str, destination: str, departure_date: str) -> str:
    """纯函数入口：查询航班信息（航班 Subagent）。"""
    return run_flight_subagent(origin, destination, departure_date)


async def fetch_flight_info_async(
    origin: str,
    destination: str,
    departure_date: str,
) -> str:
    """异步查询航班信息。"""
    return await run_flight_subagent_async(origin, destination, departure_date)


def fetch_train_info(origin: str, destination: str, departure_date: str) -> str:
    """纯函数入口：查询高铁信息（高铁 Subagent）。"""
    return run_train_subagent(origin, destination, departure_date)


async def fetch_train_info_async(
    origin: str,
    destination: str,
    departure_date: str,
) -> str:
    """异步查询高铁信息。"""
    return await run_train_subagent_async(origin, destination, departure_date)


def fetch_driving_route(origin: str, destination: str) -> str:
    """纯函数入口：查询自驾路线（自驾 Subagent）。"""
    return run_driving_subagent(origin, destination)


async def fetch_driving_route_async(origin: str, destination: str) -> str:
    """异步查询自驾路线。"""
    return await run_driving_subagent_async(origin, destination)


def fetch_transport_options(
    origin_city: str,
    destination_city: str,
    departure_date: str,
    *,
    transport_type: str | None = None,
    passenger_count: int = 1,
    user_preference: str = "",
) -> str:
    """交通规划协调器入口（同步）。"""
    return run_transport_coordinator(
        origin_city,
        destination_city,
        departure_date,
        passenger_count=passenger_count,
        user_preference=user_preference,
        transport_type=transport_type,
    )


async def fetch_transport_options_async(
    origin_city: str,
    destination_city: str,
    departure_date: str,
    *,
    transport_type: str | None = None,
    passenger_count: int = 1,
    user_preference: str = "",
) -> str:
    """交通规划协调器入口（异步）。"""
    return await run_transport_coordinator_async(
        origin_city,
        destination_city,
        departure_date,
        passenger_count=passenger_count,
        user_preference=user_preference,
        transport_type=transport_type,
    )


def fetch_transport_plan(
    origin: str,
    destination: str,
    departure_date: str,
    *,
    passenger_count: int = 1,
    user_preference: str = "",
    transport_type: str | None = None,
) -> str:
    """兼容别名：fetch_transport_options。"""
    return fetch_transport_options(
        origin,
        destination,
        departure_date,
        transport_type=transport_type,
        passenger_count=passenger_count,
        user_preference=user_preference,
    )


async def fetch_transport_plan_async(
    origin: str,
    destination: str,
    departure_date: str,
    *,
    passenger_count: int = 1,
    user_preference: str = "",
    transport_type: str | None = None,
) -> str:
    """兼容别名：fetch_transport_options_async。"""
    return await fetch_transport_options_async(
        origin,
        destination,
        departure_date,
        transport_type=transport_type,
        passenger_count=passenger_count,
        user_preference=user_preference,
    )


@tool
async def query_transport_options(
    origin_city: str,
    destination_city: str,
    departure_date: str,
    transport_type: str = "",
    passenger_count: int = 1,
) -> str:
    """
    查询交通选项（调用交通规划协调器）

    Args:
        origin_city: 出发城市
        destination_city: 目的地城市
        departure_date: 出发日期 YYYY-MM-DD
        transport_type: 交通方式（可选）flight / train / driving
        passenger_count: 乘客人数

    Returns:
        格式化的交通选项信息
    """
    logger.info("调用交通规划协调器: {} -> {}", origin_city, destination_city)
    normalized_type = transport_type.strip() or None
    return await fetch_transport_options_async(
        origin_city,
        destination_city,
        departure_date,
        transport_type=normalized_type,
        passenger_count=passenger_count,
    )


@tool
def query_transport_plan(
    origin: str,
    destination: str,
    departure_date: str,
    passenger_count: int = 1,
) -> str:
    """
    交通规划协调器（同步，Route 1 step_context 使用）

    根据出行场景调度航班 / 高铁 / 自驾 Subagent，返回整合后的交通方案。
    """
    return fetch_transport_options(
        origin,
        destination,
        departure_date,
        passenger_count=passenger_count,
    )


@tool
def query_flight_info(origin: str, destination: str, departure_date: str) -> str:
    """查询航班信息（航班 Subagent）。"""
    return fetch_flight_info(origin, destination, departure_date)


@tool
def query_train_info(origin: str, destination: str, departure_date: str) -> str:
    """查询高铁信息（高铁 Subagent）。"""
    return fetch_train_info(origin, destination, departure_date)


@tool
def query_driving_route(origin: str, destination: str) -> str:
    """查询自驾路线（自驾 Subagent）。"""
    return fetch_driving_route(origin, destination)
