export type SSEEvent =
  | { type: "token"; content: string }
  | { type: "tool_call"; tool: string }
  | { type: "step"; step: string; label: string }
  | { type: "itinerary"; itinerary: unknown[]; budget?: Record<string, number> }
  | { type: "approval_required"; message: string }
  | { type: "done" }
  | { type: "error"; message: string };

function extractDataPayload(block: string): string | null {
  const dataLines: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith("data: ")) {
      dataLines.push(line.slice(6));
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  return dataLines.join("\n");
}

function parseEventBlock(block: string): SSEEvent | null {
  const payload = extractDataPayload(block);
  if (!payload) {
    return null;
  }

  try {
    return JSON.parse(payload) as SSEEvent;
  } catch {
    return null;
  }
}

/** Parse SSE frames from a fetch response body reader. */
export async function* parseSSEStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      const event = parseEventBlock(block);
      if (event) {
        yield event;
      }

      boundary = buffer.indexOf("\n\n");
    }
  }

  buffer += decoder.decode();
  const trailing = buffer.trim();
  if (trailing) {
    const event = parseEventBlock(trailing);
    if (event) {
      yield event;
    }
  }
}
