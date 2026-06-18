from sqlalchemy import JSON, Boolean, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.ext.asyncio import AsyncSession


class GlobalAttraction(Base):
    __tablename__ = "global_attractions"

    id = Column(Integer, primary_key=True, index=True)

    external_place_id = Column(String, unique=True, index=True, nullable=True)
    wikidata_id = Column(String, nullable=True)
    official_name = Column(String, index=True, nullable=False)
    opening_hours = Column(JSON, nullable=True)

    city = Column(String, index=True, nullable=False)
    state_province = Column(String, index=True, nullable=True)
    country = Column(String, index=True, nullable=False)
    formatted_address = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    category = Column(String, index=True)
    tags = Column(String, nullable=True)
    description = Column(Text)
    image_url = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    price_tier = Column(Integer, nullable=True)

    recommended_duration_mins = Column(Integer, default=120)
    tod_preference = Column(String, nullable=True)
    needs_reservation = Column(Boolean, nullable=True, default=False)

    search_count = Column(Integer, default=1, nullable=False)
    must_count = Column(Integer, default=0, nullable=False)
    want_count = Column(Integer, default=0, nullable=False)
    optional_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @classmethod
    def dynamic_relevance_rank(cls, gravity: float = 1.5):
        """
        Compiles the Laplace-Smoothed Engagement Quality Model directly into a SQL statement.
        Allows multi-factor ordering using the native database engine execution block.
        """
        intent_score = (
            (3.0 * cls.must_count) + (1.5 * cls.want_count) + (0.5 * cls.optional_count)
        )

        conversion_rate = (intent_score + 1.0) / (cls.search_count + 10.0)

        raw_score = intent_score * conversion_rate

        age_years = func.extract("year", func.age(func.now(), cls.created_at))
        age_months = func.extract("month", func.age(func.now(), cls.created_at))
        delta_months = (age_years * 12.0) + age_months

        decay_denominator = func.pow(delta_months + 1.0, gravity)

        return raw_score / decay_denominator

    @classmethod
    async def track_search_metrics(cls, db: AsyncSession, attraction_ids: list[int]):
        """
        Executes an atomic SQL update pass over selected IDs.
        Increments metrics in a single network trip without risking state drift.
        """
        if not attraction_ids:
            return

        from sqlalchemy import update

        stmt = (
            update(cls)
            .where(cls.id.in_(attraction_ids))
            .values(search_count=cls.search_count + 1)
        )

        await db.execute(stmt)
        await db.commit()
