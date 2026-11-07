import os
import json
import zipfile
import shutil
import logging
from sqlalchemy.orm import Session
from app.utils.table_registry import BACKUP_REGISTRY
from app.models.user import User
from app.models.attachment import Attachment
from app.models.instrument import Instrument
from fastapi import HTTPException

logger = logging.getLogger(__name__)

UPLOAD_DIR = "/app/uploads"
TEMP_DIR = "/app/backups/temp_restore"

def secure_extract(zip_ref, target_dir):
    """Safely extracts a zip file, preventing path traversal attacks."""
    for member in zip_ref.infolist():
        # Prevent absolute paths or path traversal attacks (e.g. '../../etc/passwd')
        if member.filename.startswith('/') or '..' in member.filename:
            continue

        target_path = os.path.join(target_dir, member.filename)
        # Ensure the extracted path stays within the intended target directory
        if os.path.commonprefix([target_path, target_dir]) == target_dir:
            zip_ref.extract(member, target_dir)

def process_restore(db: Session, user_id: int, zip_filepath: str):
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        # 1. Securely unzip the file (Mitigates Path Traversal)
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            secure_extract(zip_ref, TEMP_DIR)

        # Build an ID map for ALL tables to prevent Foreign Key hijacking
        id_map = {
            "strategies": {},
            "strategy_rules": {},
            "trades": {},
            "instruments": {}
        }

        # Pre-map instruments based on the existing DB to prevent instrument injection
        all_instruments = db.query(Instrument).all()
        symbol_to_id = {inst.symbol: inst.id for inst in all_instruments}

        # 2. CLEAR DATA AND INSERT NEW DATA IN A SINGLE TRANSACTION
        # (Mitigates the delete-before-commit data loss risk)

        # A. Clear existing USER SPECIFIC data backwards to avoid FK constraint errors
        for table_def in reversed(BACKUP_REGISTRY):
            if table_def["name"] in ["users", "markets", "instruments"]:
                continue

            query = db.query(table_def["model"])
            filtered_query = table_def["user_filter"](query, user_id)
            objects_to_delete = filtered_query.all()

            for obj in objects_to_delete:
                if table_def["name"] == "attachments":
                    file_path = os.path.join(UPLOAD_DIR, getattr(obj, 'path', ''))
                    if getattr(obj, 'path', None) and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            logger.warning(f"Could not remove old file {file_path}: {e}")
                db.delete(obj)

        # Flush the deletions so the DB state is ready for inserts, but DO NOT commit yet.
        db.flush()

        # B. Insert all data forwards with strict ID mapping
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

                        # Security: Strip password_hash if it exists in the payload
                        if 'password_hash' in row_data:
                            del row_data['password_hash']

                        # --- Strict Foreign Key Mapping ---
                        if 'strategy_id' in row_data and row_data['strategy_id'] in id_map["strategies"]:
                            row_data['strategy_id'] = id_map["strategies"][row_data['strategy_id']]

                        if 'rule_id' in row_data and row_data['rule_id'] in id_map["strategy_rules"]:
                            row_data['rule_id'] = id_map["strategy_rules"][row_data['rule_id']]

                        if 'trade_id' in row_data and row_data['trade_id'] in id_map["trades"]:
                            row_data['trade_id'] = id_map["trades"][row_data['trade_id']]

                        if table_def["name"] == "attachments":
                            if row_data.get("owner_type") == "trade":
                                if 'owner_id' in row_data and row_data['owner_id'] in id_map["trades"]:
                                    row_data['owner_id'] = id_map["trades"][row_data['owner_id']]
                            elif row_data.get("owner_type") == "avatar":
                                row_data['owner_id'] = user_id

                        # Map instrument IDs safely by verifying the symbol against the DB
                        if table_def["name"] == "instruments":
                            symbol = row_data.get('symbol')
                            if symbol in symbol_to_id:
                                if old_id:
                                    id_map["instruments"][old_id] = symbol_to_id[symbol]
                            # We skip inserting new instruments during a user restore.
                            # Instruments are global and should only be managed by admins.
                            continue

                        # Apply the instrument ID mapping if this row relies on an instrument
                        if 'instrument_id' in row_data:
                            if row_data['instrument_id'] in id_map["instruments"]:
                                row_data['instrument_id'] = id_map["instruments"][row_data['instrument_id']]
                            else:
                                # Reject rows that try to reference invalid or unmapped instruments
                                raise HTTPException(
                                    status_code=400,
                                    detail=f"Restore failed: Cannot map instrument_id {row_data['instrument_id']}."
                                )

                        new_record = table_def["model"](**row_data)
                        db.add(new_record)
                        db.flush()

                        if old_id and table_def["name"] in id_map:
                            id_map[table_def["name"]][old_id] = new_record.id

        # Sync the User's profile DB row to point to the newly restored Avatar file
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            latest_avatar = db.query(Attachment).filter(
                Attachment.user_id == user_id,
                Attachment.owner_type == 'avatar'
            ).order_by(Attachment.created_at.desc()).first()
            user.avatar_attachment_id = latest_avatar.id if latest_avatar else None

        # 3. Commit EVERYTHING safely in one atomic transaction
        db.commit()

        # 4. Restore image files to the uploads directory only after DB success
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
