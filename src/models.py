from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Table, Column, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List

db = SQLAlchemy()

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    lastname: Mapped[str] = mapped_column(String(120), nullable=False)
    suscription_date: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    FavoritePlanet: Mapped[List["Planet"]] = relationship(secondary='favorite_planets', back_populates='user_favorites')
    FavoriteCharacter: Mapped[List["Character"]] = relationship(secondary='favorite_characters', back_populates='user_favorites')



    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "lastname": self.lastname,
            "subscription_date": self.subscription_date.isoformat(), 
        }

class Planet(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    material: Mapped[str] = mapped_column(String(120), nullable=False)
    population: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    user_favorites: Mapped[List["User"] ] = relationship(secondary='favorite_planets', back_populates="FavoritePlanet")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "size": self.size,
            "material": self.material,
            "population": self.population,
        }
    
class Character(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[str] = mapped_column(String(120), nullable=False)
    affiliation: Mapped[str] = mapped_column(String(120), nullable=False)

    user_favorites: Mapped[List["User"] ] = relationship(secondary='favorite_characters', back_populates="FavoriteCharacter")


    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "genre": self.genre,
            "affiliation": self.affiliation,
        }
    
FavoritePlanet = Table(
    'favorite_planets',
    db.metadata,
    Column('planet_id', ForeignKey('planet.id'), primary_key=True),
    Column('user_id', ForeignKey('user.id'), primary_key=True)
)

FavoriteCharacter = Table(
    'favorite_characters',
    db.metadata,
    Column('character_id', ForeignKey('character.id'), primary_key=True),
    Column('user_id', ForeignKey('user.id'), primary_key=True)
)