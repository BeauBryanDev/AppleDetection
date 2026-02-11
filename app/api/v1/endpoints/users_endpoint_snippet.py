@router.get("/", response_model=List[user_schema.UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_admin)
):
    """
    Retrieve users.
    Only for admins.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users
