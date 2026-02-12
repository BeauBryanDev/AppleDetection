from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models.farming import Orchard as OrchardModel, Tree as TreeModel, Image
from app.db.models.users import User, UserRole
from app.schemas.orchard_schema import OrchardCreate, Orchard as OrchardSchema
from app.schemas.tree_schema import TreeCreate, Tree as TreeSchema
from app.schemas.image_schema import ImageResponse
from app.api.deps import get_current_user, get_current_active_admin
from app.core.logging import logger


router = APIRouter()


# ── Validation Helpers ─────────────/─────────────────────

def validate_orchard_ownership(
    orchard_id: int,
    current_user: User,
    db: Session
) -> OrchardModel:
    """
    Validate that the orchard exists and belongs to the user.

    Admins can access any orchard.

    Args:
        orchard_id: Orchard ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Orchard: Validated orchard from DB

    Raises:
        HTTPException 404: If orchard not found
        HTTPException 403: If user lacks permission
    """
    orchard = db.query(OrchardModel).filter(OrchardModel.id == orchard_id).first()

    if not orchard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchard {orchard_id} not found"
        )

    # Admins can access all
    if current_user.role == UserRole.ADMIN:
        return orchard

    # Non-admins must own it
    if orchard.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access orchards that you own"
        )

    return orchard


def validate_tree_ownership(
    tree_id: int,
    orchard_id: int,
    current_user: User,
    db: Session
) -> TreeModel:
    """
    Validate that the tree exists and belongs to the orchard.

    User must have permission via orchard ownership.

    Args:
        tree_id: Tree ID
        orchard_id: Orchard ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Tree: Validated tree

    Raises:
        HTTPException 404: If tree not found
        HTTPException 403: If user lacks permission
    """
    tree = db.query(TreeModel).filter(
        TreeModel.id == tree_id,
        TreeModel.orchard_id == orchard_id
    ).first()

    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree {tree_id} not found in orchard {orchard_id}"
        )

    # Validate orchard ownership (cascades permission check)
    validate_orchard_ownership(orchard_id, current_user, db)

    return tree


def validate_image_ownership(
    image_id: int,
    current_user: User,
    db: Session
) -> Image:
    """
    Validate that the image exists and belongs to the user.

    Admins can access any image.

    Args:
        image_id: Image ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Image: Validated image

    Raises:
        HTTPException 404: If image not found
        HTTPException 403: If user lacks permission
    """
    image = db.query(Image).filter(Image.id == image_id).first()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found"
        )

    # Admins can access all
    if current_user.role == UserRole.ADMIN:
        return image

    # Non-admins must own it
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access images that you own"
        )

    return image


# ── Orchard Endpoints ──────────────────────────────────────────────────────────

