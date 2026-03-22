import { MemoryRepository } from '../models/memory_model';
import { logger } from '../lib/logger';

export class MemoryService {
  constructor(private memoryRepo: MemoryRepository = new MemoryRepository()) {}

  async storeMemory(content: string, metadata: { goalId?: string; taskId?: string; userId?: string }) {
    logger.info('Storing new memory record');

    // Simulate embedding generation (1536 dimensions for GPT)
    // In a real app, this would call OpenAI or a local embedding model.
    const mockEmbedding = Array.from({ length: 1536 }, () => Math.random());

    return await this.memoryRepo.create({
      content,
      embedding: mockEmbedding,
      ...metadata,
    });
  }

  async recallContext(query: string, limit: number = 3) {
    logger.info(`Recalling context for query: ${query.substring(0, 50)}...`);

    // Simulate query embedding
    const queryEmbedding = Array.from({ length: 1536 }, () => Math.random());

    const memories = await this.memoryRepo.findRelevant(queryEmbedding, limit);
    return memories.map(m => m.content);
  }
}
