/**
 * Task Routes
 * Defines all task-related endpoints
 */

import { Router } from 'express';
import { taskController } from '../controllers/task.controller';
import { validateRequest } from '../middleware/validation';
import {
  TaskCreateSchema,
  TaskUpdateSchema,
  TaskStatusUpdateSchema,
} from '../validators/task.validator';

const router = Router();

/**
 * @route   POST /api/v1/tasks
 * @desc    Create a new task
 * @access  Public
 */
router.post('/', validateRequest(TaskCreateSchema), taskController.createTask.bind(taskController));

/**
 * @route   GET /api/v1/tasks
 * @desc    List all tasks
 * @access  Public
 */
router.get('/', taskController.listTasks.bind(taskController));

/**
 * @route   GET /api/v1/tasks/:id
 * @desc    Get task by ID
 * @access  Public
 */
router.get('/:id', taskController.getTask.bind(taskController));

/**
 * @route   PATCH /api/v1/tasks/:id
 * @desc    Update task
 * @access  Public
 */
router.patch(
  '/:id',
  validateRequest(TaskUpdateSchema),
  taskController.updateTask.bind(taskController)
);

/**
 * @route   PATCH /api/v1/tasks/:id/status
 * @desc    Update task status
 * @access  Public
 */
router.patch(
  '/:id/status',
  validateRequest(TaskStatusUpdateSchema),
  taskController.updateTaskStatus.bind(taskController)
);

/**
 * @route   DELETE /api/v1/tasks/:id
 * @desc    Delete task
 * @access  Public
 */
router.delete('/:id', taskController.deleteTask.bind(taskController));

export default router;
