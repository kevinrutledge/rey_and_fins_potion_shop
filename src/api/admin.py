import sqlalchemy
import logging
from fastapi import APIRouter, Depends, HTTPException
from src.api import auth
from src import database as db
from src.utilities import LedgerManager, StateValidator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """Reset game state to initial values."""
    try:
        with db.engine.begin() as conn:
            logger.debug("Starting game state reset")
            
            initial_state = StateValidator.get_current_state(conn)
            logger.debug(
                f"Pre-reset state - gold: {initial_state['gold']}, "
                f"potions: {initial_state['total_potions']}, "
                f"ml: {initial_state['total_ml']}"
            )
            
            conn.execute(
                sqlalchemy.text("""
                    TRUNCATE TABLE active_strategy CASCADE;
                    TRUNCATE TABLE current_game_time CASCADE;
                    TRUNCATE TABLE ledger_entries CASCADE;
                """)
            )
            
            conn.execute(
                sqlalchemy.text("UPDATE potions SET current_quantity = 0")
            )

            time_id = conn.execute(
                sqlalchemy.text("""
                    SELECT time_id
                    FROM game_time
                    ORDER BY time_id ASC
                    LIMIT 1
                """)
            ).scalar_one()

            LedgerManager.create_ledger_entry(
                conn=conn,
                time_id=time_id,
                entry_type='ADMIN_CHANGE',
                gold_change=100
            )

            premium_strategy_id = conn.execute(
                sqlalchemy.text("SELECT strategy_id FROM strategies WHERE name = 'PREMIUM'")
            ).scalar_one()

            conn.execute(
                sqlalchemy.text("""
                    INSERT INTO active_strategy (strategy_id, game_time_id)
                    VALUES (:strategy_id, :game_time_id)
                """),
                {
                    "strategy_id": premium_strategy_id,
                    "game_time_id": time_id
                }
            )

            if not StateValidator.verify_reset_state(conn):
                logger.error("Reset validation failed - state does not match initial values")
                raise HTTPException(status_code=500, detail="Reset failed - state validation error")
            
            final_state = StateValidator.get_current_state(conn)    
            logger.debug(
                f"Post-reset state - gold: {final_state['gold']}, "
                f"potions: {final_state['total_potions']}, "
                f"ml: {final_state['total_ml']}"
            )
            
            logger.info("Successfully reset game state to initial values")
            return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset game state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset game state")