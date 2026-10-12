from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import password_encode
from app.models import User
from app.schemas.users import UserPartialUpdate, UserPasswordUpdate


async def partial_update(data: UserPartialUpdate, user: User, db: AsyncSession):

    new_data = data.model_dump(exclude_unset=True)
    if new_data:

        for field, val in new_data.items():
            setattr(user, field, val)

    await db.commit()
    await db.refresh(user)
    return user


async def update_my_password(user: User, data: UserPasswordUpdate, db: AsyncSession):
    new_pass = password_encode(data.hashed_password)
    await db.execute(
        update(User).where(User.id == user.id).values(hashed_password=new_pass)
    )
    await db.commit()

    return {"message": "Password update successfull"}
