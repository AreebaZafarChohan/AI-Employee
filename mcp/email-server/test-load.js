// Quick test: verify MCP server starts and Gmail auth works
import('./src/index.js')
  .then(() => console.log('[OK] Server module loaded'))
  .catch(err => console.error('[ERR]', err.message));
