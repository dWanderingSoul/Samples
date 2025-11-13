# ============= tasks/views.py =============
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
import json
import os

class TaskViewSet(viewsets.ViewSet):
    """
    ViewSet for managing tasks with JSON file storage
    """
    TASKS_FILE = "tasks.json"
    
    def _load_tasks(self):
        """Load tasks from JSON file"""
        if not os.path.exists(self.TASKS_FILE):
            return []
        
        try:
            with open(self.TASKS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    
    def _save_tasks(self, tasks):
        """Save tasks to JSON file"""
        with open(self.TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def _get_next_id(self, tasks):
        """Get next available task ID"""
        if not tasks:
            return 1
        return max(task['id'] for task in tasks) + 1
    
    def _find_task(self, tasks, task_id):
        """Find task by ID"""
        for idx, task in enumerate(tasks):
            if task['id'] == task_id:
                return idx, task
        return None, None
    
    def list(self, request):
        """GET /tasks/ - List all tasks"""
        status_filter = request.query_params.get('status')
        tasks = self._load_tasks()
        
        if status_filter:
            if status_filter not in ['todo', 'in-progress', 'done']:
                return Response(
                    {"error": "Invalid status. Must be 'todo', 'in-progress', or 'done'"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            tasks = [task for task in tasks if task['status'] == status_filter]
        
        return Response(tasks)
    
    def create(self, request):
        """POST /tasks/ - Create a new task"""
        description = request.data.get('description')
        
        if not description:
            return Response(
                {"error": "Description is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(description, str) or len(description.strip()) == 0:
            return Response(
                {"error": "Description must be a non-empty string"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self._load_tasks()
        now = datetime.now().isoformat()
        
        new_task = {
            "id": self._get_next_id(tasks),
            "description": description.strip(),
            "status": "todo",
            "createdAt": now,
            "updatedAt": now
        }
        
        tasks.append(new_task)
        self._save_tasks(tasks)
        
        return Response(new_task, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """GET /tasks/{id}/ - Get a specific task"""
        try:
            task_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid task ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self._load_tasks()
        idx, task = self._find_task(tasks, task_id)
        
        if task is None:
            return Response(
                {"error": f"Task with ID {task_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(task)
    
    def update(self, request, pk=None):
        """PUT /tasks/{id}/ - Update task description"""
        try:
            task_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid task ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        description = request.data.get('description')
        
        if not description:
            return Response(
                {"error": "Description is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self._load_tasks()
        idx, task = self._find_task(tasks, task_id)
        
        if task is None:
            return Response(
                {"error": f"Task with ID {task_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tasks[idx]['description'] = description.strip()
        tasks[idx]['updatedAt'] = datetime.now().isoformat()
        
        self._save_tasks(tasks)
        return Response(tasks[idx])
    
    def destroy(self, request, pk=None):
        """DELETE /tasks/{id}/ - Delete a task"""
        try:
            task_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid task ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self._load_tasks()
        idx, task = self._find_task(tasks, task_id)
        
        if task is None:
            return Response(
                {"error": f"Task with ID {task_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tasks.pop(idx)
        self._save_tasks(tasks)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        """PATCH /tasks/{id}/status/ - Update task status"""
        try:
            task_id = int(pk)
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid task ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_status = request.data.get('status')
        
        if new_status not in ['todo', 'in-progress', 'done']:
            return Response(
                {"error": "Status must be 'todo', 'in-progress', or 'done'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self._load_tasks()
        idx, task = self._find_task(tasks, task_id)
        
        if task is None:
            return Response(
                {"error": f"Task with ID {task_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        tasks[idx]['status'] = new_status
        tasks[idx]['updatedAt'] = datetime.now().isoformat()
        
        self._save_tasks(tasks)
        return Response(tasks[idx])
    
    @action(detail=True, methods=['patch'])
    def mark_in_progress(self, request, pk=None):
        """PATCH /tasks/{id}/mark_in_progress/ - Mark as in-progress"""
        request.data['status'] = 'in-progress'
        return self.status(request, pk)
    
    @action(detail=True, methods=['patch'])
    def mark_done(self, request, pk=None):
        """PATCH /tasks/{id}/mark_done/ - Mark as done"""
        request.data['status'] = 'done'
        return self.status(request, pk)