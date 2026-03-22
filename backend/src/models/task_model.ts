import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class TaskRepository {
  async createMany(tasks: any[]) {
    return await prisma.task.createMany({
      data: tasks,
    });
  }

  async findByGoalId(goalId: string) {
    return await prisma.task.findMany({
      where: { goalId },
      orderBy: { order: 'asc' },
    });
  }

  async updateStatus(id: string, status: string) {
    return await prisma.task.update({
      where: { id },
      data: { status },
    });
  }

  async findById(id: string) {
    return await prisma.task.findUnique({
      where: { id },
    });
  }
}
