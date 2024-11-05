import sqlalchemy
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src import database as db
from src.utilities import CatalogManager

logger = logging.getLogger(__name__)

router = APIRouter()

class CatalogItem(BaseModel):
    sku: str
    name: str
    quantity: int
    price: int
    potion_type: List[int]  # [red_ml, green_ml, blue_ml, dark_ml]


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """Get available potions for sale, maximum 6 items."""
    try:
        with db.engine.begin() as conn:
            items = CatalogManager.get_available_potions(conn)
            items_dict = [dict(customer) for customer in items]
            
            logger.debug(f"Generated catalog with {len(items)} items")
            logger.debug(items_dict)
            
            return [
                CatalogItem(
                    sku=item['sku'],
                    name=item['name'],
                    quantity=item['quantity'],
                    price=item['price'],
                    potion_type=item['potion_type']
                )
                for item in items
            ]
            
    except Exception as e:
        logger.error(f"Failed to generate catalog: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate catalog")