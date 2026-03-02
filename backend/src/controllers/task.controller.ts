/**
 * Task Controller
 * HTTP request handlers for task endpoints
 */

import { Request, Response, NextFunction } from 'express';
import { taskService } from '../services/task.service';
import { TaskStatusUpdateInput, TaskCreateInput, TaskUpdateInput } from '../validators/task.validator';
import { Task } from '@prisma/client';

/**
 * Map backend PascalCase status to frontend kebab-case
 */
function mapTaskStatus(status: string): string {
  const mapping: Record<string, string> = {
    'Pending': 'pending',
    'InProgress': 'in-progress',
    'Done': 'completed',
  };
  return mapping[status] ?? status.toLowerCase();
}

/**
 * Map backend task to frontend shape with converted status
 */
function mapTaskForResponse(task: Task): Record<string, unknown> {
  return {
    ...task,
    status: mapTaskStatus(task.status as string),
  };
}

export class TaskController {
  /**
   * Create a new task
   * POST /api/v1/tasks
   */
  async createTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const taskData = req.body as TaskCreateInput;
      const task = await taskService.createTask(taskData);

      res.status(201).json({
        data: mapTaskForResponse(task),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Get task by ID
   * GET /api/v1/tasks/:id
   */
  async getTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const task = await taskService.getTask(id);

      res.status(200).json({
        data: mapTaskForResponse(task),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * List all tasks
   * GET /api/v1/tasks
   */
  async listTasks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { status, page, pageSize } = req.query;
      const result = await taskService.getTasks({
        status: status as 'Pending' | 'InProgress' | 'Done',
        page: Number(page),
        pageSize: Number(pageSize),
      });

      res.status(200).json({
        data: result.tasks.map(mapTaskForResponse),
        meta: {
          total: result.total,
          page: page ? Number(page) : 1,
          pageSize: pageSize ? Number(pageSize) : 20,
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Update task
   * PATCH /api/v1/tasks/:id
   */
  async updateTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const taskData = req.body as TaskUpdateInput;
      const task = await taskService.updateTask(id, taskData);

      res.status(200).json({
        data: mapTaskForResponse(task),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Update task status
   * PATCH /api/v1/tasks/:id/status
   */
  async updateTaskStatus(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { status } = req.body as TaskStatusUpdateInput;
      const task = await taskService.updateTaskStatus(id, status as 'Pending' | 'InProgress' | 'Done');

      res.status(200).json({
        data: mapTaskForResponse(task),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Delete task
   * DELETE /api/v1/tasks/:id
   */
  async deleteTask(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      await taskService.deleteTask(id);

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }
}

export const taskController = new TaskController();
export default taskController;
