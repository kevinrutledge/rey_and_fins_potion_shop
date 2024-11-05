import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from enum import Enum
from src.api import auth
from src import database as db
from src.utilities import CartManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

class CartItem(BaseModel):
    quantity: int

class CartCheckout(BaseModel):
    payment: str

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """Record customers visiting the shop."""
    customers_dict = [dict(customer) for customer in customers]
    logger.debug(f"Recording visit - id: {visit_id}, customers: {len(customers)}")
    
    try:
        with db.engine.begin() as conn:
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            visit_record_id = CartManager.record_customer_visit(
                conn, 
                visit_id, 
                customers_dict, 
                time_id
            )
            
            logger.info(f"Successfully recorded visit for {len(customers)} customers")
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to record customer visit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record customer visit")

@router.post("/")
def create_cart(new_cart: Customer):
    """Create new cart for customer."""
    logger.debug(f"Creating cart for customer: {new_cart.customer_name}")
    
    try:
        with db.engine.begin() as conn:
            time_id, visit_id = conn.execute(
                sqlalchemy.text("""
                    WITH latest_game_time AS (
                        SELECT game_time_id 
                        FROM current_game_time 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    )
                    SELECT 
                        lgt.game_time_id,
                        cv.visit_id
                    FROM latest_game_time lgt
                    CROSS JOIN (
                        SELECT visit_id 
                        FROM customer_visits 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    ) cv
                """)
            ).first()
            
            cart_id = CartManager.create_cart(conn, new_cart.dict(), time_id, visit_id)
            
            logger.info(
                f"Created cart for customer name: {new_cart.customer_name}, "
                f"class: {new_cart.character_class}, level: {new_cart.level}"
            )
            return {"cart_id": cart_id}
            
    except Exception as e:
        logger.error(f"Failed to create cart: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create cart")

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """Add or update item quantity in cart."""
    logger.debug(f"Updating cart - id: {cart_id}, sku: {item_sku}, quantity: {cart_item.quantity}")
    
    try:
        with db.engine.begin() as conn:
            cart = CartManager.validate_cart_status(conn, cart_id)
            

            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            CartManager.update_cart_item(
                conn, 
                cart_id, 
                item_sku, 
                cart_item.quantity, 
                time_id,
                cart['visit_id']
            )
            
            logger.info(f"Updated cart {cart_id} - item: {item_sku}, quantity: {cart_item.quantity}")
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update cart item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update cart item")

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """Process cart checkout."""
    logger.debug(f"Processing checkout - cart: {cart_id}")
    
    try:
        with db.engine.begin() as conn:
            cart = CartManager.validate_cart_status(conn, cart_id)
            
            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT game_time_id 
                    FROM current_game_time 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
            ).scalar_one()
            
            result = CartManager.process_checkout(
                conn, 
                cart_id,
                cart_checkout.payment, 
                time_id
            )
            
            logger.info(
                f"Completed checkout - cart: {cart_id}, "
                f"total potions: {result['total_potions_bought']}, "
                f"total gold: {result['total_gold_paid']}"
            )
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process checkout")

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }