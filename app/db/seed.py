from sqlalchemy import select
from app.db.models import Service,ServiceCode
from app.db.session import SessionLocal

async def seed_services():
    defaults=[
        (ServiceCode.IDENTITY.value,"تثبیت هویت",280_000,"خدمت تثبیت هویت"),
        (ServiceCode.KHODNEVIS.value,"کد رهگیری خودنویس",1_700_000,"خدمت کد رهگیری خودنویس"),
    ]
    async with SessionLocal() as session:
        for code,name,price,description in defaults:
            row=(await session.execute(select(Service).where(Service.code==code))).scalar_one_or_none()
            if row is None: session.add(Service(code=code,name=name,price_toman=price,description=description,enabled=True))
        await session.commit()