@router.post("/orchards", response_model=OrchardSchema)
async def create_orchard(
    orchard_in: OrchardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new orchard for the authenticated user.

    Returns:
        Orchard: Created orchard
    """
    new_orchard = OrchardModel(
        user_id=current_user.id,
        name=orchard_in.name,
        location=orchard_in.location,
        n_trees=orchard_in.n_trees
    )

    db.add(new_orchard)
    db.commit()
    db.refresh(new_orchard)
    return new_orchard


@router.get("/orchards", response_model=List[OrchardSchema])
async def get_orchards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    all_users: bool = True  # Admins can see all, non-admins can filter by their own
):
    """
    Get a paginated list of the user's orchards.

    Admins can see all orchards.

    Returns:
        List[Orchard]: Orchards
    """
    query = db.query(OrchardModel)

    if current_user.role != UserRole.ADMIN:
        query = query.filter(OrchardModel.user_id == current_user.id if all_users else OrchardModel.user_id == None)

    orchards = query.offset(skip).limit(limit).all()
    return orchards


@router.get("/orchards/{orchard_id}", response_model=OrchardSchema)
async def get_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific orchard by ID.

    Validates ownership (unless admin).

    Returns:
        Orchard: Orchard details
    """
    return validate_orchard_ownership(orchard_id, current_user, db)


@router.put("/orchards/{orchard_id}", response_model=OrchardSchema)
async def update_orchard(
    orchard_id: int,
    obj_in: OrchardCreate,  # Reuse create schema for updates
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an orchard's details.

    Validates ownership (unless admin).

    Returns:
        Orchard: Updated orchard
    """
    orchard = validate_orchard_ownership(orchard_id, current_user, db)

    orchard.name = obj_in.name
    orchard.location = obj_in.location
    orchard.n_trees = obj_in.n_trees

    db.commit()
    db.refresh(orchard)
    return orchard


@router.delete("/orchards/{orchard_id}")
async def delete_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an orchard and its related data (trees, images).

    Validates ownership (unless admin).

    Returns:
        dict: Confirmation message
    """
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    logger.info("Deleted orchard {id} by user {user_id}", id=orchard_id, user_id=current_user.id)
    db.delete(orchard)
    db.commit()

    return {
        "message": "Orchard and related data deleted successfully",
        "orchard_id": orchard_id
    }


# ── Tree Endpoints ─────────────────────────────────────────────────────────────

@router.post("/trees", response_model=TreeSchema)
async def create_tree(
    tree_in: TreeCreate,
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new tree in a specific orchard.

    Validates orchard ownership.

    Args:
        tree_in: Tree data
        orchard_id: Orchard ID (query param)

    Returns:
        Tree: Created tree
    """
    orchard = validate_orchard_ownership(orchard_id, current_user, db)

    new_tree = TreeModel(
        user_id=current_user.id,
        orchard_id=orchard_id,
        tree_code=tree_in.tree_code,
        tree_type=tree_in.tree_type
    )

    db.add(new_tree)
    db.commit()
    db.refresh(new_tree)
    return new_tree


@router.get("/trees", response_model=List[TreeSchema])
async def get_trees(
    orchard_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a paginated list of trees.

    - If orchard_id provided: trees in that orchard
    - Else: all user's trees
    Admins can see all.

    Returns:
        List[Tree]: Trees
    """
    query = db.query(TreeModel)

    if current_user.role != UserRole.ADMIN:
        query = query.filter(TreeModel.user_id == current_user.id)

    if orchard_id:
        validate_orchard_ownership(orchard_id, current_user, db)
        query = query.filter(TreeModel.orchard_id == orchard_id)

    trees = query.offset(skip).limit(limit).all()
    return trees


@router.get("/trees/{tree_id}", response_model=TreeSchema)
async def get_tree(
    tree_id: int,
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific tree by ID in an orchard.

    Validates ownership via orchard.

    Returns:
        Tree: Tree details
    """
    return validate_tree_ownership(tree_id, orchard_id, current_user, db)


@router.put("/trees/{tree_id}", response_model=TreeSchema)
async def update_tree(
    tree_id: int,
    orchard_id: int,
    obj_in: TreeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a tree's details.

    Validates ownership via orchard.

    Returns:
        Tree: Updated tree
    """
    tree = validate_tree_ownership(tree_id, orchard_id, current_user, db)

    tree.tree_code = obj_in.tree_code
    tree.tree_type = obj_in.tree_type

    db.commit()
    db.refresh(tree)
    return tree


@router.delete("/trees/{tree_id}")
async def delete_tree(
    tree_id: int,
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a tree and its related data (images).

    Validates ownership via orchard.

    Returns:
        dict: Confirmation message
    """
    tree = validate_tree_ownership(tree_id, orchard_id, current_user, db)

    db.delete(tree)
    db.commit()

    return {
        "message": "Tree and related data deleted successfully",
        "tree_id": tree_id
    }


# ── Image Endpoints ────────────────────────────────────────────────────────────

@router.get("/images/{image_id}", response_model=ImageResponse)
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get an image's details by ID.

    Validates ownership (unless admin).

    Returns:
        ImageResponse: Image metadata
    """
    image = validate_image_ownership(image_id, current_user, db)
    return image


@router.delete("/images/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an image and its associated predictions/detections.

    Also deletes the physical file in /uploads/ (TODO: uncomment os.remove).

    Validates ownership (unless admin).

    Returns:
        dict: Confirmation message
    """
    image = validate_image_ownership(image_id, current_user, db)

    # TODO: Delete physical file
    import os
    if os.path.exists(image.image_path):
        os.remove(image.image_path)

    db.delete(image)
    db.commit()

    return {
        "message": "Image and associated predictions deleted successfully",
        "image_id": image_id,
        "image_path": image.image_path
    }


# ── Additional Endpoints ───────────────────────────────────────────────────────

@router.get("/my-orchards", response_model=List[OrchardSchema])
async def get_my_orchards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the authenticated user's orchards.

    Equivalent to GET /orchards but more semantically clear.

    Returns:
        List[Orchard]: User's orchards
    """
    orchards = db.query(OrchardModel).filter(
        OrchardModel.user_id == current_user.id
    ).all()

    return orchards


@router.get("/orchard/{orchard_id}/summary")
async def get_orchard_summary(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a quick summary of an orchard with stats.

    Validates ownership (unless admin).

    Returns:
        dict: Orchard summary with stats
    """
    orchard = validate_orchard_ownership(orchard_id, current_user, db)

    # Count trees
    n_trees = db.query(TreeModel).filter(
        TreeModel.orchard_id == orchard_id
    ).count()

    # Count images
    n_images = db.query(Image).filter(
        Image.orchard_id == orchard_id
    ).count()

    return {
        "orchard_id": orchard.id,
        "orchard_name": orchard.name,
        "location": orchard.location,
        "registered_trees": n_trees,
        "total_images": n_images,
        "owner_id": orchard.user_id,
        "owner_name": current_user.name
    }