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
    Valida que el orchard existe y pertenece al usuario actual.
    Los ADMIN pueden acceder a cualquier orchard.
    
    Args:
        orchard_id: ID del orchard a validar
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        Orchard: El orchard validado
        
    Raises:
        HTTPException 404: Si el orchard no existe
        HTTPException 403: Si el usuario no tiene permisos
    """
    orchard = db.query(models.Orchard).filter(
        models.Orchard.id == orchard_id
    ).first()
    
    if not orchard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orchard {orchard_id} not found"
        )
    
    # Si es ADMIN, puede acceder a cualquier orchard
    if current_user.role == UserRole.ADMIN:
        return orchard
    
    # Si no es ADMIN, debe ser el dueño
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
    Valida que el árbol existe, pertenece al orchard indicado,
    y el usuario tiene permisos.
    
    Args:
        tree_id: ID del árbol
        orchard_id: ID del orchard
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        Tree: El árbol validado
        
    Raises:
        HTTPException 404: Si el árbol no existe
        HTTPException 403: Si el usuario no tiene permisos
    """
    tree = db.query(models.Tree).filter(
        models.Tree.id == tree_id,
        models.Tree.orchard_id == orchard_id
    ).first()
    
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree {tree_id} not found in orchard {orchard_id}"
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
    Valida que la imagen existe y pertenece al usuario.
    
    Args:
        image_id: ID de la imagen
        current_user: Usuario autenticado
        db: Sesión de base de datos
        
    Returns:
        Image: La imagen validada
        
    Raises:
        HTTPException 404: Si la imagen no existe
        HTTPException 403: Si el usuario no tiene permisos
    """
    image = db.query(models.Image).filter(
        models.Image.id == image_id
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image {image_id} not found"
        )
    
    # Si es ADMIN, puede acceder a cualquier imagen
    if current_user.role == UserRole.ADMIN:
        return image
    
    # Validar que la imagen pertenece al usuario
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access images that you own"
        )
    
    return image


# ============================================
# GESTIÓN DE HUERTOS (ORCHARDS)
# ============================================

@router.get("/orchards", response_model=List[orchard_schema.Orchard])
async def get_orchards(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene los orchards del usuario actual.
    
    - FARMER: Solo ve sus propios orchards
    - ADMIN: Ve todos los orchards del sistema
    
    Returns:
        List[Orchard]: Lista de orchards
    """
    # Si es ADMIN, retorna todos los orchards
    if current_user.role == UserRole.ADMIN:
        orchards = db.query(models.Orchard).all()
    else:
        # Si es FARMER, solo sus orchards
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
    Obtiene un orchard específico por ID.
    
    Validaciones:
    - El orchard debe existir
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard
        
    Returns:
        Orchard: Datos del orchard
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
    """
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    return orchard


@router.post("/orchards", response_model=orchard_schema.Orchard, status_code=status.HTTP_201_CREATED)
async def create_orchard(
    orchard_data: orchard_schema.Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Crea un nuevo orchard para el usuario actual.
    
    SEGURIDAD: El user_id se asigna automáticamente desde el token.
    No es necesario enviarlo en el body.
    
    Args:
        orchard_data: Datos del orchard (name, location, n_trees)
        
    Returns:
        Orchard: El orchard creado
    """
    # Crear el orchard con el user_id del usuario autenticado
    orchard_dict = orchard_data.dict()
    orchard_dict['user_id'] = current_user.id  # ✅ Asignación automática
    
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
    Actualiza el número de árboles de un orchard.
    
    Validaciones:
    - El orchard debe existir
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard
        n_trees: Nuevo número de árboles
        
    Returns:
        Orchard: El orchard actualizado
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
    """
    # Validar ownership
    orchard = validate_orchard_ownership(orchard_id, current_user, db)
    
    # Actualizar
    orchard.n_trees = n_trees
    db.commit()
    db.refresh(orchard)
    
    return orchard


@router.delete("/orchards/{orchard_id}", status_code=status.HTTP_200_OK)
async def delete_orchard(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Elimina un orchard y todos sus datos asociados (árboles, imágenes, predicciones).
    
    CASCADA: Al eliminar el orchard, se eliminan automáticamente:
    - Todos los árboles del orchard
    - Todas las imágenes de esos árboles
    - Todas las predicciones y detecciones
    
    Validaciones:
    - El orchard debe existir
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard a eliminar
        
    Returns:
        dict: Mensaje de confirmación
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
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


# ============================================
# GESTIÓN DE ÁRBOLES (TREES)
# ============================================

@router.get("/orchard/{orchard_id}/trees", response_model=List[tree_schema.Tree])
async def get_orchard_trees(
    orchard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Obtiene todos los árboles de un orchard específico.
    
    Validaciones:
    - El orchard debe existir
    - El usuario debe ser el dueño (o ADMIN)
    
    Args:
        orchard_id: ID del orchard
        
    Returns:
        List[Tree]: Lista de árboles del orchard
        
    Raises:
        404: Si el orchard no existe
        403: Si el usuario no tiene permisos
    """
    # Validar ownership
    validate_orchard_ownership(orchard_id, current_user, db)
    
    # Obtener árboles
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
    