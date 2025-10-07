from typing import Any, Dict
from sqlalchemy import text
from sqlalchemy.orm import Session


# PUBLIC_INTERFACE
def get_me(db: Session, user_id: str) -> Dict[str, Any]:
    """Return combined basic user profile."""
    row = db.execute(
        text(
            """
            select u.id, u.email, u.user_type, u.full_name, u.phone, u.avatar_url,
                   js.bio as seeker_bio, js.location as seeker_location, js.desired_role,
                   e.org_name as employer_org, e.website as employer_website, e.location as employer_location, e.verified as employer_verified
            from public.users u
            left join public.job_seekers js on js.user_id = u.id
            left join public.employers e on e.user_id = u.id
            where u.id = :id
            """
        ),
        {"id": user_id},
    ).mappings().first()
    return dict(row) if row else {}


# PUBLIC_INTERFACE
def upsert_job_seeker(db: Session, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update job seeker profile."""
    sql = """
        insert into public.job_seekers (user_id, bio, location, visibility, desired_role)
        values (:user_id, :bio, :location, coalesce(:visibility, true), :desired_role)
        on conflict (user_id)
        do update set bio = excluded.bio, location = excluded.location, visibility = excluded.visibility, desired_role = excluded.desired_role
        returning *
    """
    row = db.execute(text(sql), {"user_id": user_id, **data}).mappings().first()
    return dict(row)  # type: ignore


# PUBLIC_INTERFACE
def upsert_employer(db: Session, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update employer profile."""
    sql = """
        insert into public.employers (user_id, org_name, website, location, verified)
        values (:user_id, :org_name, :website, :location, coalesce(:verified, false))
        on conflict (user_id)
        do update set org_name = excluded.org_name, website = excluded.website, location = excluded.location, verified = excluded.verified
        returning *
    """
    row = db.execute(text(sql), {"user_id": user_id, **data}).mappings().first()
    return dict(row)  # type: ignore
