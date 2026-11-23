"""Completed component life evidence, independent of stand life and stock."""
from sqlalchemy import func
from app.models.spare_life_record import SpareLifeRecord


def life_summaries(db):
    rows = db.query(
        SpareLifeRecord.item_id,
        func.sum(SpareLifeRecord.life_hours * SpareLifeRecord.quantity),
        func.sum(SpareLifeRecord.quantity),
        func.count(SpareLifeRecord.id),
    ).group_by(SpareLifeRecord.item_id).all()
    return {item_id: {
        'average_life_hours': round(total / count, 2),
        'life_sample_count': count,
        'life_record_count': records,
        'average_life_source': 'COMPLETED_RECORDS',
    } for item_id, total, count, records in rows}


def life_summary(item, summaries):
    return summaries.get(item.id, {
        'average_life_hours': item.observed_avg_life_hours,
        'life_sample_count': 0,
        'life_record_count': 0,
        'average_life_source': 'MANUAL' if item.observed_avg_life_hours is not None else 'UNKNOWN',
    })
