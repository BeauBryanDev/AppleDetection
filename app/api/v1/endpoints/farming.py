from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.models import farming as models
from app.db.models.users import User, UserRole
from app.schemas import tree_schema, orchard_schema
from app.api import deps

router = APIRouter()

# --- GESTIÓN DE ÁRBOLES (TREES) ---

def validate_orchard_ownership(
    orchard_id: int,
    current_user: User,
    db: Session
) -> models.Orchard:
    """
    Validate Orchard exist and belongs to same user
    Adming user can see orchards from other usersid in database 
    
    Args:
        orchard_id:
        current_user: auth user
        db: databsee session
        
    Returns:
        Orchard: valid orchard fro mdatabase
        
    Raises:
        HTTPException 404: If orchard does nto exists
        HTTPException 403: If user does not have enough permission. Not Admin. 
    """
    orchard = db.query(models.Orchard).filter(
        models.Orchard.id == orchard_id
    ).first()
    
    if not orchard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchard {orchard_id} Not Found"
        )
    
    # Si it is admin, it can acess all orchards to see reports in dashboards.
    if current_user.role == UserRole.ADMIN:
        return orchard
    
    # If it is not admin, then it must owns the requested orchard id.
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
) -> models.Tree:
    """
    Validate that this tree exists and it belongs to orchard id, 
    UCurrent User must have all permission to go.
    
    Args:
        tree_id: 
        orchard_
        current_user: authenticated user
        db: database session
        
    Returns:
        Tree: valid treee.
        
    Raises:
        HTTPException 404: if not treee
        HTTPException 403: User does nto have permissions to go.
    """
    tree = db.query(models.Tree).filter(
        models.Tree.id == tree_id,
        models.Tree.orchard_id == orchard_id
    ).first()
    
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree {tree_id} Not Found in Orchard {orchard_id}"
        )
    
    # Validar que el orchard pertenece al usuario
    validate_orchard_ownership(orchard_id, current_user, db)
    
    return tree


def validate_image_ownership(
    image_id: int,
    current_user: User,
    db: Session
) -> models.Image:
    """
    Validate Image exist and it belongs to current user
    
    Args:
        image_id: 
        current_user: 
        db: 
        
    Returns:
        Image: validated resource
        
    Raises:
        HTTPException 404: if image resource does nto exist
        HTTPException 403: if user does not have permission to go
    """
    image = db.query(models.Image).filter(
        models.Image.id == image_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} Not Found"
        )
    
    # I it is admin,  it can access / see all images/resoruces
    if current_user.role == UserRole.ADMIN:
        return image
    
    # Validate images belongs to current user
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access images that you own"
        )
    
    return image


