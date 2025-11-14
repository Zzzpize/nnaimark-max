from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List

import models
from database import SessionLocal, create_db_and_tables
from gigachat_client import generate_initial_steps, generate_sub_steps

create_db_and_tables()

app = FastAPI()

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Pydantic модели ---
class RoadmapCreateRequest(BaseModel):
    prompt: str
    max_user_id: str = Field(..., alias="maxUserId")

# --- Логика БД ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_user(db: Session, max_user_id: str) -> models.User:
    user = db.query(models.User).filter(models.User.max_user_id == max_user_id).first()
    if not user:
        user = models.User(max_user_id=max_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# --- Рекурсивные хелперы ---
def build_tree(step: models.RoadmapStep):
    """Собирает рекурсивно дерево шагов для ответа API."""
    return {
        "id": step.id,
        "title": step.title,
        "description": step.description,
        "difficulty": step.difficulty,
        "is_done": step.is_done,
        "children": [build_tree(child) for child in step.children]
    }

def _count_steps_recursive(steps: List[models.RoadmapStep]) -> list[int]:
    """Рекурсивно считает выполненные и общие шаги."""
    done_count = 0
    total_count = 0
    for step in steps:
        total_count += 1
        if step.is_done:
            done_count += 1
        if step.children:
            child_done, child_total = _count_steps_recursive(step.children)
            done_count += child_done
            total_count += child_total
    return done_count, total_count


# --- Эндпоинты API ---

@app.post("/api/roadmaps")
async def create_roadmap(request: RoadmapCreateRequest, db: Session = Depends(get_db)):
    user = get_or_create_user(db, request.max_user_id)
    steps_data = await generate_initial_steps(request.prompt)
    if not steps_data:
        raise HTTPException(status_code=500, detail="Не удалось сгенерировать шаги роадмапа")
    
    new_roadmap = models.Roadmap(title=request.prompt, owner_id=user.id)
    step_objects = [models.RoadmapStep(
        title=step.get("title", "Без названия"),
        description=step.get("description", ""),
        difficulty=step.get("difficulty", "green"),
        roadmap=new_roadmap
    ) for step in steps_data]
    
    db.add(new_roadmap)
    db.add_all(step_objects)
    db.commit()
    db.refresh(new_roadmap)
    
    response_tree = [build_tree(step) for step in new_roadmap.steps]
    return {"id": new_roadmap.id, "title": new_roadmap.title, "steps": response_tree}

@app.get("/api/roadmaps")
def get_user_roadmaps(max_user_id: str = Query(..., alias="maxUserId"), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.max_user_id == max_user_id).first()
    if not user:
        return []

    response = []
    for roadmap in user.roadmaps:
        done_count, total_count = _count_steps_recursive(roadmap.steps)
        progress_str = f"{done_count}/{total_count}" if total_count > 0 else "0/0"
        response.append({
            "id": roadmap.id,
            "title": roadmap.title,
            "progress": progress_str
        })
    return response

@app.get("/api/roadmaps/{roadmap_id}")
def get_single_roadmap(roadmap_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(models.Roadmap).filter(models.Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Роадмап не найден")
    
    response_tree = [build_tree(step) for step in roadmap.steps]
    return {"id": roadmap.id, "title": roadmap.title, "steps": response_tree}


@app.post("/api/steps/{step_id}/decompose")
async def decompose_step(step_id: int, db: Session = Depends(get_db)):
    parent_step = db.query(models.RoadmapStep).filter(models.RoadmapStep.id == step_id).first()
    if not parent_step:
        raise HTTPException(status_code=404, detail="Родительский шаг не найден")
    
    sub_steps_data = await generate_sub_steps(parent_step.title, parent_step.description)
    if not sub_steps_data:
        raise HTTPException(status_code=500, detail="Не удалось сгенерировать подзадачи")

    sub_step_objects = [models.RoadmapStep(
        title=step.get("title", "Без названия"),
        description=step.get("description", ""),
        difficulty=step.get("difficulty", "green"),
        roadmap_id=parent_step.roadmap_id,
        parent_id=parent_step.id
    ) for step in sub_steps_data]

    db.add_all(sub_step_objects)
    db.commit()

    response_children = [build_tree(step) for step in sub_step_objects]
    return response_children

@app.put("/api/steps/{step_id}/toggle")
def toggle_step_status(step_id: int, db: Session = Depends(get_db)):
    step = db.query(models.RoadmapStep).filter(models.RoadmapStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Шаг не найден")
    step.is_done = not step.is_done
    db.commit()
    db.refresh(step)
    return {"id": step.id, "is_done": step.is_done}


@app.delete("/api/roadmaps/{roadmap_id}", status_code=status.HTTP_200_OK)
def delete_roadmap(roadmap_id: int, db: Session = Depends(get_db)):
    roadmap = db.query(models.Roadmap).filter(models.Roadmap.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Роадмап для удаления не найден")
    
    db.delete(roadmap)
    db.commit()
    
    return {"status": "ok", "message": "Роадмап успешно удален"}