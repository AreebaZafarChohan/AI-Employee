import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class MemoryRepository {
  async create(data: { content: string; embedding?: number[]; goalId?: string; taskId?: string; userId?: string }) {
    // For pgvector, we need to handle the embedding as a vector
    // Since Prisma doesn't natively support pgvector types yet, we use raw SQL for insertion if embedding is provided
    if (data.embedding) {
      const vectorStr = `[${data.embedding.join(',')}]`;
      return await prisma.$executeRaw`
        INSERT INTO "MemoryRecord" (id, content, embedding, "goalId", "taskId", "userId", "createdAt")
        VALUES (${crypto.randomUUID()}, ${data.content}, ${vectorStr}::vector, ${data.goalId}, ${data.taskId}, ${data.userId}, NOW())
      `;
    }

    return await prisma.memoryRecord.create({
      data: {
        content: data.content,
        goalId: data.goalId,
        taskId: data.taskId,
        userId: data.userId,
      },
    });
  }

  async findRelevant(embedding: number[], limit: number = 5) {
    const vectorStr = `[${embedding.join(',')}]`;
    // Vector similarity search (cosine distance: <=>)
    return await prisma.$queryRaw<any[]>`
      SELECT * FROM "MemoryRecord"
      ORDER BY embedding <=> ${vectorStr}::vector
      LIMIT ${limit}
    `;
  }
}
