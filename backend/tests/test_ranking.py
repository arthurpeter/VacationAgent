import pytest
import datetime
from sqlalchemy import create_engine, select, event
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.global_attraction import GlobalAttraction

DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(name="db_session")
def fixture_db_session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        def mock_age(now_val, created_val):
            if not now_val or not created_val:
                return "0000-01-01 00:00:00"
            try:
                t1 = datetime.datetime.fromisoformat(str(now_val).split('.')[0].replace(" ", "T"))
                t2 = datetime.datetime.fromisoformat(str(created_val).split('.')[0].replace(" ", "T"))
                
                diff_years = t1.year - t2.year
                diff_months = t1.month - t2.month
                
                if diff_months < 0:
                    diff_years -= 1
                    diff_months += 12
                
                diff_years = max(0, min(9999, diff_years))
                diff_months = max(0, min(11, diff_months))
                
                return f"{diff_years:04d}-{diff_months+1:02d}-01 00:00:00"
            except Exception:
                return "0000-01-01 00:00:00"

        def mock_pow(base, exp):
            try:
                if base is None:
                    return 0.0
                return float(base) ** float(exp)
            except Exception:
                return 0.0

        dbapi_connection.create_function("age", 2, mock_age)
        dbapi_connection.create_function("pow", 2, mock_pow)

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_dynamic_relevance_rank_sql_generation(db_session):
    antipa = GlobalAttraction(
        official_name="Muzeul Antipa",
        city="Bucharest",
        country="Romania",
        latitude=44.4531,
        longitude=26.0845,
        search_count=100,
        must_count=40,
        want_count=10,
        optional_count=5,
        created_at=datetime.datetime.now() - datetime.timedelta(days=180),
    )

    ateneu_roman = GlobalAttraction(
        official_name="Ateneul Roman",
        city="Bucharest",
        country="Romania",
        latitude=44.4412,
        longitude=26.0973,
        search_count=150,
        must_count=20,
        want_count=10,
        optional_count=0,
        created_at=datetime.datetime.now() - datetime.timedelta(days=180),
    )
    arcul_de_triumf = GlobalAttraction(
        official_name="Arcul de Triumf",
        city="Bucharest",
        country="Romania",
        latitude=44.4671,
        longitude=26.0784,
        search_count=150,
        must_count=20,
        want_count=10,
        optional_count=0,
        created_at=datetime.datetime.now() - datetime.timedelta(days=365),
    )

    parcul_herastrau = GlobalAttraction(
        official_name="Parcul Herastrau",
        city="Bucharest",
        country="Romania",
        latitude=44.4712,
        longitude=26.0792,
        search_count=100,
        must_count=10,
        want_count=10,
        optional_count=0,
        created_at=datetime.datetime.now() - datetime.timedelta(days=180),
    )
    palatul_parlamentului = GlobalAttraction(
        official_name="Palatul Parlamentului",
        city="Bucharest",
        country="Romania",
        latitude=44.4275,
        longitude=26.1361,
        search_count=1000,
        must_count=10,
        want_count=10,
        optional_count=0,
        created_at=datetime.datetime.now() - datetime.timedelta(days=180),
    )

    carturesti_carusel = GlobalAttraction(
        official_name="Carturesti Carusel",
        city="Bucharest",
        country="Romania",
        latitude=44.4318,
        longitude=26.1024,
        search_count=100,
        must_count=1,
        want_count=1,
        optional_count=50,
        created_at=datetime.datetime.now() - datetime.timedelta(days=180),
    )

    db_session.add_all([
        antipa, 
        ateneu_roman, 
        arcul_de_triumf, 
        parcul_herastrau, 
        palatul_parlamentului, 
        carturesti_carusel
    ])
    db_session.commit()

    stmt = select(GlobalAttraction).order_by(
        GlobalAttraction.dynamic_relevance_rank().desc()
    )
    results = db_session.execute(stmt).scalars().all()

    assert len(results) == 6
    
    assert results[0].official_name == "Muzeul Antipa"
    
    assert results[1].official_name == "Ateneul Roman"
    
    assert results[2].official_name == "Parcul Herastrau"
    
    assert results[3].official_name == "Arcul de Triumf"
    
    assert results[4].official_name == "Carturesti Carusel"
    
    assert results[5].official_name == "Palatul Parlamentului"