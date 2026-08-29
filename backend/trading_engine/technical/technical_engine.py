"""
BALLY FLOW - Technical Analysis Engine

Authoritative entry point for TECHNICAL MODE.

Responsibilities
----------------
This module:

    - accepts symbol and candle data
    - runs the complete technical-analysis pipeline
    - preserves dependency order between technical components
    - produces a standardized technical-analysis result
    - exposes technical evidence to downstream layers

This module MUST NOT:

    - perform fundamental analysis
    - perform hybrid decision-making
    - make the final BUY / SELL / NO_TRADE decision
    - execute trades
    - place MT5 orders
    - manage risk
    - calculate position size

TECHNICAL PIPELINE
------------------

    Candles
       |
       +--> Market Structure
       |
       +--> Liquidity
       |
       +--> Order Blocks --------+
       |                         |
       +--> Fair Value Gaps -----+
       |                         |
       +--> Breaker Blocks ------+
       |                         |
       +--> Premium / Discount --+
       |                         |
       +--> Supply / Demand -----+
       |                         |
       +--> Volume Profile ------+
       |
       v
    Technical Confluence
       |
       v
    Standardized Technical Result

Dependency Rules
----------------

Market Structure is calculated first because several downstream
components can use its structural information.

Order Blocks and Fair Value Gaps receive Market Structure.

Breaker Blocks receive Market Structure and Order Blocks.

Premium / Discount receives Market Structure.

Supply / Demand receives Market Structure.

Liquidity and Volume Profile are independently calculated.

Technical Confluence receives all technical component results.

The Technical Engine itself does not decide whether a trade should
be taken.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.trading_engine.technical.confluence.market_structure import (
    MarketStructure,
)
from backend.trading_engine.technical.confluence.liquidity import (
    Liquidity,
)
from backend.trading_engine.technical.confluence.order_blocks import (
    OrderBlocks,
)
from backend.trading_engine.technical.confluence.fvg import (
    FairValueGaps,
)
from backend.trading_engine.technical.confluence.breaker_blocks import (
    BreakerBlocks,
)
from backend.trading_engine.technical.confluence.premium_discount import (
    PremiumDiscount,
)
from backend.trading_engine.technical.confluence.supply_demand_quality import (
    SupplyDemandQuality,
)
from backend.trading_engine.technical.confluence.volume_profile_quality import (
    VolumeProfileQuality,
)
from backend.trading_engine.technical.confluence.technical_confluence import (
    TechnicalConfluence,
)


class TechnicalEngine:
    """
    Central technical-analysis engine for BALLY FLOW.

    Technical Mode uses this engine independently.

    Hybrid Mode may consume the technical result, but this class
    never performs hybrid decision-making.

    Final trading decisions belong to the Decision Engine.
    """

    MODE = "technical"

    def __init__(self) -> None:
        self.name = "BALLY FLOW Technical Engine"

        # ----------------------------------------------------------
        # Technical component analyzers
        # ----------------------------------------------------------

        self.market_structure = MarketStructure()

        self.liquidity = Liquidity()

        self.order_blocks = OrderBlocks()

        self.fvg = FairValueGaps()

        self.breaker_blocks = BreakerBlocks()

        self.premium_discount = PremiumDiscount()

        self.supply_demand = SupplyDemandQuality()

        self.volume_profile = VolumeProfileQuality()

        # ----------------------------------------------------------
        # Technical confluence aggregator
        # ----------------------------------------------------------

        self.technical_confluence = TechnicalConfluence()

    # ==============================================================
    # PUBLIC API
    # ==============================================================

    def analyze(
        self,
        symbol: str,
        candles: Any,
        timeframe: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a market using technical information only.

        Parameters
        ----------
        symbol:
            Trading instrument, for example XAUUSD.

        candles:
            Candle/market-data collection supplied by the caller.

        timeframe:
            Optional timeframe identifier such as M15, H1 or H4.

        Returns
        -------
        dict
            Standardized technical-analysis result.

        Notes
        -----
        This method does not produce a final trading decision.
        """

        # ----------------------------------------------------------
        # Input validation
        # ----------------------------------------------------------

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        symbol = symbol.strip()

        if not symbol:
            raise ValueError("symbol is required")

        if candles is None:
            raise ValueError("candles are required")

        # ----------------------------------------------------------
        # Normalize candle availability without modifying the
        # original candle collection.
        #
        # The individual technical modules perform their own
        # validation/normalization.
        # ----------------------------------------------------------

        candle_count = self._candle_count(candles)

        # ----------------------------------------------------------
        # Extract optional volume information.
        #
        # Individual modules already support candle-contained volume,
        # so we only provide external volume when the caller supplies
        # a structure containing it separately.
        # ----------------------------------------------------------

        volume = self._extract_volume(candles)

        # ==========================================================
        # 1. MARKET STRUCTURE
        # ==========================================================

        market_structure = self.market_structure.analyze(
            candles=candles,
        )

        # ==========================================================
        # 2. LIQUIDITY
        # ==========================================================

        liquidity = self.liquidity.analyze(
            candles=candles,
        )

        # ==========================================================
        # 3. ORDER BLOCKS
        # ==========================================================

        order_blocks = self.order_blocks.analyze(
            candles=candles,
            structure=market_structure,
            volume=volume,
        )

        # ==========================================================
        # 4. FAIR VALUE GAPS
        # ==========================================================

        fvg = self.fvg.analyze(
            candles=candles,
            structure=market_structure,
            volume=volume,
        )

        # ==========================================================
        # 5. BREAKER BLOCKS
        # ==========================================================

        breaker_blocks = self.breaker_blocks.analyze(
            candles=candles,
            structure=market_structure,
            order_blocks=order_blocks,
            volume=volume,
        )

        # ==========================================================
        # 6. PREMIUM / DISCOUNT
        # ==========================================================

        current_price = self._extract_current_price(candles)

        premium_discount = self.premium_discount.analyze(
            candles=candles,
            structure=market_structure,
            current_price=current_price,
        )

        # ==========================================================
        # 7. SUPPLY / DEMAND QUALITY
        # ==========================================================

        supply_demand = self.supply_demand.analyze(
            candles=candles,
            structure=market_structure,
            volume=volume,
        )

        # ==========================================================
        # 8. VOLUME PROFILE QUALITY
        # ==========================================================

        volume_profile = self.volume_profile.analyze(
            candles=candles,
            volume=volume,
        )

        # ==========================================================
        # STANDARDIZED COMPONENT MAP
        # ==========================================================

        technical_components = {
            "market_structure": market_structure,
            "liquidity": liquidity,
            "order_blocks": order_blocks,
            "fvg": fvg,
            "breaker_blocks": breaker_blocks,
            "premium_discount": premium_discount,
            "supply_demand": supply_demand,
            "volume_profile": volume_profile,
        }

        # ==========================================================
        # TECHNICAL CONFLUENCE
        # ==========================================================

        technical_confluence = self.technical_confluence.calculate(
            technical_data=technical_components,
        )

        # ==========================================================
        # FINAL TECHNICAL RESULT
        # ==========================================================

        return {
            "mode": self.MODE,
            "symbol": symbol,
            "timeframe": timeframe,
            "technical_analysis": True,
            "status": "READY",

            "candle_count": candle_count,

            "analysis": {
                "market_structure": market_structure,
                "liquidity": liquidity,
                "order_blocks": order_blocks,
                "fvg": fvg,
                "breaker_blocks": breaker_blocks,
                "premium_discount": premium_discount,
                "supply_demand": supply_demand,
                "volume_profile": volume_profile,
                "technical_confluence": technical_confluence,
            },

            # Explicit architectural marker.
            "decision": None,
            "decision_authority": "downstream_decision_engine",
        }

    # ==============================================================
    # INPUT HELPERS
    # ==============================================================

    @staticmethod
    def _candle_count(candles: Any) -> int:
        """
        Determine candle count without changing the supplied data.
        """

        if isinstance(candles, dict):
            candle_data = candles.get("candles")

            if candle_data is None:
                return 0

            try:
                return len(candle_data)
            except TypeError:
                return 0

        try:
            return len(candles)
        except TypeError:
            try:
                return len(list(candles))
            except TypeError:
                return 0

    @staticmethod
    def _extract_volume(candles: Any) -> Optional[Any]:
        """
        Extract externally supplied volume when candles are provided
        as a dictionary containing a separate volume sequence.

        Normal candle dictionaries containing a 'volume' field are
        intentionally left untouched because all technical modules
        already support that format.
        """

        if not isinstance(candles, dict):
            return None

        for key in (
            "volume",
            "volumes",
        ):
            if key in candles:
                return candles[key]

        return None

    @staticmethod
    def _extract_current_price(candles: Any) -> Optional[float]:
        """
        Extract the latest candle close as the current analytical
        price.

        This is an analytical reference only. It is not an MT5
        execution price.
        """

        source = candles

        if isinstance(source, dict):
            source = source.get("candles")

        if source is None:
            return None

        try:
            sequence = list(source)
        except TypeError:
            return None

        if not sequence:
            return None

        latest = sequence[-1]

        try:
            if isinstance(latest, dict):
                return float(latest["close"])

            return float(getattr(latest, "close"))

        except (KeyError, AttributeError, TypeError, ValueError):
            return None


# ==================================================================
# CONVENIENCE API
# ==================================================================

def analyze_technical_market(
    symbol: str,
    candles: Any,
    timeframe: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convenience entry point for Technical Mode.
    """

    engine = TechnicalEngine()

    return engine.analyze(
        symbol=symbol,
        candles=candles,
        timeframe=timeframe,
    )