import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

import time
from uuid import UUID
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session

from database import engine, Base, get_db
import models
import schemas
import redis_client

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Redis Caching & Performance API",
    description="Task 04 - Redis Caching, Cache Expiration, and Invalidation",
    version="4.0.0"
)


# Middleware to measure request execution time and attach an X-Process-Time header
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response: Response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000  # in milliseconds
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}ms"
    return response


@app.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )

    db_user = models.User(name=payload.name, email=payload.email, age=payload.age)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Invalidate cached user lists on addition
    redis_client.delete_cache_pattern("users:all*")

    return db_user


@app.get("/users", response_model=List[schemas.UserResponse], status_code=status.HTTP_200_OK)
def get_all_users(response: Response, db: Session = Depends(get_db)):
    cache_key = "users:all"
    cached_data = redis_client.get_cache(cache_key)

    if cached_data is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_data

    # Cache miss: fetch from MySQL database
    users = db.query(models.User).all()
    user_list = [
        {"id": u.id, "name": u.name, "email": u.email, "age": u.age}
        for u in users
    ]

    # Store serialized result in Redis with 60-second expiration TTL
    redis_client.set_cache(cache_key, user_list)
    response.headers["X-Cache"] = "MISS"
    return user_list


@app.get("/users/{user_id}", response_model=schemas.UserResponse, status_code=status.HTTP_200_OK)
def get_user_by_id(user_id: UUID, response: Response, db: Session = Depends(get_db)):
    cache_key = f"users:{user_id}"
    cached_user = redis_client.get_cache(cache_key)

    if cached_user is not None:
        response.headers["X-Cache"] = "HIT"
        return cached_user

    # Cache miss: fetch from database
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )

    user_dict = {"id": user.id, "name": user.name, "email": user.email, "age": user.age}
    redis_client.set_cache(cache_key, user_dict)
    response.headers["X-Cache"] = "MISS"
    return user_dict


@app.put("/users/{user_id}", response_model=schemas.UserResponse, status_code=status.HTTP_200_OK)
def update_user(user_id: UUID, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields provided to update."
        )

    if "email" in update_data and update_data["email"] != user.email:
        if db.query(models.User).filter(models.User.email == update_data["email"]).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already taken."
            )

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    # Invalidate both specific user cache and all-users cache
    redis_client.delete_cache_pattern(f"users:{user_id}")
    redis_client.delete_cache_pattern("users:all*")

    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found."
        )

    db.delete(user)
    db.commit()

    # Invalidate associated caches
    redis_client.delete_cache_pattern(f"users:{user_id}")
    redis_client.delete_cache_pattern("users:all*")

    return None