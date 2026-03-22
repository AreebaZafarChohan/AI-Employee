import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class GoalRepository {
  async create(data: { title: string; description?: string; priority?: number }) {
    return await prisma.goal.create({
      data: {
        ...data,
        state: 'PENDING_PLAN',
      },
    });
  }

  async findById(id: string) {
    return await prisma.goal.findUnique({
      where: { id },
      include: { tasks: true },
    });
  }

  async updateState(id: string, state: string) {
    return await prisma.goal.update({
      where: { id },
      data: { state },
    });
  }

  async delete(id: string) {
    return await prisma.goal.delete({
      where: { id },
    });
  }
}
