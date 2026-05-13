from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class PreferenceMode(str, Enum):
    SMART = "smart_optimization"
    MANUAL = "manual_rules"

# --- BASE STRATEGY ---
class BaseStrategy(BaseModel):
    enabled: bool = True
    priority: int = 1

# --- SPECIFIC STRATEGIES ---

class WalkingStrategy(BaseStrategy):
    max_time_mins: int = Field(default=15, description="Don't walk if it takes longer than this.")
    
class PublicTransportStrategy(BaseStrategy):
    details_loaded: bool = False
    pass_price_est: Optional[float] = None
    currency: Optional[str] = None
    official_link: Optional[str] = None
    operating_hours: Dict[str, str] = Field(default={"open": "05:30", "close": "23:30"})

class RideShareStrategy(BaseStrategy):
    trigger_late_night: bool = True
    trigger_airport_transfer: bool = True
    min_dist_km: float = Field(default=10000.0, description="Use taxi if distance > X km")

class RentalCarStrategy(BaseStrategy):
    details_loaded: bool = False
    official_link: Optional[str] = None
    daily_price_est: Optional[float] = None
    currency: str = "EUR"
    ztl_warning: bool = False
    operating_hours: Dict[str, str] = Field(
        default={"open": "08:00", "close": "20:00"},
        description="Standard rental office hours"
    )
    
    includes_parking_buffer: bool = True 
    ignore_ztl_zones: bool = False

class IntercityStrategy(BaseStrategy):
    preferred_mode: Optional[str] = None # "train", "bus", or None
    booking_required: bool = True
    official_link: Optional[str] = None

# --- THE MASTER CONFIG ---

class MobilityConfig(BaseModel):
    preference_mode: PreferenceMode = PreferenceMode.SMART
    strategies: Dict[str, Union[
        WalkingStrategy, 
        PublicTransportStrategy, 
        RideShareStrategy, 
        RentalCarStrategy, 
        IntercityStrategy
    ]] = Field(default_factory=dict)

    @classmethod
    def create_default(cls):
        """Initializes a standard setup for a new trip."""
        return cls(
            preference_mode=PreferenceMode.SMART,
            strategies={
                "walking": WalkingStrategy(priority=1, max_time_mins=15),
                "public_transport": PublicTransportStrategy(priority=2),
                "taxi_uber": RideShareStrategy(priority=3),
                "rental_car": RentalCarStrategy(enabled=False, priority=1),
                "intercity": IntercityStrategy(priority=4)
            }
        )
    
    def apply_rental_logic(self, daily_price: float):
        """
        Enables rental car and disables all other strategies except walking.
        This ensures the routing engine doesn't produce conflicting options.
        """
        # 1. Enable Rental
        self.strategies["rental_car"].enabled = True
        self.strategies["rental_car"].daily_price_est = daily_price
        self.strategies["rental_car"].priority = 1 # Top priority when active

        # 2. Disable conflicting modes
        modes_to_disable = ["public_transport", "taxi_uber", "intercity"]
        for mode in modes_to_disable:
            if mode in self.strategies:
                self.strategies[mode].enabled = False
        
        self.strategies["walking"].enabled = True
        
        return self