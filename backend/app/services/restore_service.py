import os
import json
import zipfile
import shutil
import logging
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.utils.table_registry import BACKUP_REGISTRY
from app.models.user import User
from app.models.attachment import Attachment
from app.models.instrument import Instrument

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
    # Ensure a unique temp dir to prevent cross-contamination if concurrent restores happen
    unique_temp_dir = f"{TEMP_DIR}_{uuid.uuid4().hex}"

    if os.path.exists(unique_temp_dir):
        shutil.rmtree(unique_temp_dir)
    os.makedirs(unique_temp_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            secure_extract(zip_ref, unique_temp_dir)

        id_map = {
            "strategies": {},
            "strategy_rules": {},
            "trades": {},
            "instruments": {}
        }

        all_instruments = db.query(Instrument).all()
        symbol_to_id = {inst.symbol: inst.id for inst in all_instruments}

        # FIX FOR BUG 78: Check if the restoring user is an admin
        user = db.query(User).filter(User.id == user_id).first()
        is_admin = user and user.role == 'admin'

        # FIX FOR BUG 56: Collect files to delete, but do NOT delete them until commit succeeds
        files_to_delete = []

        for table_def in reversed(BACKUP_REGISTRY):
            # Skip system tables and logs
            if table_def["name"] in ["users", "markets", "instruments", "app_logs"]:
                continue

            query = db.query(table_def["model"])
            filtered_query = table_def["user_filter"](query, user_id)
            objects_to_delete = filtered_query.all()

            for obj in objects_to_delete:
                if table_def["name"] == "attachments":
                    file_path = os.path.join(UPLOAD_DIR, getattr(obj, 'path', ''))
                    if getattr(obj, 'path', None):
                        files_to_delete.append(file_path)
                db.delete(obj)

        db.flush()

        for table_def in BACKUP_REGISTRY:
            if table_def["name"] in ["users", "markets", "app_logs"]:
                continue

            json_file = os.path.join(unique_temp_dir, f"{table_def['name']}.json")
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    rows = json.load(f)

                    for row_data in rows:
                        old_id = row_data.get('id')

                        if 'id' in row_data:
                            del row_data['id']
                        if 'user_id' in row_data:
                            row_data['user_id'] = user_id
                        if 'password_hash' in row_data:
                            del row_data['password_hash']

                        # --- FIX FOR BUG 56 & 79: Strict Foreign Key Mapping (Skip NULLs) ---
                        if row_data.get('strategy_id') is not None:
                            if row_data['strategy_id'] in id_map["strategies"]:
                                row_data['strategy_id'] = id_map["strategies"][row_data['strategy_id']]
                            else:
                                raise HTTPException(status_code=400, detail="Restore aborted: Unmapped strategy detected.")

                        if row_data.get('rule_id') is not None:
                            if row_data['rule_id'] in id_map["strategy_rules"]:
                                row_data['rule_id'] = id_map["strategy_rules"][row_data['rule_id']]
                            else:
                                raise HTTPException(status_code=400, detail="Restore aborted: Unmapped rule detected.")

                        if row_data.get('trade_id') is not None:
                            if row_data['trade_id'] in id_map["trades"]:
                                row_data['trade_id'] = id_map["trades"][row_data['trade_id']]
                            else:
                                raise HTTPException(status_code=400, detail="Restore aborted: Unmapped trade detected.")

                        if table_def["name"] == "attachments":
                            if row_data.get("owner_type") == "trade":
                                if row_data.get('owner_id') is not None and row_data['owner_id'] in id_map["trades"]:
                                    row_data['owner_id'] = id_map["trades"][row_data['owner_id']]
                            elif row_data.get("owner_type") == "avatar":
                                row_data['owner_id'] = user_id

                        # Map instrument IDs safely by verifying the symbol against the DB
                        if table_def["name"] == "instruments":
                            symbol = row_data.get('symbol')
                            if symbol in symbol_to_id:
                                if old_id:
                                    id_map["instruments"][old_id] = symbol_to_id[symbol]
                            else:
                                # FIX FOR BUG 78: Restrict global instrument creation to admins only
                                if not is_admin:
                                    raise HTTPException(
                                        status_code=400,
                                        detail=f"Restore aborted: Unknown instrument '{symbol}'. Normal users cannot create global instruments."
                                    )

                                new_inst = Instrument(**row_data)
                                db.add(new_inst)
                                db.flush()
                                symbol_to_id[symbol] = new_inst.id
                                if old_id:
                                    id_map["instruments"][old_id] = new_inst.id
                            continue

                        # Apply the instrument ID mapping if this row relies on an instrument
                        if row_data.get('instrument_id') is not None:
                            if row_data['instrument_id'] in id_map["instruments"]:
                                row_data['instrument_id'] = id_map["instruments"][row_data['instrument_id']]
                            else:
                                raise HTTPException(status_code=400, detail="Restore aborted: Unknown instrument ID.")

                        new_record = table_def["model"](**row_data)
                        db.add(new_record)
                        db.flush()

                        if old_id and table_def["name"] in id_map:
                            id_map[table_def["name"]][old_id] = new_record.id

        if user:
            latest_avatar = db.query(Attachment).filter(
                Attachment.user_id == user_id,
                Attachment.owner_type == 'avatar'
            ).order_by(Attachment.created_at.desc()).first()
            user.avatar_attachment_id = latest_avatar.id if latest_avatar else None

        db.commit()

        # FIX FOR BUG 56: Only delete old physical files after commit succeeds
        for fp in files_to_delete:
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception as e:
                    logger.warning(f"Could not remove old file {fp}: {e}")

        # Restore new images
        uploads_source = os.path.join(unique_temp_dir, "uploads")
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
        if os.path.exists(unique_temp_dir):
            shutil.rmtree(unique_temp_dir)
        if os.path.exists(zip_filepath):
            os.remove(zip_filepath)
