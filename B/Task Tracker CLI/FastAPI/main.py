"""
FastAPI Task Tracker API
Install: pip install fastapi uvicorn pydantic
Run: uvicorn main:app --reload
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import json
import os
from pathlib import Path

app = FastAPI(title="Task Tracker API")

# Configuration
TASKS_FILE = "tasks.json"

# Pydantic Models
class TaskCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)

class TaskUpdate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)

class TaskStatus(BaseModel):
    status: Literal["todo", "in-progress", "done"]

class Task(BaseModel):
    id: int
    description: str
    status: Literal["todo", "in-progress", "done"]
    createdAt: str
    updatedAt: str

# Helper Functions
def load_tasks() -> List[dict]:
    """Load tasks from JSON file"""
    if not os.path.exists(TASKS_FILE):
        return []
    
    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_tasks(tasks: List[dict]) -> None:
    """Save tasks to JSON file"""
    with open(TASKS_FILE, 'w') as f:
        json.dump(tasks, f, indent=2)

def get_next_id(tasks: List[dict]) -> int:
    """Get next available task ID"""
    if not tasks:
        return 1
    return max(task['id'] for task in tasks) + 1

def find_task_index(tasks: List[dict], task_id: int) -> int:
    """Find task index by ID"""
    for idx, task in enumerate(tasks):
        if task['id'] == task_id:
            return idx
    return -1

# API Endpoints
@app.get("/")
def read_root():
    """API root endpoint"""
    return {
        "message": "Task Tracker API",
        "endpoints": {
            "GET /tasks": "List all tasks",
            "GET /tasks/{task_id}": "Get specific task",
            "GET /tasks/status/{status}": "List tasks by status",
            "POST /tasks": "Create new task",
            "PUT /tasks/{task_id}": "Update task description",
            "PATCH /tasks/{task_id}/status": "Update task status",
            "DELETE /tasks/{task_id}": "Delete task"
        }
    }

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_data: TaskCreate):
    """Add a new task"""
    tasks = load_tasks()
    
    now = datetime.now().isoformat()
    new_task = {
        "id": get_next_id(tasks),
        "description": task_data.description,
        "status": "todo",
        "createdAt": now,
        "updatedAt": now
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    return new_task

@app.get("/tasks", response_model=List[Task])
def list_tasks():
    """List all tasks"""
    return load_tasks()

@app.get("/tasks/status/{task_status}", response_model=List[Task])
def list_tasks_by_status(task_status: Literal["todo", "in-progress", "done"]):
    """List tasks by status"""
    tasks = load_tasks()
    filtered = [task for task in tasks if task['status'] == task_status]
    return filtered

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    """Get a specific task"""
    tasks = load_tasks()
    idx = find_task_index(tasks, task_id)
    
    if idx == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return tasks[idx]

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_data: TaskUpdate):
    """Update task description"""
    tasks = load_tasks()
    idx = find_task_index(tasks, task_id)
    
    if idx == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    tasks[idx]['description'] = task_data.description
    tasks[idx]['updatedAt'] = datetime.now().isoformat()
    
    save_tasks(tasks)
    return tasks[idx]

@app.patch("/tasks/{task_id}/status", response_model=Task)
def update_task_status(task_id: int, status_data: TaskStatus):
    """Update task status"""
    tasks = load_tasks()
    idx = find_task_index(tasks, task_id)
    
    if idx == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    tasks[idx]['status'] = status_data.status
    tasks[idx]['updatedAt'] = datetime.now().isoformat()
    
    save_tasks(tasks)
    return tasks[idx]

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    """Delete a task"""
    tasks = load_tasks()
    idx = find_task_index(tasks, task_id)
    
    if idx == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    tasks.pop(idx)
    save_tasks(tasks)
    
    return None

# Convenience endpoints for marking status
@app.patch("/tasks/{task_id}/mark-in-progress", response_model=Task)
def mark_in_progress(task_id: int):
    """Mark task as in-progress"""
    return update_task_status(task_id, TaskStatus(status="in-progress"))

@app.patch("/tasks/{task_id}/mark-done", response_model=Task)
def mark_done(task_id: int):
    """Mark task as done"""
    return update_task_status(task_id, TaskStatus(status="done"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)