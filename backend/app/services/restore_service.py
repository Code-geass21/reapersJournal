import os
import json
import zipfile
import shutil
import logging
from sqlalchemy.orm import Session
from app.utils.table_registry import BACKUP_REGISTRY
# --- BUG 17 FIX: Import models required for Avatar profile remapping ---
from app.models.user import User
from app.models.attachment import Attachment

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads"
TEMP_DIR = "/app/backups/temp_restore"

def process_restore(db: Session, user_id: int, zip_filepath: str):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        # 1. Unzip the file
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)

        # 2. Clear existing USER SPECIFIC data backwards to avoid FK constraint errors
        for table_def in reversed(BACKUP_REGISTRY):
            if table_def["name"] in ["users", "markets", "instruments"]:
                continue

            query = db.query(table_def["model"])
            filtered_query = table_def["user_filter"](query, user_id)

            # Fetch the objects first, then delete them to avoid the .join() error
            objects_to_delete = filtered_query.all()
            for obj in objects_to_delete:
                # --- BUG 17 FIX: Delete physical files before dropping the DB row to prevent orphans ---
                if table_def["name"] == "attachments":
                    file_path = os.path.join(UPLOAD_DIR, getattr(obj, 'path', ''))
                    if getattr(obj, 'path', None) and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logger.warning(f"Could not remove old file {file_path}: {e}")

                db.delete(obj)

        # 3. Insert all data forwards with ID mapping
        id_map = {
            "strategies": {},
            "strategy_rules": {},
            "trades": {},
            "instruments": {}
        }

        for table_def in BACKUP_REGISTRY:
            if table_def["name"] in ["users", "markets"]:
                continue

            json_file = os.path.join(TEMP_DIR, f"{table_def['name']}.json")
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    rows = json.load(f)

                    for row_data in rows:
                        old_id = row_data.get('id')

                        # Strip the primary key so Postgres generates a new, safe one
                        if 'id' in row_data:
                            del row_data['id']

                        # Enforce ownership mapping
                        if 'user_id' in row_data:
                            row_data['user_id'] = user_id

                        # --- Map Foreign Keys ---
                        if 'strategy_id' in row_data and row_data['strategy_id'] in id_map["strategies"]:
                            row_data['strategy_id'] = id_map["strategies"][row_data['strategy_id']]

                        if 'rule_id' in row_data and row_data['rule_id'] in id_map["strategy_rules"]:
                            row_data['rule_id'] = id_map["strategy_rules"][row_data['rule_id']]

                        if 'trade_id' in row_data and row_data['trade_id'] in id_map["trades"]:
                            row_data['trade_id'] = id_map["trades"][row_data['trade_id']]

                        # --- BUG 17 FIX: Remap ownership of both screenshots and avatars ---
                        if table_def["name"] == "attachments":
                            if row_data.get("owner_type") == "trade":
                                if 'owner_id' in row_data and row_data['owner_id'] in id_map["trades"]:
                                    row_data['owner_id'] = id_map["trades"][row_data['owner_id']]
                            elif row_data.get("owner_type") == "avatar":
                                row_data['owner_id'] = user_id

                        # For instruments, we check the symbol string instead of trusting the old ID
                        if table_def["name"] == "instruments":
                            existing_inst = db.query(table_def["model"]).filter(
                                table_def["model"].symbol == row_data.get('symbol')
                            ).first()

                            if existing_inst:
                                if old_id:
                                    id_map["instruments"][old_id] = existing_inst.id
                                continue # Skip inserting duplicate instruments

                        # Apply the instrument ID mapping if this row is a Trade
                        if 'instrument_id' in row_data and row_data['instrument_id'] in id_map["instruments"]:
                            row_data['instrument_id'] = id_map["instruments"][row_data['instrument_id']]

                        # Insert the record and force flush to get the new primary key
                        new_record = table_def["model"](**row_data)
                        db.add(new_record)
                        db.flush()

                        # Store the mapping so child tables can find it
                        if old_id and table_def["name"] in id_map:
                            id_map[table_def["name"]][old_id] = new_record.id

        # --- BUG 17 FIX: Sync the User's profile DB row to point to the newly restored Avatar file ---
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            latest_avatar = db.query(Attachment).filter(
                Attachment.user_id == user_id,
                Attachment.owner_type == 'avatar'
            ).order_by(Attachment.created_at.desc()).first()
            user.avatar_attachment_id = latest_avatar.id if latest_avatar else None

        # 4. Commit EVERYTHING safely in one transaction
        db.commit()

        # 5. Restore image files to the uploads directory
        uploads_source = os.path.join(TEMP_DIR, "uploads")
        if os.path.exists(uploads_source):
            for filename in os.listdir(uploads_source):
                src = os.path.join(uploads_source, filename)
                dst = os.path.join(UPLOAD_DIR, filename)
                shutil.copy2(src, dst)

    except Exception as e:
        db.rollback()
        logger.error(f"Restore failed: {str(e)}")
        raise e
    finally:
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
