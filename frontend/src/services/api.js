const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = rawApiUrl.replace(/\/+$/, '');

export const streamAnalysis = async (formData, onProgress, onResult, onError) => {
  try {
    const response = await fetch(`${API_URL}/api/analyse`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
        if (response.status === 400) {
            const errData = await response.json();
            throw new Error(errData.message || 'Bad Request');
        }
        throw new Error(`Server error: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // Keep incomplete line in buffer

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed || !trimmed.startsWith('data: ')) continue

        const dataStr = trimmed.slice(6).trim()
        if (!dataStr) continue

        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.type === 'progress') onProgress(parsed)
          if (parsed.type === 'result') onResult(parsed)
          if (parsed.type === 'error') onError(parsed)
        } catch (e) {
          console.error('Failed to parse SSE JSON. Length:', dataStr.length)
          console.error('Start:', dataStr.slice(0, 100))
          console.error('End:', dataStr.slice(-100))
          console.error('Full string:', dataStr) // Critical for debugging
          console.error('Error:', e)
        }
      }
    }

    // Process any remaining data in the buffer
    if (buffer.trim()) {
      const line = buffer.trim()
      if (line.startsWith('data: ')) {
        const dataStr = line.slice(6).trim()
        if (dataStr) {
          try {
            const parsed = JSON.parse(dataStr)
            if (parsed.type === 'result') onResult(parsed)
          } catch (e) {
            console.error('Failed to parse final SSE chunk. Length:', dataStr.length)
            console.error('Content:', dataStr)
            console.error('Error:', e)
          }
        }
      }
    }
  } catch (err) {
    onError({ message: err.message })
  }
}

export const pingServer = async () => {
    try {
        console.log("Pinging backend at:", `${API_URL}/ping`);
        const response = await fetch(`${API_URL}/ping`, { signal: AbortSignal.timeout(40000) });
        return response.ok;
    } catch (e) {
        console.error("Ping failed:", e);
        return false;
    }
}
