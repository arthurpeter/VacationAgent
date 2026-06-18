from pydantic import BaseModel, Field
from typing import Optional, Dict, Union


class BaseStrategy(BaseModel):
    enabled: bool = True


class WalkingStrategy(BaseStrategy):
    pass


class PublicTransportStrategy(BaseStrategy):
    details_loaded: bool = False
    pass_price_est: Optional[float] = None
    currency: Optional[str] = None
    official_link: Optional[str] = None
    operating_hours: Dict[str, str] = Field(default={"open": "05:30", "close": "23:30"})


class RideShareStrategy(BaseStrategy):
    pass


class RentalCarStrategy(BaseStrategy):
    details_loaded: bool = False
    official_link: Optional[str] = None
    daily_price_est: Optional[float] = None
    currency: str = "EUR"
    ztl_warning: bool = False
    operating_hours: Dict[str, str] = Field(
        default={"open": "08:00", "close": "20:00"},
        description="Standard rental office hours",
    )

    includes_parking_buffer: bool = True
    ignore_ztl_zones: bool = False


class IntercityStrategy(BaseStrategy):
    preferred_mode: Optional[str] = None
    booking_required: bool = True
    official_link: Optional[str] = None


class MobilityConfig(BaseModel):
    strategies: Dict[
        str,
        Union[
            WalkingStrategy,
            PublicTransportStrategy,
            RideShareStrategy,
            RentalCarStrategy,
            IntercityStrategy,
        ],
    ] = Field(default_factory=dict)

    @classmethod
    def create_default(cls):
        """Initializes a standard setup for a new trip."""
        return cls(
            strategies={
                "walking": WalkingStrategy(enabled=True),
                "public_transport": PublicTransportStrategy(enabled=True),
                "taxi_uber": RideShareStrategy(enabled=True),
                "rental_car": RentalCarStrategy(enabled=False),
                "intercity": IntercityStrategy(enabled=True),
            }
        )

    def apply_rental_logic(self, daily_price: float):
        """
        Enables rental car and disables all other strategies except walking.
        This ensures the routing engine doesn't produce conflicting options.
        """

        self.strategies["rental_car"].enabled = True
        self.strategies["rental_car"].daily_price_est = daily_price

        modes_to_disable = ["public_transport", "taxi_uber", "intercity"]
        for mode in modes_to_disable:
            if mode in self.strategies:
                self.strategies[mode].enabled = False

        self.strategies["walking"].enabled = True

        return self
