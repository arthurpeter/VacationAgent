import pytest
import datetime
from sqlalchemy import create_engine, select, event, func
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.global_attraction import GlobalAttraction

DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("age", 2, lambda now, created_at: created_at)
        dbapi_connection.create_function("extract", 2, lambda field, val: 0.0)
        dbapi_connection.create_function("pow", 2, lambda base, exp: float(base) ** float(exp))

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_dynamic_relevance_rank_sql_generation(db_session):
    atractie_1 = GlobalAttraction(
        official_name="Muzeul Antipa",
        city="Bucharest",
        country="Romania",
        latitude=44.4531,
        longitude=26.0845,
        search_count=100,
        must_count=30,
        want_count=10,
        optional_count=5,
        created_at=datetime.datetime.now()
    )
    
    atractie_2 = GlobalAttraction(
        official_name="Parcul Herastrau",
        city="Bucharest",
        country="Romania",
        latitude=44.4712,
        longitude=26.0792,
        search_count=80,
        must_count=15,
        want_count=20,
        optional_count=10,
        created_at=datetime.datetime.now()
    )
    
    atractie_3 = GlobalAttraction(
        official_name="Un magazin oarecare",
        city="Bucharest",
        country="Romania",
        latitude=44.4325,
        longitude=26.1039,
        search_count=500,
        must_count=1,
        want_count=2,
        optional_count=20,
        created_at=datetime.datetime.now()
    )
    
    atractie_veche_dar_buna = GlobalAttraction(
        official_name="Arcul de Triumf",
        city="Bucharest",
        country="Romania",
        latitude=44.4671,
        longitude=26.0784,
        search_count=150,
        must_count=25,
        want_count=5,
        optional_count=2,
        created_at=datetime.datetime.now() - datetime.timedelta(days=730)
    )
    
    db_session.add_all([atractie_1, atractie_2, atractie_3, atractie_veche_dar_buna])
    db_session.commit()
    
    stmt = (
        select(GlobalAttraction)
        .order_by(GlobalAttraction.dynamic_relevance_rank().desc())
    )
    
    results = db_session.execute(stmt).scalars().all()
    
    assert len(results) == 4
    assert results[0].official_name == "Muzeul Antipa"
    assert results[1].official_name == "Parcul Herastrau"
    assert results[2].official_name == "Arcul de Triumf"
    assert results[3].official_name == "Un magazin oarecare"