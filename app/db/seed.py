from sqlalchemy import select
from app.db.models import Service,ServiceCode,Setting
from app.db.session import SessionLocal

async def seed_services():
    defaults=[
        (ServiceCode.IDENTITY.value,"تثبیت هویت",280_000,"خدمت تثبیت هویت"),
        (ServiceCode.KHODNEVIS.value,"کد رهگیری خودنویس",1_700_000,"خدمت کد رهگیری خودنویس"),
        (ServiceCode.FIDA.value,"ثبت‌نام کد فیدا غیرحضوری",100,"ثبت‌نام کد فیدا غیرحضوری"),
        (ServiceCode.DOLATMAN_LOGIN.value,"رفع مشکل ورود به درگاه دولت من",100,"رفع مشکل ورود به درگاه دولت من"),
        (ServiceCode.STUDENT_SCREENING.value,"آزمون غربالگری دانش‌آموزان",400,"آزمون غربالگری دانش‌آموزان"),
        (ServiceCode.OTHER_SERVICE.value,"درخواست خدمات دیگر",100,"ثبت درخواست خدمت دیگر"),
    ]
    async with SessionLocal() as session:
        for code,name,price,description in defaults:
            row=(await session.execute(select(Service).where(Service.code==code))).scalar_one_or_none()
            if row is None:
                session.add(Service(code=code,name=name,price_toman=price,description=description,enabled=True))
            elif code in {ServiceCode.FIDA.value, ServiceCode.DOLATMAN_LOGIN.value, ServiceCode.STUDENT_SCREENING.value, ServiceCode.OTHER_SERVICE.value} and row.price_toman == 0:
                # Backfill the requested 100-toman tariff for existing installations,
                # while preserving any nonzero tariff configured by an administrator.
                row.price_toman = price
                row.enabled = True
        # One-time migration: move the old 100-toman screening unit tariff to 400.
        # The marker ensures future admin-configured prices are never overwritten at restart.
        migration_key = "migration:student_screening_unit_price_400_v1"
        migration = (await session.execute(select(Setting).where(Setting.key == migration_key))).scalar_one_or_none()
        if migration is None:
            screening = (await session.execute(select(Service).where(Service.code == ServiceCode.STUDENT_SCREENING.value))).scalar_one_or_none()
            if screening is not None and screening.price_toman == 100:
                screening.price_toman = 400
            session.add(Setting(key=migration_key, value="done"))
        for key in ("card_number","card_holder"):
            row=(await session.execute(select(Setting).where(Setting.key==key))).scalar_one_or_none()
            if row is None:session.add(Setting(key=key,value=""))
        await session.commit()