# Orchards management
@router.get("/orchards", response_model=List[orchard_schema.Orchard])
async def get_orchards(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get all orchards from current user.
    
    - FARMER: Only can see its own orchards
    - ADMIN:  Can see all orchards in the system 
    
    Returns:
        List[Orchard]: Orchards list
    """
    # If it is  ADMIN, return all  orchards in database
    if current_user.role == UserRole.ADMIN:
        orchards = db.query(models.Orchard).all()
    else:
        # If it is FARMER, it only can see its own  orchards
        orchards = db.query(models.Orchard).filter(
            models.Orchard.user_id == current_user.id
        ).all()
    
    return orchards


@router.get("/orchards/{orchard_id}", response_model=orchard_schema.Orchard)
async def get_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Get just the requested orchard id 
    
    Validations:

    - Orchard id must exists
    - User must own the orchard or be  an  ADMIN
    
    Args:
        orchard_id: 
        
    Returns:
        Orchard: 
        
    Raises:
        404: if orchard does not exits
        403: if user does nto have permissions
    """
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    return orchard


@router.post("/orchards", response_model=orchard_schema.Orchard, status_code=status.HTTP_201_CREATED)
async def create_orchard(
    orchard_data: orchard_schema.OrchardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Create a new orchard for current user id .
    
    Security : current user id  must be asigned to orchard at the moment of creating
    
    Args:
        orchard_data:  orchard fields (name, location, n_trees)
        
    Returns:
        Orchard: new orchard class isntance
    """
    # Create a new orchard with the id of authenticated user
    orchard_dict = orchard_data.dict()
    orchard_dict['user_id'] = current_user.id  # authomatic asign
    
    new_orchard = models.Orchard(**orchard_dict)
    db.add(new_orchard)
    db.commit()
    db.refresh(new_orchard)
    
    return new_orchard


@router.patch("/orchards/{orchard_id}", response_model=orchard_schema.Orchard)
async def update_orchard(
    orchard_id: int,
    n_trees: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Update number of threes from a current orchard
    + It only allows User/Farmers to edit the numbers of threes,
    - Users can not change orchard name or location
    - they must delete current orchard and create a neww one

    Validations:
    - Orchard must exist
    - User must be the owner or Admin role 
    
    Args:
        orchard_id:
        n_trees: Number of threes 
        
    Returns:
        Orchard: updated orchard
        
    Raises:
        404: If orchard does nto exist
        403: If user does not have enoguh privileges
    """
    # Validar ownership
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    
    # Actualizar
    orchard.n_trees = n_trees
    db.commit()
    db.refresh(orchard)
    
    return orchard

# Delete an existing Orchard
@router.delete("/orchards/{orchard_id}", status_code=status.HTTP_200_OK)
async def delete_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Delete an orchard and all its data like: trees, images, predictions.
    
    CASCADA: when orchard deleted is must be cascade delete all resoruces
    - All trees from  orchard
    - All images from these trees
    - All predictions and detections must be gone.
    
    Validations : 
    - Ordchard must exist before being deleted
    - User must own this orchard or user must have Admin Privileges
    
    Args:
        orchard_id: 
        
    Returns:
        dict: confirmation message
        
    Raises:
        404: If Orchard does nto exist
        403: If not enough privileges 
    """
    # Validar ownership
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    
    # Eliminar
    db.delete(orchard)
    db.commit()
    
    return {
        "message": f"Orchard '{orchard.name}' and all associated data deleted successfully",
        "orchard_id": orchard_id
    }

# TREE MANAGEMENT


@router.get("/orchard/{orchard_id}/trees", response_model=List[tree_schema.Tree])
async def get_orchard_trees(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
   Get all trees from an Orchard id
    
    Validations;
    - Orchard must exist
    - User must own this orchard
    
    Args:
        orchard_id:
        
    Returns:
        List[Tree]: List of all trees standing in orchard
        
    Raises:
        404: orchard does not exits
        403: Not privilegues .
    """
    # validate orchard ownership
    validate_orchard_ownership(orchard_id, current_user, db)
    
    # get trees
    trees = db.query(models.Tree).filter(
        models.Tree.orchard_id == orchard_id
    ).all()
    
    return trees


@router.post("/orchard/{orchard_id}/create_tree", response_model=tree_schema.Tree, status_code=status.HTTP_201_CREATED)
async def create_tree(
    orchard_id: int,
    tree_data: tree_schema.TreeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Crea un nuevo árbol en el orchard especificado.
    
    SEGURIDAD:
    - El orchard_id de la URL tiene prioridad sobre el body
    - El user_id se asigna automáticamente
    
    Validaciones:
    - El orchard debe existir
    - El usuario debe ser el dueño del orchard (o ADMIN)
    
    Args:
        orchard_id: ID del orchard (desde URL)
        tree_data: Datos del árbol (tree_code, tree_type)
        
    Returns:
        Tree: El árbol creado
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
    """
    # Validar que el orchard existe y pertenece al usuario
    validate_orchard_ownership(orchard_id, current_user, db)
    
    # Crear el árbol
    tree_dict = tree_data.dict()
    tree_dict['orchard_id'] = orchard_id  # ✅ Forzar orchard_id de la URL
    tree_dict['user_id'] = current_user.id  # ✅ Asignar user_id automáticamente
    
    new_tree = models.Tree(**tree_dict)
    db.add(new_tree)
    db.commit()
    db.refresh(new_tree)
    
    return new_tree


@router.put("/orchard/{orchard_id}/tree/{tree_id}", response_model=tree_schema.Tree)
async def update_tree(
    orchard_id: int,
    tree_id: int,
    tree_update: tree_schema.TreeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Actualiza un árbol existente.
    
    Validaciones:
    - El árbol debe existir
    - El árbol debe pertenecer al orchard indicado
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard
        tree_id: ID del árbol
        tree_update: Datos a actualizar (tree_code, tree_type)
        
    Returns:
        Tree: El árbol actualizado
        
    Raises:
        404: Si el árbol no existe
        403: Si el usuario no tiene permisos
    """
    # Validar ownership
    tree = validate_tree_ownership(tree_id, orchard_id, current_user, db)
    
    # Actualizar campos
    if tree_update.tree_code is not None:
        tree.tree_code = tree_update.tree_code
    if tree_update.tree_type is not None:
        tree.tree_type = tree_update.tree_type
    
    db.commit()
    db.refresh(tree)
    
    return tree


@router.delete("/trees/{orchard_id}/{tree_id}", status_code=status.HTTP_200_OK)
async def delete_tree(
    orchard_id: int,
    tree_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Elimina un árbol específico.
    
    CASCADA: Al eliminar el árbol, se eliminan automáticamente:
    - Todas las imágenes del árbol
    - Todas las predicciones y detecciones
    
    Validaciones:
    - El árbol debe existir
    - El árbol debe pertenecer al orchard indicado
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard
        tree_id: ID del árbol
        
    Returns:
        dict: Mensaje de confirmación
        
    Raises:
        404: Si el árbol no existe
        403: Si el usuario no tiene permisos
    """
    # Validar ownership
    tree = validate_tree_ownership(tree_id, orchard_id, current_user, db)
    
    # Eliminar
    db.delete(tree)
    db.commit()
    
    return {
        "message": f"Tree {tree.tree_code} deleted successfully",
        "tree_id": tree_id,
        "orchard_id": orchard_id
    }


# ============================================
# GESTIÓN DE IMÁGENES
# ============================================

@router.delete("/images/{image_id}", status_code=status.HTTP_200_OK)
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Elimina una imagen y todos sus datos asociados.
    
    CASCADA: Al eliminar la imagen, se eliminan automáticamente:
    - La predicción asociada
    - Todas las detecciones de esa predicción
    
    TODO: Implementar eliminación del archivo físico en /uploads/
    
    Validaciones:
    - La imagen debe existir
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        image_id: ID de la imagen
        
    Returns:
        dict: Mensaje de confirmación
        
    Raises:
        404: Si la imagen no existe
        403: Si el usuario no tiene permisos
    """
    # Validar ownership
    image = validate_image_ownership(image_id, current_user, db)
    
    # TODO: Eliminar archivo físico
    # import os
    # if os.path.exists(image.image_path):
    #     os.remove(image.image_path)
    
    # Eliminar de BD
    db.delete(image)
    db.commit()
    
    return {
        "message": "Image and associated predictions deleted successfully",
        "image_id": image_id,
        "image_path": image.image_path
    }


# ============================================
# ENDPOINTS ADICIONALES (OPCIONAL)
# ============================================

@router.get("/my-orchards", response_model=List[orchard_schema.Orchard])
async def get_my_orchards(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Endpoint alternativo más explícito para obtener los orchards del usuario actual.
    Equivalente a GET /orchards pero más claro semánticamente.
    
    Returns:
        List[Orchard]: Orchards del usuario autenticado
    """
    orchards = db.query(models.Orchard).filter(
        models.Orchard.user_id == current_user.id
    ).all()
    
    return orchards


@router.get("/orchard/{orchard_id}/summary")
async def get_orchard_summary(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene un resumen rápido del orchard con estadísticas.
    
    Validaciones:
    - El orchard debe existir
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard
        
    Returns:
        dict: Resumen con estadísticas del orchard
    """
    # Validar ownership
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    
    # Contar árboles
    n_trees = db.query(models.Tree).filter(
        models.Tree.orchard_id == orchard_id
    ).count()
    
    # Contar imágenes
    n_images = db.query(models.Image).filter(
        models.Image.orchard_id == orchard_id
    ).count()
    
    # Obtener el usuario actual
    return {
        "orchard_id": orchard.id,
        "orchard_name": orchard.name,
        "location": orchard.location,
        "registered_trees": n_trees,
        "total_images": n_images,
        "owner_id": orchard.user_id,
        "owner_name": current_user.name
        
    }
    
