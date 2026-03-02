/**
 * Task Service
 * Business logic for task management
 */

import { prisma } from '../models';
import { Task, TaskStatus } from '@prisma/client';
import { TaskCreateInput, TaskUpdateInput, VALID_STATUS_TRANSITIONS } from '../models/task.model';
import { NotFoundError, ConflictError } from '../utils/errors';
import logger from '../utils/logger';

export class TaskService {
  /**
   * Create a new task
   */
  async createTask(data: TaskCreateInput): Promise<Task> {
    const task = await prisma.task.create({
      data: {
        title: data.title,
        description: data.description,
        status: data.status || 'Pending',
      },
    });

    logger.info('Task created:', { taskId: task.id, title: task.title });

    // Log activity
    await this.logActivity(task, 'task.created');

    return task;
  }

  /**
   * Get task by ID
   */
  async getTask(id: string): Promise<Task> {
    const task = await prisma.task.findUnique({
      where: { id },
    });

    if (!task) {
      throw new NotFoundError('Task');
    }

    return task;
  }

  /**
   * Get all tasks with optional filtering
   */
  async getTasks(filters?: {
    status?: TaskStatus;
    page?: number;
    pageSize?: number;
  }): Promise<{ tasks: Task[]; total: number; page: number; pageSize: number }> {
    const { status, page = 1, pageSize = 20 } = filters || {};

    const where = status ? { status } : {};

    const [tasks, total] = await Promise.all([
      prisma.task.findMany({
        where,
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * pageSize,
        take: pageSize,
      }),
      prisma.task.count({ where }),
    ]);

    return { tasks, total, page, pageSize };
  }

  /**
   * Update task
   */
  async updateTask(id: string, data: TaskUpdateInput): Promise<Task> {
    // Verify task exists
    await this.getTask(id);

    const updateData: Record<string, unknown> = {
      ...data,
    };

    // Handle completedAt based on status
    if (data.status === 'Done') {
      updateData.completedAt = new Date();
    } else if (data.status !== undefined) {
      updateData.completedAt = null;
    }

    const task = await prisma.task.update({
      where: { id },
      data: updateData,
    });

    logger.info('Task updated:', { taskId: task.id });
    await this.logActivity(task, 'task.updated');

    return task;
  }

  /**
   * Update task status with transition validation
   */
  async updateTaskStatus(id: string, newStatus: TaskStatus): Promise<Task> {
    const task = await this.getTask(id);

    // Validate status transition
    const validTransitions = VALID_STATUS_TRANSITIONS[task.status];

    if (!validTransitions.includes(newStatus)) {
      throw new ConflictError(
        `Cannot transition from ${task.status} to ${newStatus}. Valid transitions: ${validTransitions.join(', ') || 'none'}`,
        'INVALID_TRANSITION'
      );
    }

    const updateData: Record<string, unknown> = {
      status: newStatus,
    };

    if (newStatus === 'Done') {
      updateData.completedAt = new Date();
    } else {
      updateData.completedAt = null;
    }

    const updatedTask = await prisma.task.update({
      where: { id },
      data: updateData,
    });

    logger.info('Task status updated:', {
      taskId: task.id,
      fromStatus: task.status,
      toStatus: newStatus,
    });

    await this.logActivity(updatedTask, 'task.updated', {
      fromStatus: task.status,
      toStatus: newStatus,
    });

    return updatedTask;
  }

  /**
   * Delete task
   */
  async deleteTask(id: string): Promise<void> {
    // Verify task exists
    await this.getTask(id);

    await prisma.task.delete({
      where: { id },
    });

    logger.info('Task deleted:', { taskId: id });

    // Log activity (best effort, task is already deleted)
    try {
      await prisma.activityLog.create({
        data: {
          type: 'task.deleted',
          description: `Task ${id} deleted`,
          metadata: { taskId: id },
        },
      });
    } catch (error) {
      logger.warn('Failed to log task deletion:', { taskId: id, error });
    }
  }

  /**
   * Log activity for task operations
   */
  private async logActivity(
    task: Task,
    type: string,
    additionalMetadata?: Record<string, unknown>
  ): Promise<void> {
    try {
      await prisma.activityLog.create({
        data: {
          type,
          description: `Task '${task.title}' ${this.getActivityDescription(type)}`,
          metadata: additionalMetadata ? JSON.parse(JSON.stringify(additionalMetadata)) : undefined,
        },
      });
    } catch (error) {
      logger.warn('Failed to log activity:', { taskId: task.id, type, error });
    }
  }

  /**
   * Get activity description based on type
   */
  private getActivityDescription(type: string): string {
    const descriptions: Record<string, string> = {
      'task.created': 'created',
      'task.updated': 'updated',
      'task.deleted': 'deleted',
    };
    return descriptions[type] || 'modified';
  }
}

export const taskService = new TaskService();
export default taskService;
